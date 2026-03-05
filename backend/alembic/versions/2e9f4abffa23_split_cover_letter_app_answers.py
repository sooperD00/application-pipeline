"""split cover_letter_app_answers

Revision ID: 2e9f4abffa23
Revises: f11a4c601796
Create Date: 2026-03-05 14:22:32.556058

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2e9f4abffa23'
down_revision: Union[str, Sequence[str], None] = 'f11a4c601796'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE promptphase ADD VALUE IF NOT EXISTS 'cover_letter'")
    op.execute("ALTER TYPE promptphase ADD VALUE IF NOT EXISTS 'app_answers'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
