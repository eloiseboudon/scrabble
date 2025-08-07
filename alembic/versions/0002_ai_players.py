"""add ai fields and player limit

Revision ID: 0002_ai_players
Revises: 0001_initial
Create Date: 2024-01-01 00:01:00
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_ai_players"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "games",
        sa.Column("max_players", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "games",
        sa.Column("vs_computer", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "game_players",
        sa.Column("is_computer", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("game_players", "user_id", existing_type=sa.Integer(), nullable=True)
    op.create_check_constraint(
        "ck_max_players", "games", "max_players >= 2 AND max_players <= 4"
    )
    op.alter_column("games", "max_players", server_default=None)
    op.alter_column("games", "vs_computer", server_default=None)
    op.alter_column("game_players", "is_computer", server_default=None)


def downgrade() -> None:
    op.alter_column("game_players", "user_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("game_players", "is_computer")
    op.drop_constraint("ck_max_players", "games", type_="check")
    op.drop_column("games", "vs_computer")
    op.drop_column("games", "max_players")

