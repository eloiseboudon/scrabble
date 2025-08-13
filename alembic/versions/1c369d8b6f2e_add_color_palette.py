"""add color palette to users

Revision ID: 1c369d8b6f2e
Revises: f249aee58340
Create Date: 2025-09-01 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1c369d8b6f2e'
down_revision = 'f249aee58340'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('color_palette', sa.String(length=20), nullable=False, server_default='palette1'))


def downgrade() -> None:
    op.drop_column('users', 'color_palette')
