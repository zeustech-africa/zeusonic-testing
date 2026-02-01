import os
import tempfile
from alembic.config import Config
from alembic import command
from backend.db.database import DATABASE_URL


def test_migrations_apply_and_idempotent(tmp_path):
    # Run alembic upgrade head against the configured DB
    cfg = Config(os.path.join(os.path.dirname(__file__), '..', 'backend', 'alembic.ini'))
    # Apply
    command.upgrade(cfg, 'head')
    # Re-apply (idempotent)
    command.upgrade(cfg, 'head')
    # Downgrade one and re-upgrade
    command.downgrade(cfg, '-1')
    command.upgrade(cfg, 'head')
    assert True
