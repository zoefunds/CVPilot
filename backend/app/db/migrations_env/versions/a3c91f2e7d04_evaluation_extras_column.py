"""evaluation: add extras JSON column for extended contract analyses

Revision ID: a3c91f2e7d04
Revises: 1851cfcda4db
Create Date: 2026-06-17 00:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a3c91f2e7d04"
down_revision: str | None = "1851cfcda4db"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("evaluations", sa.Column("extras", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("evaluations", "extras")
