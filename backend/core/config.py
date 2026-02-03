from pathlib import Path
from typing import Optional

try:
    # Optional: load .env into environment variables if python-dotenv is installed
    from dotenv import load_dotenv

    # Load .env from project root if present. This is safe if .env is missing.
    project_root = Path(__file__).resolve().parents[2]
    load_dotenv(project_root / ".env")
except Exception:
    # Don't fail import if python-dotenv is not available or .env is missing
    project_root = Path(__file__).resolve().parents[2]

from pydantic import AliasChoices, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or an optional .env file."""

    # Basic app metadata
    app_name: str = "Zeusonic API"
    version: str = "0.1.0"
    company: str = "ZeusTech"

    # Environment
    app_env: str = Field(
        default="development",
        validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"),
    )  # development | production
    environment: str = "development"  # Alias for compatibility
    debug: bool = False

    # Beta mode toggle (dev-only, non-functional feature gate)
    beta_mode: bool = False

    # Operational kill switches (server-authoritative)
    disable_uploads: bool = False

    # Auth / JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60
    verification_code_minutes: int = 10

    # Email (Resend)
    resend_api_key: str
    resend_from_email: str = "Zeusonic <no-reply@zeustechafrica.com>"

    # Stripe (billing)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_monthly_price_id: Optional[str] = None
    stripe_yearly_price_id: Optional[str] = None
    frontend_base_url: str = "http://localhost:3000"

    # Paths (can be overridden via env vars)
    storage_path: Path = Path(project_root) / "backend" / "storage"
    database_path: Path = Path(project_root) / "backend" / "storage" / "zeusonic.db"
    api_key_path: Path = Path(project_root) / "backend" / ".demo_api_key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def _sync_app_env(self):
        if self.app_env == "development" and self.environment != "development":
            object.__setattr__(self, "app_env", self.environment)
        return self


settings = Settings()
