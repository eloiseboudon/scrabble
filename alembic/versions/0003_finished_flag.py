"""add finished flag to games

Revision ID: 0003_finished_flag
Revises: 0002_ai_players
Create Date: 2024-01-01 00:02:00
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_finished_flag"
down_revision = "0002_ai_players"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("finished", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("games", "finished", server_default=None)


def downgrade() -> None:
    op.drop_column("games", "finished")
