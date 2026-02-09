from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta
import secrets

from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.db.database import get_db, SessionLocal
from backend.db import models
from backend.core.config import settings
from backend.core.logging import get_logger

import jwt
from passlib.context import CryptContext
import bcrypt

APIKEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=APIKEY_NAME, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = get_logger(__name__)


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


def _require_jwt_secret() -> str:
    if not settings.jwt_secret:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="JWT secret is not configured")
    return settings.jwt_secret


def hash_password(password: str) -> str:
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.exception("[AUTH][HASH] Password hashing failed via passlib: %s", e)
        # Fallback: direct bcrypt hashing (same algorithm, avoid passlib backend issues)
        try:
            salt = bcrypt.gensalt()
            hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
            return hashed.decode("utf-8")
        except Exception as fallback_error:
            logger.exception("[AUTH][HASH] Password hashing failed via bcrypt fallback: %s", fallback_error)
            raise ValueError("Failed to hash password")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash. Returns False on mismatch or error (never throws)."""
    try:
        result = pwd_context.verify(password, password_hash)
        logger.debug("[AUTH][VERIFY_PASSWORD] Verification completed (result=%s)", result)
        return result
    except Exception as e:
        logger.error("[AUTH][VERIFY_PASSWORD] Verification threw exception: %s", e, exc_info=True)
        return False


def create_access_token(subject: str) -> str:
    """Create JWT access token. Wraps exceptions for controlled error handling."""
    try:
        secret = _require_jwt_secret()
        expires = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_minutes)
        payload = {"sub": subject, "exp": expires}
        logger.debug("[AUTH][CREATE_TOKEN] Encoding JWT (sub=%s, algorithm=%s, expires=%s)", 
                     subject, settings.jwt_algorithm, expires)
        token = jwt.encode(payload, secret, algorithm=settings.jwt_algorithm)
        logger.debug("[AUTH][CREATE_TOKEN] JWT encode successful")
        return token
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[AUTH][CREATE_TOKEN] JWT encoding failed: %s", e)
        raise ValueError(f"Failed to create access token: {e}")


def decode_access_token(token: str) -> str:
    secret = _require_jwt_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.jwt_algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    subject = payload.get("sub")
    if not subject:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return subject


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme), db: Session = Depends(get_db)) -> models.User:
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    subject = decode_access_token(credentials.credentials)
    user = db.query(models.User).filter(models.User.email == subject).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return user


async def get_current_verified_user(user: models.User = Depends(get_current_user)) -> models.User:
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return user


async def get_api_key(api_key_header_value: str = Security(api_key_header), db: Session = Depends(get_db)) -> APIKeyModel:
    """FastAPI dependency to validate X-API-Key header and return the API key model.

    Validates the API key from the X-API-Key header using a two-tier system:
    1. First checks against ZEUSONIC_API_KEY environment variable (if set)
    2. Falls back to database lookup for user-specific API keys
    
    Returns clear error messages for missing or invalid keys.
    Logs authentication failures (without exposing sensitive data).

    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    from backend.core.logging import get_logger
    logger = get_logger(__name__)
    
    if not api_key_header_value:
        logger.warning("API authentication failed: Missing X-API-Key header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-Key header with your request.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # TIER 1: Check master API key from environment (production/deployment key)
    if settings.zeusonic_api_key and api_key_header_value == settings.zeusonic_api_key:
        logger.info("API authentication successful: Master API key (ZEUSONIC_API_KEY)")
        return APIKeyModel(
            key=api_key_header_value,
            owner="master",
            tier="PRO",  # Master key gets full access
            created_at=datetime.utcnow()
        )
    
    # TIER 2: Validate API key from database (user-specific keys)
    row = db.query(models.ApiKey).filter(
        models.ApiKey.key == api_key_header_value,
        models.ApiKey.is_active == True
    ).first()
    
    if row:
        # Log successful authentication (non-sensitive info only)
        logger.debug(f"API authentication successful for owner: {row.owner}, tier: {row.tier}")
        return APIKeyModel(key=row.key, owner=row.owner, tier=row.tier, created_at=row.created_at)
    
    # Authentication failed - log and reject
    key_preview = api_key_header_value[:8] + "..." if len(api_key_header_value) > 8 else "***"
    logger.warning(f"API authentication failed: Invalid or inactive API key (preview: {key_preview})")
    
    # Provide hint about master key if not configured
    detail = "Invalid API key. Verify your X-API-Key header value."
    if not settings.zeusonic_api_key:
        logger.debug("Note: ZEUSONIC_API_KEY environment variable not configured (database-only mode)")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "ApiKey"},
    )
