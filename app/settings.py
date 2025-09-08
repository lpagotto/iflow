# app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Postgres
    DATABASE_URL: str

    # S3 / MinIO
    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_SECRET_KEY: str | None = None
    S3_BUCKET: str | None = None

    # Meta WhatsApp
    META_WABA_TOKEN: str | None = None
    META_WABA_PHONE_ID: str | None = None
    META_WABA_VERIFY_TOKEN: str | None = None
    META_WABA_API_BASE: str = "https://graph.facebook.com/v20.0"

    # App
    APP_ENV: str = "production"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
