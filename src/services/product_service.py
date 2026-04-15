from src.database.supabase_client import get_supabase


async def get_product_by_id(product_id: str) -> dict | None:
    supabase = get_supabase()
    response = supabase.table("products").select("*").eq("id", product_id).execute()
    return response.data[0] if response.data else None


async def get_products_by_category(category: str, limit: int = 10) -> list[dict]:
    supabase = get_supabase()
    response = (
        supabase.table("products")
        .select("*")
        .eq("category", category)
        .limit(limit)
        .execute()
    )
    return response.data
