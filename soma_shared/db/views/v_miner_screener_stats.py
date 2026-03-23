from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.batch_challenge import BatchChallenge
from soma_shared.db.models.batch_challenge_score import BatchChallengeScore
from soma_shared.db.models.challenge_batch import ChallengeBatch
from soma_shared.db.models.miner import Miner
from soma_shared.db.models.miner_upload import MinerUpload
from soma_shared.db.models.screener import Screener
from soma_shared.db.models.screening_challenge import ScreeningChallenge
from soma_shared.db.models.script import Script

from .base import ViewDefinition, view_table, weight, weighted_score


def v_miner_screener_stats(
    materialized: bool = False,
    unique_index_columns: tuple[str, ...] = (),
) -> ViewDefinition:
    challenge_batches = ChallengeBatch.__table__
    scripts = Script.__table__
    miners = Miner.__table__
    miner_uploads = MinerUpload.__table__
    batch_challenges = BatchChallenge.__table__
    scores = BatchChallengeScore.__table__
    screening = ScreeningChallenge.__table__
    screeners = Screener.__table__

    from_clause = (
        challenge_batches.join(scripts, scripts.c.id == challenge_batches.c.script_fk)
        .join(miners, miners.c.id == scripts.c.miner_fk)
        .join(miner_uploads, miner_uploads.c.script_fk == scripts.c.id)
        .join(
            batch_challenges,
            batch_challenges.c.challenge_batch_fk == challenge_batches.c.id,
        )
        .join(screeners, screeners.c.competition_fk == miner_uploads.c.competition_fk)
        .join(
            screening,
            sa.and_(
                screening.c.screener_fk == screeners.c.id,
                screening.c.challenge_fk == batch_challenges.c.challenge_fk,
            ),
        )
        .outerjoin(scores, scores.c.batch_challenge_fk == batch_challenges.c.id)
    )

    scored_weight = sa.case(
        (scores.c.id.is_not(None), weight(batch_challenges.c.compression_ratio)),
        else_=0.0,
    )
    scored_score = sa.case(
        (
            scores.c.id.is_not(None),
            weighted_score(scores.c.score, batch_challenges.c.compression_ratio),
        ),
        else_=0.0,
    )

    base = (
        sa.select(
            miner_uploads.c.competition_fk.label("competition_id"),
            miners.c.id.label("miner_id"),
            miners.c.ss58.label("ss58"),
            miners.c.miner_banned_status.label("is_banned"),
            (
                sa.func.sum(scored_score) / sa.func.nullif(sa.func.sum(scored_weight), 0)
            ).label("total_screener_score"),
            sa.func.count(sa.distinct(scores.c.batch_challenge_fk)).label("screener_scored"),
            sa.func.min(miner_uploads.c.created_at).label("first_upload_at"),
        )
        .select_from(from_clause)
        .where(screeners.c.is_active.is_(True))
        .group_by(miner_uploads.c.competition_fk, miners.c.id, miners.c.ss58, miners.c.miner_banned_status)
        .subquery()
    )

    selectable = sa.select(
        base.c.competition_id,
        base.c.miner_id,
        base.c.ss58,
        base.c.is_banned,
        base.c.total_screener_score,
        base.c.screener_scored,
        base.c.first_upload_at,
        sa.func.row_number()
        .over(
            partition_by=base.c.competition_id,
            order_by=(
                base.c.total_screener_score.desc().nullslast(),
                base.c.first_upload_at.asc().nullsfirst(),
                base.c.ss58.asc(),
            ),
        )
        .label("screener_rank"),
    )
    name = "mv_miner_screener_stats" if materialized else "v_miner_screener_stats"
    table = view_table(name)
    return ViewDefinition(
        name=table.name,
        table=table,
        selectable=selectable,
        materialized=materialized,
        unique_index_columns=unique_index_columns,
    )
