from typing import List, Literal, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
import json


class Settings(BaseSettings):

    AUTH_MODE: Literal["DEV", "PROD"] = "DEV"

    JWT_SECRET: str = "dev-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_MINUTES: int = 60
    RESEND_API_KEY: Optional[str] = None

    database_path: str = "zeusonic.db"
    storage_path: str = "storage"

    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]

    app_env: str = "development"

    # Runtime aliases used across the codebase
    jwt_secret: str = "dev-secret-key"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60
    resend_api_key: Optional[str] = None
    zeusonic_api_key: Optional[str] = None
    api_key_path: str = "backend/.demo_api_key"

    app_name: str = "Zeusonic"
    version: str = "0.1.0"
    company: str = "Zeusonic"
    beta_mode: bool = False
    disable_uploads: bool = False
    verification_code_minutes: int = 10

    stripe_secret_key: Optional[str] = None
    stripe_monthly_price_id: Optional[str] = None
    stripe_yearly_price_id: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    frontend_base_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_allowed_origins(cls, v):
        if isinstance(v, list):
            return v

        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [origin.strip() for origin in v.split(",")]

        return v


settings = Settings()

ENVIRONMENT = settings.app_env

