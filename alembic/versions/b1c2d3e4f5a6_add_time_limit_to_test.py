"""add time_limit to test

Revision ID: b1c2d3e4f5a6
Revises: ca107b03ddf8
Create Date: 2026-01-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'ca107b03ddf8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('tests', sa.Column('time_limit', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('tests', 'time_limit')
