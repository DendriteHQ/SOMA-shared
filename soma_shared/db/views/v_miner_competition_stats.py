from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.batch_challenge import BatchChallenge
from soma_shared.db.models.batch_challenge_score import BatchChallengeScore
from soma_shared.db.models.challenge_batch import ChallengeBatch
from soma_shared.db.models.competition_challenge import CompetitionChallenge
from soma_shared.db.models.miner import Miner
from soma_shared.db.models.miner_upload import MinerUpload
from soma_shared.db.models.script import Script

from .base import ViewDefinition, view_table, weighted_avg


def v_miner_competition_stats(
    materialized: bool = False,
    unique_index_columns: tuple[str, ...] = (),
) -> ViewDefinition:
    challenge_batches = ChallengeBatch.__table__
    scripts = Script.__table__
    miners = Miner.__table__
    miner_uploads = MinerUpload.__table__
    batch_challenges = BatchChallenge.__table__
    scores = BatchChallengeScore.__table__
    comp_challenges = CompetitionChallenge.__table__

    base = (
        sa.select(
            comp_challenges.c.competition_fk.label("competition_id"),
            miners.c.ss58.label("ss58"),
            miners.c.miner_banned_status.label("is_banned"),
            weighted_avg(scores.c.score, batch_challenges.c.compression_ratio).label(
                "total_score"
            ),
            sa.func.min(miner_uploads.c.created_at).label("first_upload_at"),
        )
        .select_from(
            challenge_batches
            .join(scripts, scripts.c.id == challenge_batches.c.script_fk)
            .join(miners, miners.c.id == scripts.c.miner_fk)
            .join(miner_uploads, miner_uploads.c.script_fk == scripts.c.id)
            .join(batch_challenges, batch_challenges.c.challenge_batch_fk == challenge_batches.c.id)
            .outerjoin(scores, scores.c.batch_challenge_fk == batch_challenges.c.id)
            .join(comp_challenges, comp_challenges.c.challenge_fk == batch_challenges.c.challenge_fk)
        )
        .where(comp_challenges.c.is_active.is_(True))
        .where(miner_uploads.c.competition_fk == comp_challenges.c.competition_fk)
        .group_by(comp_challenges.c.competition_fk, miners.c.ss58, miners.c.miner_banned_status)
        .subquery()
    )

    selectable = sa.select(
        base.c.competition_id,
        base.c.ss58,
        base.c.is_banned,
        base.c.total_score,
        base.c.first_upload_at,
        sa.func.row_number()
        .over(
            partition_by=base.c.competition_id,
            order_by=(
                base.c.total_score.desc().nullslast(),
                base.c.first_upload_at.asc().nullsfirst(),
                base.c.ss58.asc(),
            ),
        )
        .label("rank")
    )

    name = "mv_miner_competition_stats" if materialized else "v_miner_competition_stats"
    table = view_table(name)
    return ViewDefinition(
        name=table.name,
        table=table,
        selectable=selectable,
        materialized=materialized,
        unique_index_columns=unique_index_columns,
    )
