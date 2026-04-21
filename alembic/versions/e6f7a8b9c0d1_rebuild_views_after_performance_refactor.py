"""Rebuild views and materialized views after performance refactor.

Refreshes all regular and materialized views from the current Python
definitions so the database picks up anti-fanout and EXISTS-based query
shape improvements introduced in the view layer.

Revision ID: e6f7a8b9c0d1
Revises: d4e6f8a1b2c3
Create Date: 2026-04-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import MV_DEFINITIONS, VIEW_DEFINITIONS


revision = "e6f7a8b9c0d1"
down_revision = "d4e6f8a1b2c3"
branch_labels = None
depends_on = None


def _compile(selectable: sa.sql.Select) -> str:
    return str(
        selectable.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def _rebuild_views() -> None:
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))

    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))

    for view_def in VIEW_DEFINITIONS:
        sql = _compile(view_def.selectable)
        op.execute(sa.text(f"CREATE VIEW {view_def.name} AS {sql}"))

    for mv in MV_DEFINITIONS:
        sql = _compile(mv.selectable)
        op.execute(sa.text(f"CREATE MATERIALIZED VIEW {mv.name} AS {sql}"))
        if mv.unique_index_columns:
            idx = f"{mv.name}_uidx"
            cols = ", ".join(mv.unique_index_columns)
            op.execute(
                sa.text(f"CREATE UNIQUE INDEX IF NOT EXISTS {idx} ON {mv.name} ({cols})")
            )


def upgrade() -> None:
    _rebuild_views()


def downgrade() -> None:
    _rebuild_views()