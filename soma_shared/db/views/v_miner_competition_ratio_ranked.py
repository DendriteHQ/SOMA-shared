from __future__ import annotations

import sqlalchemy as sa

from .base import ViewDefinition, view_table
from .v_miner_competition_stats import competition_ratio_stats_subquery


def v_miner_competition_ratio_ranked() -> ViewDefinition:
    ratio_stats = competition_ratio_stats_subquery()

    selectable = sa.select(
        ratio_stats.c.competition_id,
        ratio_stats.c.compression_ratio,
        ratio_stats.c.ss58,
        ratio_stats.c.is_banned,
        ratio_stats.c.ratio_score,
        ratio_stats.c.first_upload_at,
        sa.func.row_number()
        .over(
            partition_by=(
                ratio_stats.c.competition_id,
                ratio_stats.c.compression_ratio,
            ),
            order_by=(
                ratio_stats.c.ratio_score.desc().nullslast(),
                ratio_stats.c.first_upload_at.asc().nullsfirst(),
                ratio_stats.c.ss58.asc(),
            ),
        )
        .label("rank"),
    ).where(ratio_stats.c.scored_count > 0)

    table = view_table("v_miner_competition_ratio_ranked")
    return ViewDefinition(name=table.name, table=table, selectable=selectable)
