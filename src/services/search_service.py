import os
import re
from typing import Optional
import cohere
from src.config import settings


class SearchService:
    def __init__(self):
        self._cohere_client = None
        self._supabase = None

    @property
    def cohere_client(self):
        if self._cohere_client is None:
            self._cohere_client = cohere.AsyncClient(api_key=settings.cohere_api_key)
        return self._cohere_client

    @property
    def supabase(self):
        if self._supabase is None:
            from src.database.supabase_client import get_supabase

            self._supabase = get_supabase()
        return self._supabase

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
            "Fashion": [
                "shoes",
                "shirt",
                "jacket",
                "jeans",
                "dress",
                "clothing",
                "sneakers",
                "sweater",
            ],
            "Electronics": [
                "headphones",
                "speaker",
                "watch",
                "charger",
                "keyboard",
                "webcam",
                "earbuds",
            ],
            "Home": [
                "bed",
                "lamp",
                "pillow",
                "clock",
                "candle",
                "plant",
                "storage",
                "basket",
            ],
            "Beauty": [
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

    async def search_products(
        self,
        query: str,
        max_price: Optional[float] = None,
        category: Optional[str] = None,
        gender: Optional[str] = None,
        limit: int = 3,
    ) -> list[dict]:
        try:
            response = await self.cohere_client.embed(
                model="embed-multilingual-v3.0",
                input=[query],
                embedding_types=["float"],
            )
            if hasattr(response, "embeddings") and isinstance(
                response.embeddings, dict
            ):
                query_embedding = response.embeddings.get("float", [[]])[0]
            else:
                return []
        except Exception:
            return []

        filters = []
        params = [query_embedding]

        filters.append("1=1")
        if max_price is not None:
            filters.append("price <= $2")
            params.append(max_price)
        if category:
            idx = 2 + len([m for m in [max_price] if m is not None])
            filters.append(f"LOWER(category) = ${idx}")
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


search_service = SearchService()
