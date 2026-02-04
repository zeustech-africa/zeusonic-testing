from __future__ import with_statement

import sys
import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ensure package imports work from root or backend directory
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
project_root = os.path.abspath(os.path.join(backend_dir, '..'))

# Add both paths to support running from different contexts
if project_root not in sys.path:
    sys.path.insert(0, project_root)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)

# Set required environment variables for migrations (they're not actually used during schema migration)
os.environ.setdefault('JWT_SECRET', 'dummy-secret-for-migrations')
os.environ.setdefault('RESEND_API_KEY', 'dummy-key-for-migrations')

# import target metadata from the application's models
try:
    # Try importing from project root (when run from root)
    from backend.db.database import Base
    from backend.core.config import settings
    from backend.db import models  # noqa: F401
except ModuleNotFoundError:
    # Fall back to relative imports (when run from backend directory)
    from db.database import Base
    from core.config import settings
    from db import models  # noqa: F401

# set the SQLAlchemy URL from our settings
config.set_main_option('sqlalchemy.url', f"sqlite:///{settings.database_path}")

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
