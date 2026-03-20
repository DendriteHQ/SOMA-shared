from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.competition import Competition
from soma_shared.db.models.competition_config import CompetitionConfig
from soma_shared.db.models.competition_timeframe import CompetitionTimeframe
from soma_shared.db.models.compression_competition_config import CompressionCompetitionConfig

from .base import ViewDefinition, view_table


def v_active_competition() -> ViewDefinition:
    competitions = Competition.__table__
    configs = CompetitionConfig.__table__
    timeframes = CompetitionTimeframe.__table__
    comp_ratios = CompressionCompetitionConfig.__table__

    selectable = (
        sa.select(
            competitions.c.id.label("competition_id"),
            competitions.c.competition_name.label("competition_name"),
            competitions.c.created_at.label("competition_created_at"),
            comp_ratios.c.compression_ratios.label("compression_ratios"),
            timeframes.c.upload_starts_at.label("upload_starts_at"),
            timeframes.c.upload_ends_at.label("upload_ends_at"),
            timeframes.c.eval_starts_at.label("eval_starts_at"),
            timeframes.c.eval_ends_at.label("eval_ends_at"),
        )
        .select_from(
            competitions.join(configs, configs.c.competition_fk == competitions.c.id)
            .join(timeframes, timeframes.c.competition_config_fk == configs.c.id)
            .join(comp_ratios, comp_ratios.c.competition_config_fk == configs.c.id)
        )
        .where(configs.c.is_active.is_(True))
        .where(timeframes.c.eval_ends_at > sa.func.now())
    )

    table = view_table("v_active_competition")
    return ViewDefinition(name=table.name, table=table, selectable=selectable)
