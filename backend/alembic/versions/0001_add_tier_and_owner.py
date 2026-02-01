"""add tier to api_keys and owner to audio_jobs

Revision ID: 0001_add_tier_and_owner
Revises: 
Create Date: 2026-02-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0001_add_tier_and_owner'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Ensure api_keys table exists and tier column present
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='api_keys'"))
    if res.fetchone() is None:
        op.create_table(
            'api_keys',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('key', sa.String(128), unique=True, index=True, nullable=False),
            sa.Column('owner', sa.String(128), nullable=False),
            sa.Column('tier', sa.String(32), nullable=False, server_default='FREE'),
            sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('is_active', sa.Boolean, nullable=False, server_default='1'),
        )
    else:
        # add tier column if missing
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(api_keys)")).fetchall()]
        if 'tier' not in cols:
            op.add_column('api_keys', sa.Column('tier', sa.String(32), nullable=False, server_default='FREE'))

    # Ensure audio_jobs table exists and owner column present
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_jobs'"))
    if res.fetchone() is None:
        op.create_table(
            'audio_jobs',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('job_id', sa.String(36), unique=True, index=True, nullable=False),
            sa.Column('filename', sa.String(256), nullable=False),
            sa.Column('status', sa.String(50), nullable=False, index=True),
            sa.Column('owner', sa.String(128), nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
            sa.Column('updated_at', sa.DateTime, server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        )
    else:
        cols = [r[1] for r in conn.execute(text("PRAGMA table_info(audio_jobs)")).fetchall()]
        if 'owner' not in cols:
            op.add_column('audio_jobs', sa.Column('owner', sa.String(128), nullable=True))


def downgrade():
    conn = op.get_bind()

    # Drop owner column if exists
    cols = [r[1] for r in conn.execute(text("PRAGMA table_info(audio_jobs)")).fetchall()]
    if 'owner' in cols:
        op.drop_column('audio_jobs', 'owner')

    # Drop tier column if exists
    cols = [r[1] for r in conn.execute(text("PRAGMA table_info(api_keys)")).fetchall()]
    if 'tier' in cols:
        op.drop_column('api_keys', 'tier')
