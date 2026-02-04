from fastapi import APIRouter
from backend.core.config import settings
from backend.db.database import engine
from sqlalchemy import text
from pathlib import Path

router = APIRouter()

@router.get("/health", tags=["health"])
async def health_check():
    """Lightweight health check reporting app status and basic readiness."""
    # Check DB accessible
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False

    # Check storage directory writable
    storage_ok = False
    try:
        test_dir = Path(settings.storage_path)
        test_dir.mkdir(parents=True, exist_ok=True)
        tmp = test_dir / ".healthcheck"
        tmp.write_text("ok")
        tmp.unlink(missing_ok=True)
        storage_ok = True
    except Exception:
        storage_ok = False

    return {
        "status": "ok",
        "db": "ok" if db_ok else "error",
        "storage": "ok" if storage_ok else "error",
        "env": settings.app_env,
    }
