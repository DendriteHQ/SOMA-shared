from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.competition_challenge import CompetitionChallenge
from soma_shared.db.models.screener import Screener
from soma_shared.db.models.screening_challenge import ScreeningChallenge

from .base import ViewDefinition, view_table


def v_competition_challenges(
    materialized: bool = False,
    unique_index_columns: tuple[str, ...] = (),
) -> ViewDefinition:
    comp_challenges = CompetitionChallenge.__table__
    screeners = Screener.__table__
    screening = ScreeningChallenge.__table__

    is_screener_sq = sa.exists(
        sa.select(sa.literal(1))
        .select_from(
            screening.join(screeners, screeners.c.id == screening.c.screener_fk)
        )
        .where(screening.c.challenge_fk == comp_challenges.c.challenge_fk)
        .where(screeners.c.is_active.is_(True))
        .where(screeners.c.competition_fk == comp_challenges.c.competition_fk)
    )

    # EXISTS avoids row multiplication from screening_challenges and screeners.
    selectable = (
        sa.select(
            comp_challenges.c.competition_fk.label("competition_id"),
            comp_challenges.c.challenge_fk.label("challenge_id"),
            comp_challenges.c.is_active.label("is_active"),
            is_screener_sq.label("is_screener"),
        )
        .select_from(comp_challenges)
    )

    name = "mv_competition_challenges" if materialized else "v_competition_challenges"
    table = view_table(name)
    return ViewDefinition(
        name=table.name,
        table=table,
        selectable=selectable,
        materialized=materialized,
        unique_index_columns=unique_index_columns,
    )
