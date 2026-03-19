from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.competition_config import CompetitionConfig
from soma_shared.db.models.compression_competition_config import (
    CompressionCompetitionConfig,
)
from soma_shared.db.models.miner_upload import MinerUpload
from soma_shared.db.models.screening_challenge import ScreeningChallenge
from soma_shared.db.models.screener import Screener
from soma_shared.db.models.script import Script

from .base import ViewDefinition, view_table
from .v_miner_screener_stats import v_miner_screener_stats


def v_miner_screener_qualified() -> ViewDefinition:
    stats = v_miner_screener_stats().selectable.subquery("miner_screener_stats")
    configs = CompetitionConfig.__table__
    compression_configs = CompressionCompetitionConfig.__table__
    screeners = Screener.__table__
    screening = ScreeningChallenge.__table__
    uploads = MinerUpload.__table__
    scripts = Script.__table__

    screener_counts = (
        sa.select(
            screeners.c.competition_fk.label("competition_id"),
            sa.func.count(sa.distinct(screening.c.challenge_fk)).label(
                "screener_challenge_count"
            ),
        )
        .select_from(screeners.join(screening, screening.c.screener_fk == screeners.c.id))
        .where(screeners.c.is_active.is_(True))
        .group_by(screeners.c.competition_fk)
        .subquery()
    )

    ratio_counts = (
        sa.select(
            configs.c.competition_fk.label("competition_id"),
            sa.func.coalesce(
                sa.func.json_array_length(compression_configs.c.compression_ratios),
                sa.literal(1),
            ).label("ratio_count"),
        )
        .select_from(
            configs.outerjoin(
                compression_configs,
                compression_configs.c.competition_config_fk == configs.c.id,
            )
        )
        .subquery()
    )

    required_pairs = (
        sa.select(
            screener_counts.c.competition_id.label("competition_id"),
            (
                screener_counts.c.screener_challenge_count * ratio_counts.c.ratio_count
            ).label("screener_required"),
        )
        .select_from(
            screener_counts.join(
                ratio_counts,
                ratio_counts.c.competition_id == screener_counts.c.competition_id,
            )
        )
        .subquery()
    )

    miner_scripts_ranked = (
        sa.select(
            uploads.c.competition_fk.label("competition_id"),
            scripts.c.miner_fk.label("miner_id"),
            uploads.c.script_fk.label("script_id"),
            sa.func.row_number()
            .over(
                partition_by=(uploads.c.competition_fk, scripts.c.miner_fk),
                order_by=(uploads.c.created_at.asc(), uploads.c.script_fk.asc()),
            )
            .label("_rn"),
        )
        .select_from(uploads.join(scripts, scripts.c.id == uploads.c.script_fk))
        .where(uploads.c.competition_fk.is_not(None))
        .subquery()
    )

    miner_scripts = (
        sa.select(
            miner_scripts_ranked.c.competition_id,
            miner_scripts_ranked.c.miner_id,
            miner_scripts_ranked.c.script_id,
        )
        .where(miner_scripts_ranked.c._rn == 1)
        .subquery()
    )

    eligible = (
        sa.select(
            stats.c.competition_id.label("competition_id"),
            stats.c.miner_id.label("miner_id"),
            miner_scripts.c.script_id.label("script_id"),
            stats.c.avg_score.label("avg_score"),
            stats.c.first_upload_at.label("first_upload_at"),
            stats.c.screener_scored.label("screener_scored"),
            required_pairs.c.screener_required.label("screener_required"),
        )
        .select_from(
            stats.join(
                required_pairs,
                required_pairs.c.competition_id == stats.c.competition_id,
            ).join(
                miner_scripts,
                sa.and_(
                    miner_scripts.c.competition_id == stats.c.competition_id,
                    miner_scripts.c.miner_id == stats.c.miner_id,
                ),
            )
        )
        .where(required_pairs.c.screener_required > 0)
        .where(stats.c.screener_scored >= required_pairs.c.screener_required)
        .subquery()
    )

    selectable = sa.select(
        eligible.c.competition_id,
        eligible.c.miner_id,
        eligible.c.script_id,
        eligible.c.avg_score,
        eligible.c.first_upload_at,
        eligible.c.screener_scored,
        eligible.c.screener_required,
        sa.func.row_number()
        .over(
            partition_by=eligible.c.competition_id,
            order_by=(
                eligible.c.avg_score.desc().nullslast(),
                eligible.c.first_upload_at.asc().nullsfirst(),
                eligible.c.miner_id.asc(),
            ),
        )
        .label("rank"),
        sa.func.count(sa.literal(1))
        .over(partition_by=eligible.c.competition_id)
        .label("total_eligible"),
    )

    table = view_table("v_miner_screener_qualified")
    return ViewDefinition(name=table.name, table=table, selectable=selectable)
