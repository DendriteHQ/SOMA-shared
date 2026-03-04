from __future__ import annotations

import sqlalchemy as sa

from .definitions import VIEW_DEFINITIONS, ViewDefinition


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
