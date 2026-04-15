from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
from src.config import settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
            options=ClientOptions(
                auth=dict(
                    auto_refresh_token=False,
                    persist_session=False,
                    detect_session_in_url=False,
                )
            ),
        )
    return _supabase_client


def get_supabase_admin() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_key)
