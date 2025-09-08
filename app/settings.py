# app/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, AliasChoices
from typing import Optional


class Settings(BaseSettings):
    # -----------------------------
    # Banco de Dados
    # Aceita: DATABASE_URL
    # -----------------------------
    DATABASE_URL: str = Field(...)

    # -----------------------------
    # AWS S3 (aceita vários nomes)
    # Preferidos no Railway:
    #   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_DEFAULT_REGION / AWS_S3_BUCKET
    # Também aceita os seus antigos:
    #   S3_ACCESS_KEY / S3_SECRET_KEY / S3_REGION / S3_BUCKET / S3_ENDPOINT / S3_ENDPOINT_URL
    # -----------------------------
    AWS_ACCESS_KEY_ID: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS_ACCESS_KEY_ID", "S3_ACCESS_KEY"),
    )
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS_SECRET_ACCESS_KEY", "S3_SECRET_KEY"),
    )
    AWS_DEFAULT_REGION: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS_DEFAULT_REGION", "S3_REGION"),
    )
    AWS_S3_BUCKET: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("AWS_S3_BUCKET", "S3_BUCKET"),
    )
    # Endpoint opcional; se não vier, chutamos o padrão pela região
    S3_ENDPOINT_URL: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("S3_ENDPOINT_URL", "S3_ENDPOINT"),
    )

    # -----------------------------
    # Meta / WhatsApp Cloud API
    # Preferidos no Railway:
    #   WHATSAPP_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN
    # Também aceita:
    #   META_WABA_TOKEN, META_WABA_PHONE_ID, META_WABA_VERIFY_TOKEN, META_TOKEN
    # -----------------------------
    WHATSAPP_TOKEN: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WHATSAPP_TOKEN", "META_WABA_TOKEN", "META_TOKEN"),
    )
    WHATSAPP_PHONE_NUMBER_ID: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WHATSAPP_PHONE_NUMBER_ID", "META_WABA_PHONE_ID"),
    )
    WHATSAPP_VERIFY_TOKEN: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("WHATSAPP_VERIFY_TOKEN", "META_WABA_VERIFY_TOKEN"),
    )
    META_WABA_API_BASE: str = "https://graph.facebook.com/v20.0"

    # -----------------------------
    # App
    # -----------------------------
    APP_SECRET: str = Field(default="change-me", validation_alias=AliasChoices("APP_SECRET"))
    APP_ENV: str = "production"
    PUBLIC_BASE_URL: Optional[str] = None  # ex.: https://meuapp.up.railway.app

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # --------- Helpers / computed props ---------
    @property
    def s3_endpoint_effective(self) -> Optional[str]:
        """
        Se não houver endpoint explícito, usa o padrão da região (quando houver).
        """
        if self.S3_ENDPOINT_URL:
            return self.S3_ENDPOINT_URL
        if self.AWS_DEFAULT_REGION:
            return f"https://s3.{self.AWS_DEFAULT_REGION}.amazonaws.com"
        # Último fallback (funciona para us-east-1 e alguns SDKs)
        return "https://s3.amazonaws.com"

    @property
    def has_s3_config(self) -> bool:
        return all([
            self.AWS_ACCESS_KEY_ID,
            self.AWS_SECRET_ACCESS_KEY,
            self.AWS_S3_BUCKET,
        ])

    @property
    def has_whatsapp_config(self) -> bool:
        return all([
            self.WHATSAPP_TOKEN,
            self.WHATSAPP_PHONE_NUMBER_ID,
            self.WHATSAPP_VERIFY_TOKEN,
        ])


settings = Settings()
