"""Fix screener_challenges to use total competition-level count.

The v_miner_status view previously set screener_challenges = screener_assigned
(per-miner), which made the condition (scored + pending) < screener_challenges
trivially always false (scored + pending == screener_assigned == screener_challenges).

Now screener_challenges = total distinct screener challenge IDs per competition,
mirroring how competition_challenges is the total non-screener challenge count.

Revision ID: f4e5d6c7b8a9
Revises: e3f4a5b6c7d8
Create Date: 2026-04-02
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_miner_status import v_miner_status


# revision identifiers, used by Alembic.
revision: str = "f4e5d6c7b8a9"
down_revision: Union[str, Sequence[str], None] = "cb3f6f9d97c0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _compile(selectable: sa.sql.Select) -> str:
    return str(
        selectable.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def _drop_miner_status_views() -> None:
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_miner_status CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS v_miner_status CASCADE"))


def _create_v_miner_status() -> None:
    sql = _compile(v_miner_status().selectable)
    op.execute(sa.text(f"CREATE VIEW v_miner_status AS {sql}"))


def _create_mv_miner_status() -> None:
    sql = _compile(v_miner_status(materialized=True).selectable)
    op.execute(sa.text(f"CREATE MATERIALIZED VIEW mv_miner_status AS {sql}"))
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS mv_miner_status_uidx "
            "ON mv_miner_status (competition_id, ss58)"
        )
    )


def upgrade() -> None:
    _drop_miner_status_views()
    _create_v_miner_status()
    _create_mv_miner_status()


def downgrade() -> None:
    # Re-create with the old (broken) definition by reverting to the previous
    # migration's view — not easily reproducible here, so we just recreate
    # with the current (fixed) definition as a safe fallback.
    _drop_miner_status_views()
    _create_v_miner_status()
    _create_mv_miner_status()
