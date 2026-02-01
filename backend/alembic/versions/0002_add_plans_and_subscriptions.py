"""add plans and subscriptions

Revision ID: 0002_add_plans_and_subscriptions
Revises: 0001_add_tier_and_owner
Create Date: 2026-02-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0002_add_plans_and_subscriptions'
down_revision = '0001_add_tier_and_owner'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Create plans table if not exists
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='plans'"))
    if not res.fetchone():
        op.create_table(
            'plans',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('code', sa.String(32), unique=True, index=True, nullable=False),
            sa.Column('name', sa.String(128), nullable=False),
            sa.Column('price_monthly', sa.Numeric, nullable=True),
            sa.Column('price_yearly', sa.Numeric, nullable=True),
            sa.Column('features', sa.JSON, nullable=False),
            sa.Column('is_active', sa.Boolean, nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # Create subscriptions table if not exists
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'"))
    if not res.fetchone():
        op.create_table(
            'subscriptions',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('owner', sa.String(128), nullable=False, index=True),
            sa.Column('plan_code', sa.String(32), nullable=False, index=True),
            sa.Column('status', sa.String(32), nullable=False, server_default='active'),
            sa.Column('started_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
            sa.Column('ends_at', sa.DateTime, nullable=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # Seed default plans if missing
    def seed_plan(code, name, features):
        r = conn.execute(text("SELECT id FROM plans WHERE code = :code"), {'code': code})
        if not r.fetchone():
            conn.execute(
                text("INSERT INTO plans (code, name, features, is_active) VALUES (:code, :name, :features, 1)"),
                {
                    'code': code,
                    'name': name,
                    'features': sa.text("json(:features)") if False else features,
                },
            )

    # Note: For SQLite, pass JSON as Python literal via SQLAlchemy parameters
    free_features = {
        'can_download_audio': False,
        'can_export_stems': False,
        'max_job_duration_seconds': 30,
        'max_jobs_per_month': 10,
        'can_use_creator_voice': False,
        'can_change_vocal_tone': False,
        'can_use_advanced_beats': False,
    }
    creator_features = {
        'can_download_audio': True,
        'can_export_stems': True,
        'max_job_duration_seconds': 120,
        'max_jobs_per_month': 500,
        'can_use_creator_voice': True,
        'can_change_vocal_tone': True,
        'can_use_advanced_beats': True,
    }
    pro_features = {
        'can_download_audio': True,
        'can_export_stems': True,
        'max_job_duration_seconds': 600,
        'max_jobs_per_month': 5000,
        'can_use_creator_voice': True,
        'can_change_vocal_tone': True,
        'can_use_advanced_beats': True,
    }

    # Insert seed plans if not present
    import json

    for code, name, features in [
        ('FREE', 'Free', free_features),
        ('CREATOR', 'Creator', creator_features),
        ('PRO', 'Pro', pro_features),
    ]:
        r = conn.execute(text("SELECT id FROM plans WHERE code = :code"), {'code': code})
        if not r.fetchone():
            conn.execute(text("INSERT INTO plans (code, name, features, is_active) VALUES (:code, :name, :features, 1)"), {'code': code, 'name': name, 'features': json.dumps(features)})


def downgrade():
    conn = op.get_bind()

    # Drop subscriptions table if exists
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'"))
    if res.fetchone():
        op.drop_table('subscriptions')

    # Drop plans table if exists
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='plans'"))
    if res.fetchone():
        op.drop_table('plans')
