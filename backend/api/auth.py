from datetime import datetime, timedelta
import hashlib
import secrets

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from sqlalchemy.orm import Session

from backend.core.auth import hash_password, verify_password, create_access_token
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.db.database import get_db
from backend.db import models
from backend.services.email_service import send_otp_email

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


@router.post("/register", response_model=RegisterResponse, status_code=202)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    """
    Stage 1: Register a new account (pending OTP verification).
    
    Creates a pending registration record with:
    - Email and hashed password
    - 6-digit OTP (hashed, 10-minute expiry)
    - No user account created yet
    
    Returns 202 Accepted (not 201 Created).
    User must verify OTP via POST /auth/verify-otp to complete registration.
    """
    email = payload.email.strip().lower()
    logger.info("[AUTH][REGISTER] Starting registration flow for: %s", email)

    # Check if user already exists
    try:
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            logger.warning("[AUTH][REGISTER] User already exists: %s", email)
            raise HTTPException(status_code=409, detail="Email already registered")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[AUTH][REGISTER] Error checking existing user for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Database error during email check")

    # Check if pending registration already exists
    try:
        existing_pending = db.query(models.PendingRegistration).filter(
            models.PendingRegistration.email == email
        ).first()
        
        if existing_pending:
            # Check if OTP expired
            if datetime.utcnow() > existing_pending.otp_expires_at:
                # Expired - delete and allow re-registration
                logger.info("[AUTH][REGISTER] Expired pending registration for %s, deleting", email)
                db.delete(existing_pending)
                db.commit()
            else:
                # Still valid - inform user
                logger.warning("[AUTH][REGISTER] Valid pending registration already exists for %s", email)
                raise HTTPException(
                    status_code=409, 
                    detail="Registration already pending. Check your email for verification code."
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[AUTH][REGISTER] Error checking pending registration for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Database error during registration check")

    # Hash password
    try:
        password_hash = hash_password(payload.password)
        logger.info("[AUTH][REGISTER] Password hashed for %s", email)
    except Exception as e:
        logger.error("[AUTH][REGISTER] Error hashing password for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Failed to hash password")

    # Generate OTP
    try:
        otp = _generate_otp()
        otp_hash = _hash_otp(otp)
        otp_expires_at = datetime.utcnow() + timedelta(minutes=settings.verification_code_minutes)
        logger.info("[AUTH][REGISTER] OTP generated for %s (expires: %s)", email, otp_expires_at)
    except Exception as e:
        logger.error("[AUTH][REGISTER] Error generating OTP for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Failed to generate verification code")

    # Create pending registration
    try:
        pending = models.PendingRegistration(
            email=email,
            password_hash=password_hash,
            otp_hash=otp_hash,
            otp_expires_at=otp_expires_at,
        )
        db.add(pending)
        db.commit()
        db.refresh(pending)
        logger.info("[AUTH][REGISTER] Pending registration created for %s (id=%s)", email, pending.id)
    except Exception as e:
        db.rollback()
        logger.error("[AUTH][REGISTER] Error creating pending registration for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Failed to create pending registration")

    # Send OTP via email (non-blocking failure)
    try:
        send_otp_email(email, otp)
        logger.info("[AUTH][REGISTER] OTP email sent to %s", email)
    except Exception as e:
        logger.warning("[AUTH][REGISTER] Failed to send OTP email to %s: %s", email, e)
        # Don't fail registration if email fails
    
    return {
        "email": email,
        "is_verified": False,
        "message": f"Verification code sent to {email}. Check your inbox and verify to complete registration.",
    }


@router.post("/verify-otp")
def verify_otp(payload: OtpVerifyRequest, db: Session = Depends(get_db)):
    """
    Stage 2: Verify OTP and complete registration.
    
    - Validates OTP from pending registration
    - Creates user account in users table
    - Marks user as verified (is_verified=True)
    - Cleans up pending registration
    - Returns success message
    
    User can then login with credentials.
    """
    email = payload.email.strip().lower()
    logger.info("[AUTH][OTP] Starting OTP verification for: %s", email)
    
    # Check if user already exists (completed registration)
    try:
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            if existing_user.is_verified:
                logger.warning("[AUTH][OTP] User already verified: %s", email)
                raise HTTPException(status_code=400, detail="Email already verified. Please login.")
            else:
                # Legacy flow: user exists but not verified (has OTP on user table)
                logger.info("[AUTH][OTP] Using legacy verification flow for: %s", email)
                return _verify_otp_legacy(payload, db, existing_user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[AUTH][OTP] Error checking existing user for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Database error during verification")

    # Look up pending registration
    try:
        pending = db.query(models.PendingRegistration).filter(
            models.PendingRegistration.email == email
        ).first()
        
        if not pending:
            logger.warning("[AUTH][OTP] No pending registration found for: %s", email)
            raise HTTPException(status_code=404, detail="No pending registration found. Please register first.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[AUTH][OTP] Error looking up pending registration for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Database error during verification")

    # Check OTP expiry
    now = datetime.utcnow()
    if now > pending.otp_expires_at:
        logger.warning("[AUTH][OTP] OTP expired for %s (expired at %s)", email, pending.otp_expires_at)
        # Clean up expired pending registration
        try:
            db.delete(pending)
            db.commit()
        except Exception:
            pass
        raise HTTPException(status_code=400, detail="Verification code expired. Please register again.")

    # Validate OTP
    provided_otp_hash = _hash_otp(payload.otp)
    if pending.otp_hash != provided_otp_hash:
        logger.warning("[AUTH][OTP] Invalid OTP provided for %s", email)
        raise HTTPException(status_code=400, detail="Invalid verification code")

    logger.info("[AUTH][OTP] OTP validated for %s", email)

    # Create user account
    try:
        user = models.User(
            email=email,
            password_hash=pending.password_hash,
            is_verified=True,  # Mark as verified immediately
            tier="FREE",
        )
        db.add(user)
        db.flush()  # Get user.id without committing yet
        logger.info("[AUTH][USER_CREATE] User created: %s (id=%s, verified=True)", email, user.id)
    except Exception as e:
        db.rollback()
        logger.error("[AUTH][USER_CREATE] Error creating user for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Failed to create user account")

    # Clean up pending registration
    try:
        db.delete(pending)
        db.commit()
        logger.info("[AUTH][OTP] Pending registration cleaned up for %s", email)
    except Exception as e:
        db.rollback()
        logger.error("[AUTH][OTP] Error cleaning up pending registration for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Failed to complete registration")

    logger.info("[AUTH][OTP] Registration completed successfully for %s", email)
    return {"message": "Email verified successfully. You can now login."}


def _verify_otp_legacy(payload: OtpVerifyRequest, db: Session, user: models.User):
    """
    Legacy OTP verification for users created with old flow.
    Validates OTP stored on user table (not pending_registrations).
    """
    email = user.email
    logger.info("[AUTH][OTP][LEGACY] Verifying OTP for existing user: %s", email)

    # Check if OTP exists and hasn't expired
    now = datetime.utcnow()
    if not user.otp_hash or not user.otp_expires_at:
        logger.warning("[AUTH][OTP][LEGACY] No OTP found for user: %s", email)
        raise HTTPException(status_code=400, detail="No verification code requested")
    
    if now > user.otp_expires_at:
        # OTP expired, clear it
        logger.warning("[AUTH][OTP][LEGACY] OTP expired for user: %s", email)
        user.otp_hash = None
        user.otp_expires_at = None
        db.add(user)
        db.commit()
        raise HTTPException(status_code=400, detail="Verification code expired. Please register again.")

    # Validate OTP
    provided_otp_hash = _hash_otp(payload.otp)
    if user.otp_hash != provided_otp_hash:
        logger.warning("[AUTH][OTP][LEGACY] Invalid OTP for user: %s", email)
        raise HTTPException(status_code=400, detail="Invalid verification code")

    # Mark user as verified and invalidate OTP
    user.is_verified = True
    user.otp_hash = None
    user.otp_expires_at = None
    db.add(user)
    db.commit()

    logger.info("[AUTH][OTP][LEGACY] User verified successfully: %s", email)
    return {"message": "Email verified successfully. You can now login."}


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

