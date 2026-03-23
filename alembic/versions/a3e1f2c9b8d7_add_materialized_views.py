"""Add materialized views for frontend (mv_*) and update regular views (v_*).

Revision ID: a3e1f2c9b8d7
Revises: f1c9a7b4d2e3
Create Date: 2026-03-20

Regular views (v_*) are recreated to apply schema changes made since the last
migration. Materialized views (mv_*) are created as snapshots of the heavy
regular views; they are refreshed periodically by the application background
task rather than on every request.
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import MV_DEFINITIONS, VIEW_DEFINITIONS

revision = "a3e1f2c9b8d7"
down_revision = "d2e4f6a8b0c1"
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
    # 1. Drop existing materialized views first (they may depend on regular views).
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))

    # 2. Drop legacy views that have been removed from VIEW_DEFINITIONS.
    _LEGACY_VIEWS = [
        "v_miner_competition_rank",
        "v_screener_challenges_active",
    ]
    for name in _LEGACY_VIEWS:
        op.execute(sa.text(f"DROP VIEW IF EXISTS {name} CASCADE"))

    # 3. Recreate regular views — drop first so column renames are allowed,
    #    then recreate. MVs are already dropped above so no dependents remain.
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))
    for view_def in VIEW_DEFINITIONS:
        sql = _compile(view_def.selectable)
        op.execute(sa.text(f"CREATE OR REPLACE VIEW {view_def.name} AS {sql}"))

    # 3. Create materialized views + unique indexes.
    for mv in MV_DEFINITIONS:
        sql = _compile(mv.selectable)
        op.execute(
            sa.text(f"CREATE MATERIALIZED VIEW IF NOT EXISTS {mv.name} AS {sql}")
        )
        if mv.unique_index_columns:
            cols = ", ".join(mv.unique_index_columns)
            idx = f"{mv.name}_uidx"
            op.execute(
                sa.text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS {idx} ON {mv.name} ({cols})"
                )
            )


def downgrade() -> None:
    # Drop materialized views.
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))

    # Restore previous regular view definitions by re-running the prior migration's
    # upgrade logic is not feasible here, so we just drop the views that were
    # added or changed in this migration. The previous migration (f1c9a7b4d2e3)
    # will restore them if the full downgrade chain is executed.
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))
