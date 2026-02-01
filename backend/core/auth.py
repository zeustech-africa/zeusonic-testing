from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import secrets

from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session

from backend.db.database import get_db, SessionLocal
from backend.db import models

APIKEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=APIKEY_NAME, auto_error=False)


class APIKeyModel(BaseModel):
    key: str
    owner: str
    tier: str
    created_at: datetime


def create_api_key(owner: str = "demo-user", tier: str = "FREE") -> APIKeyModel:
    """Create and persist a new API key (development use). Ensures tables exist."""
    # Ensure tables are created (safe to call repeatedly)
    from backend.db.database import create_tables

    create_tables()

    key = secrets.token_urlsafe(32)
    db = SessionLocal()
    try:
        ak = models.ApiKey(key=key, owner=owner, tier=tier)
        db.add(ak)
        db.commit()
        db.refresh(ak)
        return APIKeyModel(key=ak.key, owner=ak.owner, tier=ak.tier, created_at=ak.created_at)
    finally:
        db.close()

def list_api_keys() -> List[APIKeyModel]:
    db = SessionLocal()
    try:
        rows = db.query(models.ApiKey).all()
        return [APIKeyModel(key=r.key, owner=r.owner, tier=r.tier, created_at=r.created_at) for r in rows]
    finally:
        db.close()


async def get_api_key(api_key_header_value: str = Security(api_key_header), db: Session = Depends(get_db)) -> APIKeyModel:
    """FastAPI dependency to validate X-API-Key header and return the API key model.

    Raises 401 Unauthorized if missing/invalid.
    """
    if not api_key_header_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    row = db.query(models.ApiKey).filter(models.ApiKey.key == api_key_header_value, models.ApiKey.is_active == True).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return APIKeyModel(key=row.key, owner=row.owner, tier=row.tier, created_at=row.created_at)
