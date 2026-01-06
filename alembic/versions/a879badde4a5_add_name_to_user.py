"""add_name_to_user

Revision ID: a879badde4a5
Revises: 520eccd2e55f
Create Date: 2026-01-02 21:21:22.159248

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'a879badde4a5'
down_revision: str | None = '520eccd2e55f'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('name', sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'name')
