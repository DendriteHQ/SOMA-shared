"""Rebuild all regular and materialized views from current definitions.

Drops all materialized views (mv_*) and regular views (v_*) then recreates
them from the current Python view definitions.  This ensures the SQL baked
into each materialized view matches the current code after view-definition
changes that were not accompanied by a migration (e.g. eligible-miners filter
added to v_miner_competition_stats).

Revision ID: c1a2b3d4e5f6
Revises: f7b3c2a1d9e4
Create Date: 2026-04-08

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import MV_DEFINITIONS, VIEW_DEFINITIONS

revision = "c1a2b3d4e5f6"
down_revision = "f7b3c2a1d9e4"
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
    # Drop materialized views first — they depend on regular views.
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))

    # Drop and recreate all regular views so column/structural changes are applied.
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))
    for view_def in VIEW_DEFINITIONS:
        sql = _compile(view_def.selectable)
        op.execute(sa.text(f"CREATE VIEW {view_def.name} AS {sql}"))

    # Recreate materialized views with data populated immediately.
    for mv in MV_DEFINITIONS:
        sql = _compile(mv.selectable)
        op.execute(
            sa.text(
                f"CREATE MATERIALIZED VIEW {mv.name} AS {sql}"
            )
        )
        if mv.unique_index_columns:
            idx = f"{mv.name}_uidx"
            cols = ", ".join(mv.unique_index_columns)
            op.execute(
                sa.text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS {idx} ON {mv.name} ({cols})"
                )
            )


def downgrade() -> None:
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))
