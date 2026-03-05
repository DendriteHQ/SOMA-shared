from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncConnection

from .definitions import VIEW_DEFINITIONS


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
