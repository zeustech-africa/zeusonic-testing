"""add audio stems and beat transform jobs

Revision ID: 0005_add_audio_transform
Revises: 0004_add_audio_processing
Create Date: 2026-02-02
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0005_add_audio_transform'
down_revision = '0004_add_audio_processing'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_stems (
            id INTEGER NOT NULL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            source_track_id INTEGER NOT NULL,
            stem_type VARCHAR(32) NOT NULL,
            file_path VARCHAR(512) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_audio_stems_project_id ON audio_stems (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audio_stems_source_track_id ON audio_stems (source_track_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audio_stems_stem_type ON audio_stems (stem_type)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS beat_transform_jobs (
            id INTEGER NOT NULL PRIMARY KEY,
            track_id INTEGER NOT NULL,
            source_style VARCHAR(64) NOT NULL DEFAULT 'unknown',
            target_style VARCHAR(64) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            output_path VARCHAR(512),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
            completed_at DATETIME
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_beat_transform_jobs_track_id ON beat_transform_jobs (track_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_beat_transform_jobs_target_style ON beat_transform_jobs (target_style)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_beat_transform_jobs_status ON beat_transform_jobs (status)")


def downgrade() -> None:
    op.drop_table('beat_transform_jobs')
    op.drop_table('audio_stems')
