from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.screener import Screener
from soma_shared.db.models.screening_challenge import ScreeningChallenge

from .base import ViewDefinition, view_table


def v_screener_challenges_active() -> ViewDefinition:
    screeners = Screener.__table__
    screening = ScreeningChallenge.__table__

    selectable = (
        sa.select(
            screeners.c.competition_fk.label("competition_id"),
            screeners.c.id.label("screener_id"),
            screening.c.challenge_fk.label("challenge_id"),
        )
        .select_from(screeners.join(screening, screening.c.screener_fk == screeners.c.id))
        .where(screeners.c.is_active.is_(True))
    )

    table = view_table("v_screener_challenges_active")
    return ViewDefinition(name=table.name, table=table, selectable=selectable)
