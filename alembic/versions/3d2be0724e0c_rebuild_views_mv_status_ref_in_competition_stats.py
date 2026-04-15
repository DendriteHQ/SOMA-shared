"""Rebuild views: mv_miner_competition_stats reads from mv_miner_status.

Instead of inlining the full v_miner_status subquery, v_miner_competition_stats
now references mv_miner_status (materialized) / v_miner_status (live) by name.
MV refresh order in MV_DEFINITIONS was also fixed so mv_miner_status is
always refreshed before mv_miner_competition_stats.

Revision ID: 3d2be0724e0c
Revises: c1a2b3d4e5f6
Create Date: 2026-04-15

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import MV_DEFINITIONS, VIEW_DEFINITIONS

revision = "3d2be0724e0c"
down_revision = "c1a2b3d4e5f6"
branch_labels = None
depends_on = None


def _compile(selectable: sa.sql.Select) -> str:
    return str(
        selectable.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def upgrade() -> None:
    # Drop materialized views first (depend on regular views).
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))

    # Recreate regular views.
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))
    for view_def in VIEW_DEFINITIONS:
        sql = _compile(view_def.selectable)
        op.execute(sa.text(f"CREATE VIEW {view_def.name} AS {sql}"))

    # Recreate materialized views with data (respects new MV_DEFINITIONS order).
    for mv in MV_DEFINITIONS:
        sql = _compile(mv.selectable)
        op.execute(sa.text(f"CREATE MATERIALIZED VIEW {mv.name} AS {sql}"))
        if mv.unique_index_columns:
            idx = f"{mv.name}_uidx"
            cols = ", ".join(mv.unique_index_columns)
            op.execute(sa.text(f"CREATE UNIQUE INDEX IF NOT EXISTS {idx} ON {mv.name} ({cols})"))


def downgrade() -> None:
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))
