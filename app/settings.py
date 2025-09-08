from pydantic_settings import BaseSettings
from pydantic import AnyUrl

class Settings(BaseSettings):
    APP_SECRET: str = "dev"
    DATABASE_URL: str
    META_TOKEN: str
    WHATSAPP_PHONE_ID: str
    WHATSAPP_VERIFY_TOKEN: str
    S3_ENDPOINT: str | None = None
    S3_REGION: str = "auto"
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_BUCKET: str | None = None
    PUBLIC_BASE_URL: str | None = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
