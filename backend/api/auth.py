from datetime import datetime, timedelta
import hashlib
import secrets

from fastapi import APIRouter, HTTPException, status, Depends, Request
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
    message: str
    registration_id: str


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


def _validate_pending_otp(pending: models.PendingRegistration, provided_otp: str, email: str, db: Session) -> None:
    """Validate pending registration OTP or raise HTTPException."""
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

    provided_otp_hash = _hash_otp(provided_otp)
    if pending.otp_hash != provided_otp_hash:
        logger.warning("[AUTH][OTP] Invalid OTP provided for %s", email)
        raise HTTPException(status_code=400, detail="Invalid verification code")

    logger.info("[AUTH][OTP] OTP validated for %s", email)


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
        "message": "Verification code sent",
        "registration_id": str(pending.id),
    }


@router.post("/verify-otp")
def verify_otp(payload: OtpVerifyRequest, request: Request, db: Session = Depends(get_db)):
    return _verify_otp_impl(payload, request, db)


@router.post("/verify")
def verify(payload: OtpVerifyRequest, request: Request, db: Session = Depends(get_db)):
    return _verify_otp_impl(payload, request, db)


def _verify_otp_impl(payload: OtpVerifyRequest, request: Request, db: Session):
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
    origin = request.headers.get("origin")
    logger.info("[AUTH][OTP] Verify endpoint hit (origin=%s, email=%s)", origin, email)
    
    # Check if user already exists (completed registration)
    try:
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user and existing_user.is_verified:
            logger.warning("[AUTH][OTP] User already verified: %s", email)
            raise HTTPException(status_code=400, detail="Email already verified. Please login.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[AUTH][OTP] Error checking existing user for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Database error during verification")

    # Look up pending registration (authoritative OTP for new flow)
    try:
        pending = db.query(models.PendingRegistration).filter(
            models.PendingRegistration.email == email
        ).first()
    except Exception as e:
        logger.error("[AUTH][OTP] Error looking up pending registration for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Database error during verification")

    if existing_user and not existing_user.is_verified:
        # If a pending registration exists, prefer it (new flow) and promote into the existing user record.
        if pending:
            _validate_pending_otp(pending, payload.otp, email, db)

            try:
                existing_user.password_hash = pending.password_hash
                existing_user.is_verified = True
                existing_user.otp_hash = None
                existing_user.otp_expires_at = None
                db.add(existing_user)
                db.commit()
                logger.info("[AUTH][USER_UPDATE] Existing user verified via pending registration: %s (id=%s)", email, existing_user.id)
            except Exception as e:
                db.rollback()
                logger.error("[AUTH][USER_UPDATE] Error updating existing user for %s: %s", email, e)
                raise HTTPException(status_code=500, detail="Failed to verify user account")

            # Clean up pending registration
            try:
                db.delete(pending)
                db.commit()
                logger.info("[AUTH][OTP] Pending registration cleaned up for %s", email)
            except Exception as e:
                db.rollback()
                logger.error("[AUTH][OTP] Error cleaning up pending registration for %s: %s", email, e)
                logger.warning("[AUTH][OTP] Proceeding despite cleanup error for %s", email)

            logger.info("[AUTH][OTP] Registration completed successfully for %s", email)
            return {"message": "Email verified successfully. You can now login."}

        # Legacy flow: user exists but not verified (has OTP on user table)
        logger.info("[AUTH][OTP] Using legacy verification flow for: %s", email)
        return _verify_otp_legacy(payload, db, existing_user)

    if not pending:
        logger.warning("[AUTH][OTP] No pending registration found for: %s", email)
        raise HTTPException(status_code=404, detail="No pending registration found. Please register first.")

    _validate_pending_otp(pending, payload.otp, email, db)

    # Create user account - ATOMIC TRANSACTION
    try:
        user = models.User(
            email=email,
            password_hash=pending.password_hash,
            is_verified=True,  # Mark as verified immediately
            tier="FREE",
        )
        db.add(user)
        db.commit()  # Commit user FIRST, before any cleanup
        db.refresh(user)  # Refresh to get the committed id
        logger.info("[AUTH][USER_CREATE] User created and committed: %s (id=%s, verified=True)", email, user.id)
    except Exception as e:
        db.rollback()
        logger.error("[AUTH][USER_CREATE] Error creating user for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Failed to create user account")

    # Clean up pending registration - SEPARATE TRANSACTION
    try:
        db.delete(pending)
        db.commit()
        logger.info("[AUTH][OTP] Pending registration cleaned up for %s", email)
    except Exception as e:
        db.rollback()
        logger.error("[AUTH][OTP] Error cleaning up pending registration for %s: %s", email, e)
        # Don't fail if cleanup fails - user is already created and verified
        logger.warning("[AUTH][OTP] Proceeding despite cleanup error for %s", email)

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
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    """
    Login with email and password.
    
    - Validates credentials
    - Requires email verification (is_verified = true)
    - Returns: JWT access token with 60-minute expiry
    """
    email = payload.email.strip().lower()
    origin = request.headers.get("origin")
    
    # ======= ENTRY LOGGING =======
    logger.info("[AUTH][LOGIN] >>> LOGIN ENTRY (origin=%s, email=%s)", origin, email)
    
    # ======= ENVIRONMENT SECRET VALIDATION =======
    try:
        if not settings.jwt_secret:
            logger.error("[AUTH][LOGIN] CRITICAL: JWT_SECRET not configured in environment")
            raise HTTPException(
                status_code=500,
                detail="Server configuration error: JWT_SECRET not set"
            )
        logger.debug("[AUTH][LOGIN] JWT_SECRET validation passed")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("[AUTH][LOGIN] Error validating JWT_SECRET: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    
    # ======= USER FETCH =======
    try:
        user = db.query(models.User).filter(models.User.email == email).first()
        logger.info("[AUTH][LOGIN] User query completed (email=%s, found=%s)", email, bool(user))
    except Exception as e:
        logger.exception("[AUTH][LOGIN] Database error during user fetch for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Database error")
    
    if not user:
        logger.warning("[AUTH][LOGIN] User not found: %s", email)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    logger.info("[AUTH][LOGIN] User found (id=%s, verified=%s)", user.id, user.is_verified)

    # ======= VALIDATE PASSWORD HASH EXISTS =======
    if not user.password_hash:
        logger.error("[AUTH][LOGIN] Missing password_hash for %s (id=%s)", email, user.id)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ======= PASSWORD VERIFICATION =======
    try:
        logger.debug("[AUTH][LOGIN] Starting password verification for %s", email)
        password_valid = verify_password(payload.password, user.password_hash)
        logger.info("[AUTH][LOGIN] Password verification completed (email=%s, valid=%s)", email, password_valid)
    except Exception as e:
        logger.exception("[AUTH][LOGIN] Password verification threw exception for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Authentication error")
    
    if not password_valid:
        logger.warning("[AUTH][LOGIN] Invalid password for %s", email)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # ======= VERIFICATION STATUS CHECK =======
    if not user.is_verified:
        logger.warning("[AUTH][LOGIN] User not verified: %s", email)
        raise HTTPException(status_code=403, detail="Email not verified. Please verify your email first.")
    
    logger.info("[AUTH][LOGIN] User verification check passed (email=%s)", email)

    # ======= JWT TOKEN CREATION =======
    try:
        logger.debug("[AUTH][LOGIN] Creating JWT token for %s", email)
        token = create_access_token(subject=user.email)
        logger.info("[AUTH][LOGIN] JWT token created successfully (email=%s)", email)
    except Exception as e:
        logger.exception("[AUTH][LOGIN] JWT token creation failed for %s: %s", email, e)
        raise HTTPException(status_code=500, detail="Failed to create access token")
    
    # ======= SUCCESS =======
    logger.info("[AUTH][LOGIN] <<< LOGIN SUCCESS (email=%s, token_length=%s)", email, len(token))
    return TokenResponse(
        access_token=token,
        expires_in=settings.jwt_access_token_minutes * 60,
    )

