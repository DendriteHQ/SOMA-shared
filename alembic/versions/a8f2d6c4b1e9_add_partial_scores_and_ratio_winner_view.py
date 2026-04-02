"""Add competition partial scores and per-compression-ratio winner view.

Revision ID: a8f2d6c4b1e9
Revises: f4e5d6c7b8a9
Create Date: 2026-04-02

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.definitions import MV_DEFINITIONS, VIEW_DEFINITIONS


revision = "a8f2d6c4b1e9"
down_revision = "f4e5d6c7b8a9"
branch_labels = None
depends_on = None


def _compile(selectable: sa.sql.Select) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)


def upgrade() -> None:
    # Drop materialized views first; they depend on regular views.
    for mv in reversed(MV_DEFINITIONS):
        op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))

    # Recreate all regular views from current definitions to apply structural changes.
    for view_def in reversed(VIEW_DEFINITIONS):
        op.execute(sa.text(f"DROP VIEW IF EXISTS {view_def.name} CASCADE"))
    for view_def in VIEW_DEFINITIONS:
        sql = _compile(view_def.selectable)
        op.execute(sa.text(f"CREATE OR REPLACE VIEW {view_def.name} AS {sql}"))

    # Recreate materialized views without initial data for faster migration.
    # They are populated by the app refresh task after deploy.
    for mv in MV_DEFINITIONS:
        sql = _compile(mv.selectable)
        op.execute(
            sa.text(
                f"CREATE MATERIALIZED VIEW IF NOT EXISTS {mv.name} AS {sql} WITH NO DATA"
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
