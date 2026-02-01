from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.core.config import settings

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
