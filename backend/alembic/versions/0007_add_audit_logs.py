"""add audit logs

Revision ID: 0007_add_audit_logs
Revises: 0006_add_stripe_billing
Create Date: 2026-02-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0007_add_audit_logs'
down_revision = '0006_add_stripe_billing'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"))
    if not res.fetchone():
        op.create_table(
            'audit_logs',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('user_id', sa.Integer, nullable=True, index=True),
            sa.Column('project_id', sa.Integer, nullable=True, index=True),
            sa.Column('resource_type', sa.String(64), nullable=False, index=True),
            sa.Column('resource_id', sa.Integer, nullable=True, index=True),
            sa.Column('event_type', sa.String(32), nullable=False, index=True),
            sa.Column('action', sa.String(32), nullable=False, index=True),
            sa.Column('details', sa.JSON, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    conn = op.get_bind()
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='audit_logs'"))
    if res.fetchone():
        op.drop_table('audit_logs')
