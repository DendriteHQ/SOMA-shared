"""merge heads ab12cd34ef56 c7d8e9f0a1b2

Revision ID: 799b43ffe9be
Revises: ab12cd34ef56, c7d8e9f0a1b2
Create Date: 2026-06-12 09:50:57.934779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '799b43ffe9be'
down_revision: Union[str, Sequence[str], None] = ('ab12cd34ef56', 'c7d8e9f0a1b2')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
