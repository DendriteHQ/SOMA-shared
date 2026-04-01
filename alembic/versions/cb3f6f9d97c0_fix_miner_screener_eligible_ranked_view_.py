"""fix_miner_screener_eligible_ranked_view_structure

Revision ID: cb3f6f9d97c0
Revises: f2a3b4c5d6e7
Create Date: 2026-04-01 14:13:23.850616

Fix the view structure issue where PostgreSQL doesn't allow CREATE OR REPLACE
when changing column names/order. Drop and recreate the view instead.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import VIEW_DEFINITIONS


# revision identifiers, used by Alembic.
revision: str = 'cb3f6f9d97c0'
down_revision: Union[str, Sequence[str], None] = 'f2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _compile_view_select(selectable: sa.sql.Select) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)


def upgrade() -> None:
    """Upgrade schema - fix v_miner_screener_eligible_ranked view structure."""
    # Find and recreate only the problematic view
    for view_def in VIEW_DEFINITIONS:
        if view_def.name == "v_miner_screener_eligible_ranked":
            # Drop the view first to allow structural changes
            op.execute(sa.text("DROP VIEW IF EXISTS v_miner_screener_eligible_ranked CASCADE"))
            sql = _compile_view_select(view_def.selectable)
            op.execute(sa.text(f"CREATE VIEW {view_def.name} AS {sql}"))
            break


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_screener_eligible_ranked CASCADE"))
