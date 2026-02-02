"""add OTP fields to users table

Revision ID: 0008_add_otp_fields
Revises: 0007_add_audit_logs
Create Date: 2026-02-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = '0008_add_otp_fields'
down_revision = '0007_add_audit_logs'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    
    # Check if columns already exist
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'otp_hash' not in columns:
        op.add_column('users', sa.Column('otp_hash', sa.String(255), nullable=True))
    
    if 'otp_expires_at' not in columns:
        op.add_column('users', sa.Column('otp_expires_at', sa.DateTime, nullable=True, index=True))


def downgrade():
    conn = op.get_bind()
    
    # Check if columns exist before dropping
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'otp_hash' in columns:
        op.drop_column('users', 'otp_hash')
    
    if 'otp_expires_at' in columns:
        op.drop_column('users', 'otp_expires_at')
