"""set_timezone_to_utc

Revision ID: 2ba7282de7d9
Revises: c4d5e6f7a8b9
Create Date: 2026-02-20 01:14:15.088425

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '2ba7282de7d9'
down_revision: str | None = 'c4d5e6f7a8b9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("SET timezone = 'UTC'")


def downgrade() -> None:
    pass
