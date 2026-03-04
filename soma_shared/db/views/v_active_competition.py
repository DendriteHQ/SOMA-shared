from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.competition import Competition
from soma_shared.db.models.competition_config import CompetitionConfig

from .base import ViewDefinition, view_table


def v_active_competition() -> ViewDefinition:
    competitions = Competition.__table__
    configs = CompetitionConfig.__table__

    ranked = (
        sa.select(
            competitions.c.id.label("competition_id"),
            competitions.c.competition_name.label("competition_name"),
            competitions.c.created_at.label("competition_created_at"),
            configs.c.id.label("competition_config_id"),
            configs.c.created_at.label("competition_config_created_at"),
            sa.func.row_number()
            .over(
                order_by=(
                    competitions.c.created_at.desc(),
                    configs.c.created_at.desc(),
                )
            )
            .label("_rn"),
        )
        .select_from(
            competitions.join(configs, configs.c.competition_fk == competitions.c.id)
        )
        .where(configs.c.is_active.is_(True))
        .subquery()
    )

    selectable = sa.select(
        ranked.c.competition_id,
        ranked.c.competition_name,
        ranked.c.competition_created_at,
        ranked.c.competition_config_id,
        ranked.c.competition_config_created_at,
    ).where(ranked.c._rn == 1)

    table = view_table("v_active_competition")
    return ViewDefinition(name=table.name, table=table, selectable=selectable)
