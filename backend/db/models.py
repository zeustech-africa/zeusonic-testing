from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Numeric, Float, Text
from sqlalchemy.sql import func
from .database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(128), unique=True, index=True, nullable=False)
    owner = Column(String(128), nullable=False)
    tier = Column(String(32), default="FREE", nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class AudioJob(Base):
    __tablename__ = "audio_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(36), unique=True, index=True, nullable=False)
    filename = Column(String(256), nullable=False)
    status = Column(String(50), nullable=False, index=True)
    owner = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(32), unique=True, index=True, nullable=False)  # FREE, CREATOR, PRO
    name = Column(String(128), nullable=False)
    price_monthly = Column(Numeric, nullable=True)
    price_yearly = Column(Numeric, nullable=True)
    features = Column(JSON, nullable=False, default={})  # authoritative feature map
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(128), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    stripe_customer_id = Column(String(128), nullable=True, index=True)
    stripe_subscription_id = Column(String(128), nullable=True, index=True)
    plan_id = Column(Integer, nullable=True, index=True)
    plan_code = Column(String(32), nullable=True, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)  # active | past_due | canceled | trialing
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    current_period_end = Column(DateTime, nullable=True)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class PendingRegistration(Base):
    """Temporary registration intent before OTP verification."""
    __tablename__ = "pending_registrations"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    otp_hash = Column(String(255), nullable=False)
    otp_expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    tier = Column(String(32), default="FREE", nullable=False, index=True)
    otp_hash = Column(String(255), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class StripeEvent(Base):
    __tablename__ = "stripe_events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String(128), unique=True, index=True, nullable=False)
    event_type = Column(String(128), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    code_hash = Column(String(128), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class AudioTrack(Base):
    __tablename__ = "audio_tracks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    filename = Column(String(256), nullable=False)
    original_filename = Column(String(256), nullable=False)
    file_size = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=True)
    status = Column(String(32), nullable=False, default="uploaded", index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)


class AudioAnalysis(Base):
    __tablename__ = "audio_analysis"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False, index=True, unique=True)
    bpm = Column(Float, nullable=True)
    musical_key = Column(String(8), nullable=True)
    duration_seconds = Column(Float, nullable=False)
    loudness_lufs = Column(Float, nullable=True)
    sample_rate = Column(Integer, nullable=True)
    channels = Column(Integer, nullable=True)
    bit_depth = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class AudioProcessing(Base):
    __tablename__ = "audio_processing"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    process_type = Column(String(32), nullable=False, index=True)
    output_filename = Column(String(256), nullable=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)


class AudioStem(Base):
    __tablename__ = "audio_stems"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    source_track_id = Column(Integer, nullable=False, index=True)
    stem_type = Column(String(32), nullable=False, index=True)
    file_path = Column(String(512), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class BeatTransformJob(Base):
    __tablename__ = "beat_transform_jobs"

    id = Column(Integer, primary_key=True, index=True)
    track_id = Column(Integer, nullable=False, index=True)
    source_style = Column(String(64), nullable=False, default="unknown")
    target_style = Column(String(64), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="pending", index=True)
    output_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    completed_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    project_id = Column(Integer, nullable=True, index=True)
    resource_type = Column(String(64), nullable=False, index=True)
    resource_id = Column(Integer, nullable=True, index=True)
    event_type = Column(String(32), nullable=False, index=True)
    action = Column(String(32), nullable=False, index=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
