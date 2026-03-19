"""Add view for ranked screener-qualified miners.

Revision ID: d2e4f6a8b0c1
Revises: c9b8e7a6d5f4
Create Date: 2026-03-19

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import VIEW_DEFINITIONS

# revision identifiers, used by Alembic.
revision = "d2e4f6a8b0c1"
down_revision = "c9b8e7a6d5f4"
branch_labels = None
depends_on = None


def _compile_view_select(selectable: sa.sql.Select) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)


def upgrade() -> None:
    for view_def in VIEW_DEFINITIONS:
        sql = _compile_view_select(view_def.selectable)
        op.execute(sa.text(f"CREATE OR REPLACE VIEW {view_def.name} AS {sql}"))


def downgrade() -> None:
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_screener_qualified"))
