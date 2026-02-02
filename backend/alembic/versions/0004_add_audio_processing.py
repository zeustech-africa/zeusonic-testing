"""add audio tracks and processing tables

Revision ID: 0004_add_audio_processing
Revises: 0003_add_users_projects_auth
Create Date: 2026-02-02 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = '0004_add_audio_processing'
down_revision = '0003_add_users_projects_auth'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # audio_tracks table
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_tracks'"))
    if not res.fetchone():
        op.create_table(
            'audio_tracks',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('project_id', sa.Integer, nullable=False, index=True),
            sa.Column('user_id', sa.Integer, nullable=False, index=True),
            sa.Column('filename', sa.String(256), nullable=False),
            sa.Column('original_filename', sa.String(256), nullable=False),
            sa.Column('file_size', sa.Integer, nullable=False),
            sa.Column('duration_seconds', sa.Float, nullable=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='uploaded', index=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # audio_analysis table
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_analysis'"))
    if not res.fetchone():
        op.create_table(
            'audio_analysis',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('track_id', sa.Integer, nullable=False, index=True, unique=True),
            sa.Column('bpm', sa.Float, nullable=True),
            sa.Column('musical_key', sa.String(8), nullable=True),
            sa.Column('duration_seconds', sa.Float, nullable=False),
            sa.Column('loudness_lufs', sa.Float, nullable=True),
            sa.Column('sample_rate', sa.Integer, nullable=True),
            sa.Column('channels', sa.Integer, nullable=True),
            sa.Column('bit_depth', sa.Integer, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # audio_processing table
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_processing'"))
    if not res.fetchone():
        op.create_table(
            'audio_processing',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('track_id', sa.Integer, nullable=False, index=True),
            sa.Column('process_type', sa.String(32), nullable=False, index=True),
            sa.Column('output_filename', sa.String(256), nullable=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='pending', index=True),
            sa.Column('error_message', sa.Text, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column('completed_at', sa.DateTime, nullable=True),
        )


def downgrade():
    conn = op.get_bind()

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_processing'"))
    if res.fetchone():
        op.drop_table('audio_processing')

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_analysis'"))
    if res.fetchone():
        op.drop_table('audio_analysis')

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audio_tracks'"))
    if res.fetchone():
        op.drop_table('audio_tracks')
