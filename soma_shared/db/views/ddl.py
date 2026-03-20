from __future__ import annotations

import sqlalchemy as sa

from .definitions import MV_DEFINITIONS, VIEW_DEFINITIONS, ViewDefinition


def _import_sqlalchemy_views():
    try:
        from sqlalchemy_views import CreateView, DropView  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Missing optional dependency 'sqlalchemy-views'. "
            "Install it to create/drop SQL views (e.g. in alembic migrations)."
        ) from exc

    return CreateView, DropView


def build_create_view_ddls(
    *, or_replace: bool = True
) -> list[sa.schema.ExecutableDDLElement]:
    CreateView, _ = _import_sqlalchemy_views()

    ddls: list[sa.schema.ExecutableDDLElement] = []
    for view_def in VIEW_DEFINITIONS:
        ddls.append(CreateView(view_def.table, view_def.selectable, or_replace=or_replace))
    return ddls


def build_drop_view_ddls(
    *, if_exists: bool = True, cascade: bool = False
) -> list[sa.schema.ExecutableDDLElement]:
    _, DropView = _import_sqlalchemy_views()

    ddls: list[sa.schema.ExecutableDDLElement] = []
    for view_def in VIEW_DEFINITIONS:
        ddls.append(DropView(view_def.table, if_exists=if_exists, cascade=cascade))
    return ddls


def build_create_mv_ddls() -> list[sa.sql.expression.TextClause]:
    """Return raw SQL TextClauses that CREATE MATERIALIZED VIEW + unique index.

    Uses raw SQL because sqlalchemy_views does not support materialized views.
    The unique index is required for REFRESH MATERIALIZED VIEW CONCURRENTLY.
    """
    ddls: list[sa.sql.expression.TextClause] = []
    for mv in MV_DEFINITIONS:
        from sqlalchemy.dialects import postgresql

        sql = mv.selectable.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
        ddls.append(
            sa.text(
                f"CREATE MATERIALIZED VIEW IF NOT EXISTS {mv.name} AS {sql}"
            )
        )
        if mv.unique_index_columns:
            cols = ", ".join(mv.unique_index_columns)
            idx_name = f"{mv.name}_uidx"
            ddls.append(
                sa.text(
                    f"CREATE UNIQUE INDEX IF NOT EXISTS {idx_name} ON {mv.name} ({cols})"
                )
            )
    return ddls


def build_drop_mv_ddls(*, cascade: bool = False) -> list[sa.sql.expression.TextClause]:
    cascade_sql = " CASCADE" if cascade else ""
    return [
        sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name}{cascade_sql}")
        for mv in reversed(MV_DEFINITIONS)
    ]
