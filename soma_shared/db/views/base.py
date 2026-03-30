from __future__ import annotations

from dataclasses import dataclass, field

import sqlalchemy as sa


@dataclass(frozen=True, slots=True)
class ViewDefinition:
    name: str
    table: sa.Table
    selectable: sa.sql.Select
    # When True, this view should be created as a MATERIALIZED VIEW.
    # unique_index_columns is required for REFRESH CONCURRENTLY support.
    materialized: bool = False
    unique_index_columns: tuple[str, ...] = field(default_factory=tuple)


_VIEW_METADATA = sa.MetaData()


def view_table(name: str) -> sa.Table:
    return sa.Table(name, _VIEW_METADATA)


def as_float(expr: sa.ColumnElement) -> sa.ColumnElement:
    return sa.cast(expr, sa.Float)


def weight(expr_compression_ratio: sa.ColumnElement) -> sa.ColumnElement:
    return sa.literal(1.0) / sa.func.sqrt(as_float(expr_compression_ratio))


def weighted_score(expr_score: sa.ColumnElement, expr_compression_ratio: sa.ColumnElement) -> sa.ColumnElement:
    return as_float(expr_score) / sa.func.sqrt(as_float(expr_compression_ratio))


def weighted_avg(expr_score: sa.ColumnElement, expr_compression_ratio: sa.ColumnElement) -> sa.ColumnElement:
    numerator = sa.func.sum(weighted_score(expr_score, expr_compression_ratio))
    denominator = sa.func.sum(weight(expr_compression_ratio))
    return numerator / sa.func.nullif(denominator, 0)
