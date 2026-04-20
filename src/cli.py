import asyncio
import json
from dataclasses import dataclass
from typing import Optional

import click
import cohere

from src.config import settings
from src.database.supabase_client import get_supabase
from src.services.scraper import ScrapedProduct, scrape_products


@dataclass
class ProductRecord:
    sku: str
    name: str
    description: str
    price: float
    category: str
    image_url: str
    product_url: str
    brand: str
    gender: Optional[str] = None
    sizes: Optional[list] = None
    colors: Optional[list] = None


def _scrape_to_record(product: ScrapedProduct, category: str = "uncategorized") -> dict:
    return {
        "sku": product.sku,
        "name": product.name,
        "description": product.description,
        "price": product.price,
        "category": category,
        "image_url": product.image_url,
        "product_url": product.product_url,
        "brand": "Outopia",
        "gender": None,
        "sizes": json.dumps(product.sizes) if product.sizes else "[]",
        "colors": json.dumps(product.colors) if product.colors else "[]",
    }


async def _scrape_and_save(url: str, category: str = "uncategorized"):
    click.echo(f"Scraping {url}...")

    products = await scrape_products(url)
    click.echo(f"Found {len(products)} products")

    supabase = get_supabase()
    cohere_client = cohere.AsyncClient(api_key=settings.cohere_api_key)
    inserted = 0
    updated = 0

    click.echo("Generating embeddings...")
    for product in products:
        record = _scrape_to_record(product, category)

        try:
            embedding_text = f"{product.name} {product.description}"
            response = await cohere_client.embed(
                model="embed-multilingual-v3.0",
                texts=[embedding_text],
                input_type="search_document",
                embedding_types=["float"],
            )
            if hasattr(response.embeddings, "float") and response.embeddings.float:
                record["embedding"] = response.embeddings.float[0]
        except Exception as e:
            click.echo(f"  Warning: embedding failed for {product.name}: {e}")

        existing = (
            supabase.table("products").select("id").eq("sku", product.sku).execute()
        )

        if existing.data:
            supabase.table("products").update(record).eq("sku", product.sku).execute()
            updated += 1
        else:
            supabase.table("products").insert(record).execute()
            inserted += 1

    return inserted, updated


def save_products_to_supabase(products: list[dict]):
    supabase = get_supabase()
    inserted = 0
    updated = 0
    failed = 0

    for product in products:
        try:
            sku = product.get("id", "")
            title = product.get("title", "")
            description = (
                product.get("description", {}).get("plain", "")
                if isinstance(product.get("description"), dict)
                else ""
            )
            url = product.get("url", "")
            media = product.get("media", [])
            variants = product.get("variants", [])

            image_url = ""
            if media:
                image_url = media[0].get("url", "")

            sizes = []
            colors = []
            price = 0.0

            for variant in variants:
                opts = variant.get("variant_options", [])
                for opt in opts:
                    if opt.get("name") == "size":
                        sizes.append(opt.get("value", ""))
                    if opt.get("name") == "color":
                        colors.append(opt.get("value", ""))

                price_obj = variant.get("price", {})
                if price_obj:
                    price = price_obj.get("amount", 0) / 100

            record = {
                "sku": sku,
                "name": title,
                "description": description,
                "price": price,
                "category": "uncategorized",
                "image_url": image_url,
                "product_url": url,
                "brand": "Outopia",
                "gender": None,
                "sizes": json.dumps(sizes),
                "colors": json.dumps(colors),
            }

            existing = supabase.table("products").select("id").eq("sku", sku).execute()

            if existing.data:
                supabase.table("products").update(record).eq("sku", sku).execute()
                updated += 1
            else:
                supabase.table("products").insert(record).execute()
                inserted += 1

        except Exception as e:
            failed += 1
            click.echo(f"Error: {e}")

    return inserted, updated, failed


@click.group()
def cli():
    """OpenClaw CLI - Product scraping and management tool"""
    pass


@cli.command()
@click.argument("url")
@click.option("--category", default="uncategorized", help="Product category")
def scrape(url: str, category: str):
    """Scrape products from a URL and save to database"""
    try:
        inserted, updated = asyncio.run(_scrape_and_save(url, category))
        click.echo(f"Done! {inserted} new, {updated} updated.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path())
def export(file_path: str):
    """Export products to JSON file in OpenAI commerce spec format"""
    try:
        supabase = get_supabase()
        response = supabase.table("products").select("*").execute()

        products = []
        for row in response.data or []:
            product = {
                "id": row.get("sku", ""),
                "title": row.get("name", ""),
                "description": {"plain": row.get("description", "")},
                "url": row.get("product_url", ""),
                "media": [{"type": "image", "url": row.get("image_url", "")}],
                "variants": [],
            }

            sizes = row.get("sizes", [])
            colors = row.get("colors", [])

            if isinstance(sizes, str):
                sizes = json.loads(sizes) if sizes else []
            if isinstance(colors, str):
                colors = json.loads(colors) if colors else []

            if sizes or colors:
                variant_opts = []
                for size in sizes:
                    variant_opts.append({"name": "size", "value": size})
                for color in colors:
                    variant_opts.append({"name": "color", "value": color})

                product["variants"] = [
                    {
                        "id": row.get("sku", ""),
                        "title": f"{row.get('name', '')}",
                        "variant_options": variant_opts,
                    }
                ]

            products.append(product)

        output = {
            "header": {
                "feed_id": "openclaw_feed",
                "account_id": "openclaw",
                "target_merchant": "outopia",
                "target_country": "US",
            },
            "products": products,
        }

        with open(file_path, "w") as f:
            json.dump(output, f, indent=2)

        click.echo(f"Exported {len(products)} products to {file_path}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("file_path", type=click.Path(exists=True))
def import_products(file_path: str):
    """Import products from JSON file in OpenAI commerce spec format"""
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        products = data.get("products", [])
        click.echo(f"Importing {len(products)} products...")

        inserted, updated, failed = save_products_to_supabase(products)

        click.echo(f"Done! {inserted} inserted, {updated} updated, {failed} failed.")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    cli()
