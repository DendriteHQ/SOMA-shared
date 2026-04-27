from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncConnection

from .definitions import MV_DEFINITIONS, VIEW_DEFINITIONS


def _compile_view_select(selectable: sa.sql.Select) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)


async def create_or_replace_views(conn: AsyncConnection) -> None:
    for view_def in VIEW_DEFINITIONS:
        sql = _compile_view_select(view_def.selectable)
        await conn.execute(sa.text(f"CREATE OR REPLACE VIEW {view_def.name} AS {sql}"))


async def create_materialized_views(conn: AsyncConnection) -> None:
    """Create all materialized views and their unique indexes (IF NOT EXISTS)."""
    for mv in MV_DEFINITIONS:
        sql = _compile_view_select(mv.selectable)
        await conn.execute(
            sa.text(f"CREATE MATERIALIZED VIEW IF NOT EXISTS {mv.name} AS {sql}")
        )
        if mv.unique_index_columns:
            cols = ", ".join(mv.unique_index_columns)
            idx = f"{mv.name}_uidx"
            await conn.execute(
                sa.text(f"CREATE UNIQUE INDEX IF NOT EXISTS {idx} ON {mv.name} ({cols})")
            )


async def refresh_materialized_views(conn: AsyncConnection) -> None:
    """Refresh all materialized views concurrently (no table lock).

    Requires the unique index created by create_materialized_views.
    Safe to call from a background task while the app is serving traffic.
    """
    if conn.in_transaction():
        raise RuntimeError(
            "refresh_materialized_views() requires a fresh connection outside a transaction; "
            "REFRESH MATERIALIZED VIEW CONCURRENTLY cannot run after autobegin or inside begin()"
        )

    autocommit_conn = await conn.execution_options(isolation_level="AUTOCOMMIT")
    for mv in MV_DEFINITIONS:
        await autocommit_conn.execute(
            sa.text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv.name}")
        )
