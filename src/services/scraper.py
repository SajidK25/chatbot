import asyncio
import hashlib
import re
import time
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class ScrapedProduct:
    name: str
    price: float
    description: str
    image_url: str
    product_url: str
    sku: str
    sizes: list[str] = field(default_factory=list)
    colors: list[str] = field(default_factory=list)


@dataclass
class ScrapingConfig:
    request_delay: int = 2
    max_retries: int = 3
    retry_backoff: int = 30
    timeout: int = 30


class ScrapingError(Exception):
    pass


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"Invalid URL format: {url}")
    if not parsed.scheme in ("http", "https"):
        raise ValueError(f"Invalid URL scheme: {parsed.scheme}")
    return url


def generate_sku_from_name(name: str, price: float) -> str:
    raw = f"{name.lower().replace(' ', '-')}-{price}"
    hash_obj = hashlib.md5(raw.encode())
    return hash_obj.hexdigest()[:12]


def parse_products(html: str) -> list[ScrapedProduct]:
    soup = BeautifulSoup(html, "html.parser")
    products = []

    for item in soup.select("product-item"):
        try:
            product = _parse_product_item(item)
            if product:
                products.append(product)
        except Exception:
            continue

    return products


def _parse_product_item(item) -> Optional[ScrapedProduct]:
    title_el = item.select_one(".product-item__title")
    if not title_el:
        return None

    name = title_el.get_text(strip=True)
    if not name:
        return None

    product_url = title_el.get("href", "")
    if product_url and not product_url.startswith("http"):
        product_url = f"https://outopia.com{product_url}"

    price_el = item.select_one(".price-item, .product-item__price")
    price_text = price_el.get_text(strip=True) if price_el else "$0"
    price = _parse_price(price_text)

    img_el = item.select_one(".product-item__image--main")
    image_url = ""
    if img_el:
        image_url = img_el.get("data.original-src") or img_el.get("src", "")
        if image_url and not image_url.startswith("http"):
            image_url = f"https://outopia.com{image_url}"

    quick_shop = item.select_one("product-item-quick-shopping")
    sku = ""
    if quick_shop:
        sku = quick_shop.get("data-product-id", "")

    if not sku:
        sku = generate_sku_from_name(name, price)

    details_el = item.select_one(".product-item__details")
    description = details_el.get_text(strip=True) if details_el else ""

    sizes = []
    for thumb in item.select(".product-item__variant-thumb"):
        size = thumb.get("data-variant-name", "")
        if size:
            sizes.append(size)

    colors = []
    for thumb in item.select(".product-item__variant-thumb"):
        color = thumb.get("data-variant-image", "")
        if color:
            colors.append(color)

    return ScrapedProduct(
        name=name,
        price=price,
        description=description,
        image_url=image_url,
        product_url=product_url,
        sku=sku,
        sizes=sizes,
        colors=colors,
    )


def _parse_price(text: str) -> float:
    match = re.search(r"[\d,]+\.?\d*", text.replace(",", ""))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return 0.0
    return 0.0


async def fetch_page(url: str, config: ScrapingConfig = None) -> str:
    config = config or ScrapingConfig()

    async with httpx.AsyncClient(timeout=config.timeout) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.text


async def scrape_products(
    url: str, config: ScrapingConfig = None
) -> list[ScrapedProduct]:
    config = config or ScrapingConfig()
    validate_url(url)

    html = await fetch_page(url, config)
    products = parse_products(html)

    if not products:
        raise ScrapingError("No products found on page")

    return products


async def retry_on_rate_limit(
    func,
    max_retries: int = 3,
    backoff: int = 30,
):
    last_error = None

    for attempt in range(max_retries):
        try:
            return await func()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                last_error = e
                await asyncio.sleep(backoff)
                continue
            raise

    raise ScrapingError(f"Rate limited after {max_retries} retries")


class Scraper:
    def __init__(self, config: ScrapingConfig = None):
        self.config = config or ScrapingConfig()
        self._last_request_time = 0.0

    async def scrape(self, url: str) -> list[ScrapedProduct]:
        validate_url(url)

        await self._respect_rate_limit()

        html = await fetch_page(url, self.config)
        products = parse_products(html)

        return products

    async def _respect_rate_limit(self):
        now = time.time()
        elapsed = now - self._last_request_time

        if elapsed < self.config.request_delay:
            await asyncio.sleep(self.config.request_delay - elapsed)

        self._last_request_time = time.time()
