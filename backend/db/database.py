from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from core.config import settings

# Database file: configurable via settings.database_path
DB_PATH = Path(settings.database_path)
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# Use check_same_thread False for SQLite + SQLAlchemy in a threaded app
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)

    # If Alembic is NOT being used (dev convenience), keep legacy ALTER behavior.
    # If Alembic migrations are present (alembic_version table), skip ALTER logic so migrations are authoritative.
    with engine.connect() as conn:
        try:
            has_alembic = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")).fetchone() is not None
        except Exception:
            has_alembic = False

        if has_alembic:
            # Alembic is present: migrations should manage schema evolution
            return

        # Fallback: ensure columns exist for development without Alembic
        try:
            res = conn.execute(text("PRAGMA table_info(api_keys)"))
            cols = [r[1] for r in res.fetchall()]
            if 'tier' not in cols:
                conn.execute(text("ALTER TABLE api_keys ADD COLUMN tier VARCHAR(32) DEFAULT 'FREE'"))
        except Exception:
            pass

        try:
            res = conn.execute(text("PRAGMA table_info(audio_jobs)"))
            cols = [r[1] for r in res.fetchall()]
            if 'owner' not in cols:
                conn.execute(text("ALTER TABLE audio_jobs ADD COLUMN owner VARCHAR(128)"))
        except Exception:
            pass

        try:
            res = conn.execute(text("PRAGMA table_info(plans)"))
            cols = [r[1] for r in res.fetchall()]
            if 'updated_at' not in cols:
                conn.execute(text("ALTER TABLE plans ADD COLUMN updated_at DATETIME DEFAULT (datetime('now'))"))
        except Exception:
            pass

        try:
            res = conn.execute(text("PRAGMA table_info(subscriptions)"))
            cols = [r[1] for r in res.fetchall()]
            if 'user_id' not in cols:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN user_id INTEGER"))
            if 'stripe_customer_id' not in cols:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN stripe_customer_id VARCHAR(128)"))
            if 'stripe_subscription_id' not in cols:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN stripe_subscription_id VARCHAR(128)"))
            if 'plan_id' not in cols:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN plan_id INTEGER"))
            if 'current_period_end' not in cols:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN current_period_end DATETIME"))
            if 'updated_at' not in cols:
                conn.execute(text("ALTER TABLE subscriptions ADD COLUMN updated_at DATETIME DEFAULT (datetime('now'))"))
        except Exception:
            pass

        try:
            res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"))
            if not res.fetchone():
                conn.execute(text("""
                    CREATE TABLE audit_logs (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER,
                        project_id INTEGER,
                        resource_type VARCHAR(64) NOT NULL,
                        resource_id INTEGER,
                        event_type VARCHAR(32) NOT NULL,
                        action VARCHAR(32) NOT NULL,
                        details JSON,
                        created_at DATETIME DEFAULT (datetime('now'))
                    )
                """))
                conn.execute(text("CREATE INDEX idx_audit_user ON audit_logs(user_id)"))
                conn.execute(text("CREATE INDEX idx_audit_project ON audit_logs(project_id)"))
                conn.execute(text("CREATE INDEX idx_audit_type ON audit_logs(event_type)"))
        except Exception:
            pass

        # Add OTP fields to users table if not present
        try:
            res = conn.execute(text("PRAGMA table_info(users)"))
            cols = [r[1] for r in res.fetchall()]
            if 'otp_hash' not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN otp_hash VARCHAR(255)"))
            if 'otp_expires_at' not in cols:
                conn.execute(text("ALTER TABLE users ADD COLUMN otp_expires_at DATETIME"))
        except Exception:
            pass

        conn.commit()

