from __future__ import annotations

from dataclasses import dataclass

import sqlalchemy as sa


@dataclass(frozen=True, slots=True)
class ViewDefinition:
    name: str
    table: sa.Table
    selectable: sa.sql.Select


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
