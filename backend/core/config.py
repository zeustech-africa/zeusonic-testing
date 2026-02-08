from pathlib import Path
from typing import Optional, Any
import json

try:
    # Optional: load .env into environment variables if python-dotenv is installed
    from dotenv import load_dotenv

    # Load .env from project root if present. This is safe if .env is missing.
    project_root = Path(__file__).resolve().parents[2]
    # Load backend/.env first (where our config actually lives)
    load_dotenv(project_root / "backend" / ".env")
    # Also load root .env if present
    load_dotenv(project_root / ".env")
except Exception:
    # Don't fail import if python-dotenv is not available or .env is missing
    project_root = Path(__file__).resolve().parents[2]

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, Field, model_validator, PrivateAttr
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables or an optional .env file."""

    # Basic app metadata
    app_name: str = "Zeusonic API"
    version: str = "0.1.0"
    company: str = "ZeusTech"

    # Environment
    app_env: str = "development"  # development | production

    # Beta mode toggle (dev-only, non-functional feature gate)
    beta_mode: bool = False

    # Operational kill switches (server-authoritative)
    disable_uploads: bool = False

    # Auth / JWT
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 60
    verification_code_minutes: int = 10
    
    # Master API Key (optional - for production deployments)
    zeusonic_api_key: Optional[str] = Field(default=None, validation_alias="ZEUSONIC_API_KEY")

    # Email (Resend)
    resend_api_key: Optional[str] = None
    resend_from_email: str = "Zeusonic <no-reply@zeustechafrica.com>"

    # Stripe (billing)
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_monthly_price_id: Optional[str] = None
    stripe_yearly_price_id: Optional[str] = None
    frontend_base_url: str = "http://localhost:3000"

    # CORS configuration - raw string field to avoid Pydantic v2 JSON parsing
    allowed_origins_raw: Optional[str] = Field(default=None, validation_alias="ALLOWED_ORIGINS")

    # Paths (can be overridden via env vars)
    storage_path: Path = Path(project_root) / "backend" / "storage"
    database_path: Path = Path(project_root) / "backend" / "storage" / "zeusonic.db"
    api_key_path: Path = Path(project_root) / "backend" / ".demo_api_key"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid"  # Don't auto-create fields from env vars
    )

    @property
    def allowed_origins(self) -> list[str]:
        """Parse ALLOWED_ORIGINS from comma-separated or JSON array format."""
        if not self.allowed_origins_raw:
            return []
        
        raw = self.allowed_origins_raw.strip()
        
        # Try JSON array format first
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if str(v).strip()]
            except Exception:
                pass
        
        # Parse as comma-separated
        return [v.strip() for v in raw.split(",") if v.strip()]


settings = Settings()
