"""Enable required PostgreSQL extensions.

Revision ID: 0001
Revises: None
Create Date: 2026-08-21
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Enable extensions required by the normative database specification."""
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')
    op.execute('CREATE EXTENSION IF NOT EXISTS "citext"')


def downgrade() -> None:
    """Preserve shared extensions during downgrade to avoid destructive side effects."""
