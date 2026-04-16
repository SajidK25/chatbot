import os
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")
    supabase_service_key: str = Field(default="", alias="SUPABASE_SERVICE_KEY")
    cohere_api_key: str = Field(default="", alias="COHERE_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    whatsapp_token: str = Field(default="", alias="WHATSAPP_TOKEN")
    whatsapp_phone_number_id: str = Field(default="", alias="WHATSAPP_PHONE_NUMBER_ID")
    whatsapp_verify_token: str = Field(
        default="openclaw_verify", alias="WHATSAPP_VERIFY_TOKEN"
    )
    whatsapp_app_secret: str = Field(default="", alias="WHATSAPP_APP_SECRET")
    port: int = Field(default=8000, alias="PORT")
    debug: bool = Field(default=False, alias="DEBUG")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
