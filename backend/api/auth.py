from datetime import datetime, timedelta
import hashlib
import secrets

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from sqlalchemy.orm import Session

from core.auth import hash_password, verify_password, create_access_token
from core.config import settings
from core.logging import get_logger
from db.database import get_db
from db import models
from services.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterResponse(BaseModel):
    email: EmailStr
    is_verified: bool
    message: str


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def _hash_otp(otp: str) -> str:
    """Hash OTP using SHA256."""
    return hashlib.sha256(otp.encode("utf-8")).hexdigest()


def _generate_otp() -> str:
    """Generate a 6-digit OTP."""
    return f"{secrets.randbelow(1_000_000):06d}"


@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.
    
    - Generates a 6-digit OTP
    - Stores OTP hashed (never plain text)
    - Sends OTP via Resend email
    - Sets OTP expiry to 10 minutes
    - Returns: email, is_verified status, and confirmation message
    """
    email = payload.email.strip().lower()

    # Check if user already exists
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Create new user account
    user = models.User(
        email=email,
        password_hash=hash_password(payload.password),
        is_verified=False,
        tier="FREE",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate 6-digit OTP
    otp = _generate_otp()
    otp_hash = _hash_otp(otp)
    otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.verification_code_minutes)

    # Store hashed OTP on user account
    user.otp_hash = otp_hash
    user.otp_expires_at = otp_expires_at
    db.add(user)
    db.commit()

    # Send OTP via Resend
    try:
        send_otp_email(email, otp)
        logger.info(f"OTP email sent successfully to {email}")
    except Exception as e:
        logger.warning(f"Failed to send OTP email to {email}: {e}")
        # In production, might want to retry or queue for later
    
    return {
        "email": user.email,
        "is_verified": user.is_verified,
        "message": f"Verification code sent to {email}. Check your inbox.",
    }


@router.post("/verify-otp")
def verify_otp(payload: OtpVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP for email verification.
    
    - Validates OTP against stored hash
    - Checks OTP expiry (10 minutes)
    - Marks user is_verified = true
    - Invalidates OTP after success
    - Returns: success message
    """
    email = payload.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Check if OTP exists and hasn't expired
    now = datetime.utcnow()
    if not user.otp_hash or not user.otp_expires_at:
        raise HTTPException(status_code=400, detail="No verification code requested")
    
    if now > user.otp_expires_at:
        # OTP expired, clear it
        user.otp_hash = None
        user.otp_expires_at = None
        db.add(user)
        db.commit()
        raise HTTPException(status_code=400, detail="Verification code expired. Please register again.")

    # Validate OTP
    provided_otp_hash = _hash_otp(payload.otp)
    if user.otp_hash != provided_otp_hash:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Mark user as verified and invalidate OTP
    user.is_verified = True
    user.otp_hash = None
    user.otp_expires_at = None
    db.add(user)
    db.commit()

    return {"message": "Email verified successfully"}


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    - Validates credentials
    - Requires email verification (is_verified = true)
    - Returns: JWT access token with 60-minute expiry
    """
    if not settings.jwt_secret:
        raise HTTPException(
            status_code=500,
            detail="Server configuration error: JWT_SECRET not set"
        )
    
    email = payload.email.strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Require email verification
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your email first.")

    # Create access token
    token = create_access_token(subject=user.email)
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_access_token_minutes * 60,
    )

