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
    resend_api_key: Optional[str] = None
    resend_from_email: str = "Zeusonic <no-reply@zeustechafrica.com>"

    # Stripe (billing)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_monthly_price_id: Optional[str] = None
    stripe_yearly_price_id: Optional[str] = None
    frontend_base_url: str = "http://localhost:3000"
    
    # CORS configuration
    allowed_origins: Optional[list[str]] = None

    # Paths (can be overridden via env vars)
    storage_path: Path = Path(project_root) / "backend" / "storage"
    database_path: Path = Path(project_root) / "backend" / "storage" / "zeusonic.db"
    api_key_path: Path = Path(project_root) / "backend" / ".demo_api_key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="before")
    @classmethod
    def _normalize_env_values(cls, data):
        # Cloud platforms (Render, Railway, etc.) may inject env vars with trailing
        # newlines or whitespace, which can break strict validation of required values.
        # Normalize all string inputs early so production rules remain strict.
        if not isinstance(data, dict):
            return data

        cleaned = {}
        for key, value in data.items():
            if isinstance(value, str):
                cleaned[key] = value.strip()
            else:
                cleaned[key] = value

        # Boolean env vars can arrive as strings (e.g., "false\n", "0") in cloud envs;
        # normalize known values without relaxing validation for unknown inputs.
        for bool_key in ("debug", "beta_mode", "disable_uploads"):
            value = cleaned.get(bool_key)
            if isinstance(value, str):
                normalized = value.strip().lower()
                if normalized in {"true", "1", "yes", "y", "on"}:
                    cleaned[bool_key] = True
                elif normalized in {"false", "0", "no", "n", "off"}:
                    cleaned[bool_key] = False

        return cleaned

    @model_validator(mode="after")
    def _sync_app_env(self):
        if self.app_env == "development" and self.environment != "development":
            object.__setattr__(self, "app_env", self.environment)
        return self


settings = Settings()
