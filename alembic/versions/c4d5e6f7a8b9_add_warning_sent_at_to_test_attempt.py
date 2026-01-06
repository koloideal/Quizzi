"""add warning_sent_at to test_attempt

Revision ID: c4d5e6f7a8b9
Revises: b1c2d3e4f5a6
Create Date: 2026-01-06

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'c4d5e6f7a8b9'
down_revision: str | None = 'b1c2d3e4f5a6'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('test_attempts', sa.Column('warning_sent_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('test_attempts', 'warning_sent_at')
