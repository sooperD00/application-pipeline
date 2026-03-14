"""add failed to tailoringstatus

Revision ID: 6bc0f4c28a4a
Revises: b30f639f830c
Create Date: 2026-03-14 09:47:17.285652

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6bc0f4c28a4a'
down_revision: Union[str, Sequence[str], None] = 'b30f639f830c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tailoringstatus ADD VALUE IF NOT EXISTS 'failed'")
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
