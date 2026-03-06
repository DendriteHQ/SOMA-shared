"""Create SQL views for API queries.

Revision ID: f1c9a7b4d2e3
Revises: 8d4a6a71f2b1
Create Date: 2026-03-04

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import VIEW_DEFINITIONS

# revision identifiers, used by Alembic.
revision = "f1c9a7b4d2e3"
down_revision = "8d4a6a71f2b1"
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
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name}"))
