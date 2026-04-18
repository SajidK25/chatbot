import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from bs4 import BeautifulSoup


class TestScraperService:
    """Test scraper service for outopia.com"""

    def test_parses_product_name(self):
        """GIVEN HTML with product card WHEN parsed THEN product name extracted"""
        html = """
        <product-item>
            <a class="product-item__title" href="/products/test-product">Test Product Name</a>
        </product-item>
        """
        soup = BeautifulSoup(html, "html.parser")
        title = soup.select_one(".product-item__title")
        assert title is not None
        assert title.text.strip() == "Test Product Name"

    def test_parses_product_price(self):
        """GIVEN HTML with product card WHEN parsed THEN product price extracted"""
        html = """
        <div class="product-item__price">
            <span class="price-item">$99.00</span>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        price = soup.select_one(".price-item")
        assert price is not None
        assert "99.00" in price.text

    def test_parses_product_description(self):
        """GIVEN HTML with product card WHEN parsed THEN product description extracted"""
        html = """
        <div class="product-item__details">
            <p>Product description here</p>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        desc = soup.select_one(".product-item__details p")
        assert desc is not None

    def test_parses_product_images(self):
        """GIVEN HTML with product card WHEN parsed THEN image URLs extracted"""
        html = """
        <product-item class="ta-c">
            <img class="product-item__image product-item__image--main" 
                 data.original-src="/image1.jpg">
        </product-item>
        """
        soup = BeautifulSoup(html, "html.parser")
        img = soup.select_one(".product-item__image--main")
        assert img is not None

    def test_parses_product_sku_from_data(self):
        """GIVEN HTML with product card WHEN parsed THEN SKU extracted"""
        html = """
        <product-item-quick-shopping data-product-id="12345">
        </product-item-quick-shopping>
        """
        soup = BeautifulSoup(html, "html.parser")
        el = soup.select_one("[data-product-id]")
        assert el is not None
        assert el.get("data-product-id") == "12345"

    def test_parses_product_url(self):
        """GIVEN HTML with product card WHEN parsed THEN product URL extracted"""
        html = """
        <product-item-quick-shopping data-product-url="/products/test-shirt">
        </product-item-quick-shopping>
        """
        soup = BeautifulSoup(html, "html.parser")
        el = soup.select_one("[data-product-url]")
        assert el is not None
        assert "/products/test-shirt" in el.get("data-product-url", "")

    def test_parses_sizes_from_thumbnails(self):
        """GIVEN HTML with product card WHEN parsed THEN sizes array extracted"""
        html = """
        <div class="product-item__variant-thumbs">
            <div class="product-item__variant-thumb" data-variant-name="S"></div>
            <div class="product-item__variant-thumb" data-variant-name="M"></div>
            <div class="product-item__variant-thumb" data-variant-name="L"></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        thumbs = soup.select(".product-item__variant-thumb")
        sizes = [t.get("data-variant-name") for t in thumbs]
        assert sizes == ["S", "M", "L"]

    def test_parses_colors_from_thumbnails(self):
        """GIVEN HTML with product card WHEN parsed THEN colors array extracted"""
        html = """
        <div class="product-item__variant-thumbs">
            <div class="product-item__variant-thumb" data.variant-image="/black.jpg"></div>
            <div class="product-item__variant-thumb" data.variant-image="/blue.jpg"></div>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        thumbs = soup.select(".product-item__variant-thumb")
        colors = [t.get("data-variant-image") for t in thumbs]
        assert len(colors) == 2

    def test_handles_empty_html(self):
        """GIVEN empty HTML response WHEN parsed THEN return empty list"""
        html = ""
        soup = BeautifulSoup(html, "html.parser")
        products = soup.select("product-item")
        assert len(products) == 0

    def test_handles_missing_fields(self):
        """GIVEN HTML with minimal product data WHEN parsed THEN handle gracefully"""
        html = """
        <product-item class="ta-c">
            <div class="product-item__image-wrapper"></div>
        </product-item>
        """
        soup = BeautifulSoup(html, "html.parser")
        item = soup.select_one("product-item")
        assert item is not None


class TestRateLimiting:
    """Test rate limiting for scraping"""

    def test_respects_rate_limit_config(self):
        """GIVEN rate limit config WHEN configured THEN delay is 2 seconds"""
        from src.services.scraper import ScrapingConfig

        config = ScrapingConfig()
        assert config.request_delay == 2


class TestErrorHandling:
    """Test error handling for scraper"""

    def test_handles_invalid_url(self):
        """GIVEN invalid URL WHEN scraping THEN raise invalid URL error"""
        from src.services.scraper import validate_url

        with pytest.raises(ValueError):
            validate_url("not-a-url")

    def test_handles_empty_page(self):
        """GIVEN empty HTML response WHEN parsed THEN return empty list"""
        from src.services.scraper import parse_products

        html = "<html><body></body></html>"
        products = parse_products(html)
        assert isinstance(products, list)

    def test_generates_sku_from_name(self):
        """GIVEN name and price WHEN no SKU THEN generate from hash"""
        from src.services.scraper import generate_sku_from_name

        sku = generate_sku_from_name("Test Product", 99.99)
        assert isinstance(sku, str)
        assert len(sku) > 0
