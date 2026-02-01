from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Numeric
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


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    owner = Column(String(128), nullable=False, index=True)
    plan_code = Column(String(32), nullable=False, index=True)
    status = Column(String(32), nullable=False, default="active", index=True)  # active | trialing | canceled | expired
    started_at = Column(DateTime, server_default=func.now(), nullable=False)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
