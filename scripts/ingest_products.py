#!/usr/bin/env python3
"""
Data Ingestion Script: Generate 500 products with embeddings
Run: python scripts/ingest_products.py
"""

import asyncio
import os
import random
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client, AsyncClient

load_dotenv()

CATEGORIES = {
    "Fashion": {
        "brands": [
            "Nike",
            "Adidas",
            "Zara",
            "H&M",
            "Uniqlo",
            "Levi's",
            "Gucci",
            "Prada",
        ],
        "items": [
            ("Running Shoes", "Lightweight running shoes with cushioned sole"),
            ("Casual T-Shirt", "Cotton blend t-shirt with modern fit"),
            ("Denim Jeans", "Classic fit denim jeans with stretch"),
            ("Winter Jacket", "Waterproof winter jacket with fleece lining"),
            ("Sports Shorts", "Breathable sports shorts for workouts"),
            ("Leather Belt", "Genuine leather belt with silver buckle"),
            ("Wool Sweater", "Merino wool sweater for cold weather"),
            ("Sneakers", "Classic white sneakers for everyday"),
        ],
    },
    "Electronics": {
        "brands": [
            "Apple",
            "Samsung",
            "Sony",
            "Bose",
            "JBL",
            "Dell",
            "Logitech",
            "Beats",
        ],
        "items": [
            ("Wireless Headphones", "Noise-cancelling wireless headphones"),
            ("Smart Watch", "Fitness tracker with heart rate monitor"),
            ("Bluetooth Speaker", "Portable waterproof bluetooth speaker"),
            ("Laptop Stand", "Ergonomic aluminum laptop stand"),
            ("Wireless Earbuds", "True wireless earbuds with charging case"),
            ("Phone Charger", "Fast charging USB-C charger"),
            ("Webcam HD", "1080p HD webcam for video calls"),
            ("Mechanical Keyboard", "RGB mechanical gaming keyboard"),
        ],
    },
    "Home": {
        "brands": [
            "IKEA",
            "West Elm",
            "Target",
            "Wayfair",
            "Amazon Basics",
            "Better Homes",
        ],
        "items": [
            ("Bed Sheets", "Egyptian cotton bed sheet set"),
            ("Coffee Maker", "Programmable drip coffee maker"),
            ("Desk Lamp", "LED desk lamp with adjustable brightness"),
            ("Throw Pillow", "Decorative throw pillow covers"),
            ("Storage Basket", "Woven storage basket with handles"),
            ("Wall Clock", "Modern minimalist wall clock"),
            ("Plant Pot", "Ceramic plant pot with drainage"),
            ("Candle Set", "Scented candle gift set"),
        ],
    },
    "Beauty": {
        "brands": [
            "L'Oreal",
            "Nivea",
            "Olay",
            "CeraVe",
            "The Ordinary",
            "Paula's Choice",
        ],
        "items": [
            ("Face Moisturizer", "Daily hydrating face moisturizer"),
            ("Shampoo", "Sulfate-free shampoo for all hair types"),
            ("Body Lotion", "Body lotion with shea butter"),
            ("Sunscreen SPF50", "Mineral sunscreen for sensitive skin"),
            ("Lip Balm", "Moisturizing lip balm set"),
            ("Serum", "Vitamin C brightening serum"),
            ("Face Mask", "Clay face mask for deep cleansing"),
            ("Perfume", "Eau de perfume with floral notes"),
        ],
    },
}

GENDERS = ["men", "women", "unisex", None]


def generate_products(count: int = 500) -> list[dict]:
    products = []
    colors = [
        "black",
        "white",
        "red",
        "blue",
        "green",
        "pink",
        "gray",
        "brown",
        "navy",
        "beige",
    ]

    for i in range(count):
        category = random.choice(list(CATEGORIES.keys()))
        category_data = CATEGORIES[category]
        brand = random.choice(category_data["brands"])
        item_name, item_desc = random.choice(category_data["items"])

        color = random.choice(colors)
        gender = random.choice(GENDERS)

        if gender:
            name = f"{gender.title()} {color.title()} {item_name}"
        else:
            name = f"{color.title()} {item_name}"

        description = f"{brand} {item_name}. {item_desc}. Perfect for everyday use. Made with premium materials."

        price_ranges = {
            "Fashion": (15, 200),
            "Electronics": (20, 350),
            "Home": (10, 150),
            "Beauty": (8, 80),
        }
        price_min, price_max = price_ranges[category]
        price = round(random.uniform(price_min, price_max), 2)

        image_id = random.randint(1, 1000)
        image_url = f"https://picsum.photos/seed/{image_id}/400/400"

        product_id = f"PROD-{i + 1:05d}"
        product_url = f"https://example.com/product/{product_id}"

        products.append(
            {
                "name": name,
                "description": description,
                "price": price,
                "category": category,
                "image_url": image_url,
                "product_url": product_url,
                "brand": brand,
                "gender": gender,
            }
        )

    return products


async def generate_embeddings(products: list[dict], client: AsyncOpenAI) -> list[dict]:
    print(f"Generating embeddings for {len(products)} products...")

    texts = [
        f"{p['name']}. {p['description']}. {p['brand']}. {p['category']}"
        for p in products
    ]

    embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await client.embeddings.create(
            model="text-embedding-3-small", input=batch, encoding_format="float"
        )
        batch_embeddings = [item.embedding for item in response.data]
        embeddings.extend(batch_embeddings)
        print(
            f"  Embedded batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}"
        )

    for product, embedding in zip(products, embeddings):
        product["embedding"] = embedding

    return products


async def insert_products(products: list[dict], supabase: AsyncClient):
    print(f"Inserting {len(products)} products into Supabase...")

    batch_size = 50
    for i in range(0, len(products), batch_size):
        batch = products[i : i + batch_size]
        response = await supabase.table("products").insert(batch).execute()
        if response.error:
            print(f"  Error inserting batch {i // batch_size + 1}: {response.error}")
        else:
            print(
                f"  Inserted batch {i // batch_size + 1}/{(len(products) - 1) // batch_size + 1}"
            )

    print("Done!")


async def main():
    import sys

    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_KEY"):
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env")
        sys.exit(1)

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY must be set in .env")
        sys.exit(1)

    openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    supabase = AsyncClient(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    products = generate_products(500)
    products = await generate_embeddings(products, openai_client)
    await insert_products(products, supabase)

    print(f"\nSuccessfully created {len(products)} products with embeddings!")


if __name__ == "__main__":
    asyncio.run(main())
