"""Add precomputed miner status column to miner status views.

Revision ID: e3f4a5b6c7d8
Revises: b7c8d9e0f1a2
Create Date: 2026-03-31
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_miner_status import v_miner_status


# revision identifiers, used by Alembic.
revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "b7c8d9e0f1a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_LEGACY_COLUMNS: tuple[str, ...] = (
    "competition_id",
    "ss58",
    "is_banned",
    "has_script",
    "competition_challenges",
    "screener_challenges",
    "scored_screened_challenges",
    "pending_assignments_screener",
    "scored_competition_challenges",
    "pending_assignments_competition",
    "screener_rank",
    "total_eligible_screener",
    "last_submit_at",
)


def _compile(selectable: sa.sql.Select) -> str:
    return str(
        selectable.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def _legacy_v_miner_status_selectable(*, materialized: bool) -> sa.sql.Select:
    current = v_miner_status(materialized=materialized).selectable.subquery(
        "v_miner_status_current"
    )
    return sa.select(
        *(getattr(current.c, col_name).label(col_name) for col_name in _LEGACY_COLUMNS)
    )


def _create_v_miner_status(*, include_status: bool) -> None:
    selectable = (
        v_miner_status().selectable
        if include_status
        else _legacy_v_miner_status_selectable(materialized=False)
    )
    sql = _compile(selectable)
    op.execute(sa.text(f"CREATE VIEW v_miner_status AS {sql}"))


def _create_mv_miner_status(*, include_status: bool) -> None:
    selectable = (
        v_miner_status(materialized=True).selectable
        if include_status
        else _legacy_v_miner_status_selectable(materialized=True)
    )
    sql = _compile(selectable)
    op.execute(sa.text(f"CREATE MATERIALIZED VIEW mv_miner_status AS {sql}"))
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS mv_miner_status_uidx "
            "ON mv_miner_status (competition_id, ss58)"
        )
    )


def _drop_miner_status_views() -> None:
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_miner_status CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_status CASCADE"))


def upgrade() -> None:
    _drop_miner_status_views()
    _create_v_miner_status(include_status=True)
    _create_mv_miner_status(include_status=True)


def downgrade() -> None:
    _drop_miner_status_views()
    _create_v_miner_status(include_status=False)
    _create_mv_miner_status(include_status=False)
