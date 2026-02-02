"""add users, email verifications, and projects

Revision ID: 0003_add_users_projects_auth
Revises: 0002_add_plans_and_subscriptions
Create Date: 2026-02-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0003_add_users_projects_auth'
down_revision = '0002_add_plans_and_subscriptions'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # users table
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
    if not res.fetchone():
        op.create_table(
            'users',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
            sa.Column('password_hash', sa.String(255), nullable=False),
            sa.Column('is_verified', sa.Boolean, nullable=False, server_default=sa.text('0')),
            sa.Column('tier', sa.String(32), nullable=False, server_default='FREE'),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # email_verifications table
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='email_verifications'"))
    if not res.fetchone():
        op.create_table(
            'email_verifications',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('user_id', sa.Integer, nullable=False, index=True),
            sa.Column('code_hash', sa.String(128), nullable=False),
            sa.Column('expires_at', sa.DateTime, nullable=False, index=True),
            sa.Column('used_at', sa.DateTime, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # projects table
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"))
    if not res.fetchone():
        op.create_table(
            'projects',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('user_id', sa.Integer, nullable=False, index=True),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('meta', sa.JSON, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    conn = op.get_bind()

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"))
    if res.fetchone():
        op.drop_table('projects')

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='email_verifications'"))
    if res.fetchone():
        op.drop_table('email_verifications')

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'"))
    if res.fetchone():
        op.drop_table('users')
