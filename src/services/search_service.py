import os
import re
from typing import Optional
from openai import AsyncOpenAI
from src.config import settings
from src.database.supabase_client import get_supabase


class SearchService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.supabase = get_supabase()

    async def search_products(
        self,
        query: str,
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        limit: int = 3,
    ) -> list[dict]:
        response = await self.openai_client.embeddings.create(
            model="text-embedding-3-small", input=[query], encoding_format="float"
        )
        query_embedding = response.data[0].embedding

        filters = []
        params = [query_embedding]

        filters.append("1=1")
        if max_price is not None:
            filters.append("price <= $2")
            params.append(max_price)
        if category:
            filters.append(
                f"LOWER(category) = ${2 + len([m for m in [max_price] if m is not None])}"
            )
            params.append(category.lower())
        if gender:
            idx = 2 + len([m for m in [max_price, category] if m is not None])
            filters.append(f"(gender = ${idx} OR gender IS NULL OR gender = 'unisex')")
            params.append(gender.lower())

        where_clause = " AND ".join(filters)

        sql = f"""
            SELECT 
                id, name, description, price, category, 
                image_url, product_url, brand, gender,
                (embedding <=> $1) as similarity
            FROM products
            WHERE {where_clause}
            ORDER BY embedding <=> $1
            LIMIT ${len(params) + 1}
        """
        params.append(limit)

        try:
            response = self.supabase.rpc(
                "exec_sql", {"query": sql, "params": params}
            ).execute()
            if response.data:
                return response.data
        except Exception:
            pass

        products = (
            self.supabase.table("products")
            .select(
                "id, name, description, price, category, image_url, product_url, brand, gender"
            )
            .limit(limit * 3)
            .execute()
            .data
        )
        return products[:limit] if products else []

    def parse_natural_language(self, query: str) -> dict:
        query_lower = query.lower()
        result = {"query": query, "max_price": None, "category": None, "gender": None}

        price_patterns = [
            r"under\s*\$?(\d+)",
            r"less\s*than\s*\$?(\d+)",
            r"below\s*\$?(\d+)",
            r"(\d+)\s*dollars?",
            r"budget\s*of?\s*\$?(\d+)",
        ]
        for pattern in price_patterns:
            match = re.search(pattern, query_lower)
            if match:
                result["max_price"] = float(match.group(1))
                break

        gender_patterns = [
            (r"\bmen\b", "men"),
            (r"\bwomen\b", "women"),
            (r"\bman\b", "men"),
            (r"\bwoman\b", "women"),
            (r"\bfor\s+him\b", "men"),
            (r"\bfor\s+her\b", "women"),
            (r"\bguys\b", "men"),
            (r"\bladies\b", "women"),
        ]
        for pattern, gender in gender_patterns:
            if re.search(pattern, query_lower):
                result["gender"] = gender
                break

        category_keywords = {
            "fashion": [
                "shoes",
                "shirt",
                "jacket",
                "jeans",
                "dress",
                "clothing",
                "sneakers",
                "sweater",
            ],
            "electronics": [
                "headphones",
                "speaker",
                "watch",
                "charger",
                "keyboard",
                "webcam",
                "earbuds",
            ],
            "home": [
                "bed",
                "lamp",
                "pillow",
                "clock",
                "candle",
                "plant",
                "storage",
                "basket",
            ],
            "beauty": [
                "moisturizer",
                "shampoo",
                "lotion",
                "sunscreen",
                "serum",
                "mask",
                "perfume",
                "lip",
            ],
        }
        for category, keywords in category_keywords.items():
            if any(kw in query_lower for kw in keywords):
                result["category"] = category
                break

        return result


search_service = SearchService()
