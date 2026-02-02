"""add stripe billing fields

Revision ID: 0006_add_stripe_billing
Revises: 0005_add_audio_transform
Create Date: 2026-02-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0006_add_stripe_billing'
down_revision = '0005_add_audio_transform'
branch_labels = None
depends_on = None


def _column_exists(conn, table: str, column: str) -> bool:
    res = conn.execute(text(f"PRAGMA table_info({table})"))
    cols = [r[1] for r in res.fetchall()]
    return column in cols


def upgrade():
    conn = op.get_bind()

    # plans: add updated_at if missing
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='plans'"))
    if res.fetchone():
        if not _column_exists(conn, 'plans', 'updated_at'):
            op.add_column('plans', sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False))

    # subscriptions: add Stripe fields + user linkage
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='subscriptions'"))
    if res.fetchone():
        if not _column_exists(conn, 'subscriptions', 'user_id'):
            op.add_column('subscriptions', sa.Column('user_id', sa.Integer, nullable=True, index=True))
        if not _column_exists(conn, 'subscriptions', 'stripe_customer_id'):
            op.add_column('subscriptions', sa.Column('stripe_customer_id', sa.String(128), nullable=True, index=True))
        if not _column_exists(conn, 'subscriptions', 'stripe_subscription_id'):
            op.add_column('subscriptions', sa.Column('stripe_subscription_id', sa.String(128), nullable=True, index=True))
        if not _column_exists(conn, 'subscriptions', 'plan_id'):
            op.add_column('subscriptions', sa.Column('plan_id', sa.Integer, nullable=True, index=True))
        if not _column_exists(conn, 'subscriptions', 'current_period_end'):
            op.add_column('subscriptions', sa.Column('current_period_end', sa.DateTime, nullable=True))
        if not _column_exists(conn, 'subscriptions', 'updated_at'):
            op.add_column('subscriptions', sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), nullable=False))

    # stripe_events table
    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='stripe_events'"))
    if not res.fetchone():
        op.create_table(
            'stripe_events',
            sa.Column('id', sa.Integer, primary_key=True),
            sa.Column('event_id', sa.String(128), unique=True, index=True, nullable=False),
            sa.Column('event_type', sa.String(128), nullable=False, index=True),
            sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        )

    # Ensure max_projects_total exists in plan features
    try:
        res = conn.execute(text("SELECT id, code, features FROM plans"))
        rows = res.fetchall()
        import json

        for row in rows:
            plan_id, code, features = row[0], row[1], row[2]
            try:
                data = json.loads(features) if isinstance(features, str) else (features or {})
            except Exception:
                data = {}
            if 'max_projects_total' not in data:
                if code == 'FREE':
                    data['max_projects_total'] = 2
                else:
                    data['max_projects_total'] = None
                conn.execute(
                    text("UPDATE plans SET features = :features WHERE id = :id"),
                    {"features": json.dumps(data), "id": plan_id},
                )
    except Exception:
        pass


def downgrade():
    conn = op.get_bind()

    res = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='stripe_events'"))
    if res.fetchone():
        op.drop_table('stripe_events')

    # No safe downgrade for added columns in SQLite without table rebuild.
