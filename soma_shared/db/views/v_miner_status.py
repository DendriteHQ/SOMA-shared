from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.batch_challenge import BatchChallenge
from soma_shared.db.models.batch_challenge_score import BatchChallengeScore
from soma_shared.db.models.challenge_batch import ChallengeBatch
from soma_shared.db.models.competition_challenge import CompetitionChallenge
from soma_shared.db.models.miner import Miner
from soma_shared.db.models.miner_upload import MinerUpload
from soma_shared.db.models.screener import Screener
from soma_shared.db.models.screening_challenge import ScreeningChallenge
from soma_shared.db.models.script import Script

from .base import ViewDefinition, view_table, weight, weighted_score


def v_miner_status(
    materialized: bool = False,
    unique_index_columns: tuple[str, ...] = (),
) -> ViewDefinition:
    challenge_batches = ChallengeBatch.__table__
    batch_challenges = BatchChallenge.__table__
    scores = BatchChallengeScore.__table__
    miners = Miner.__table__
    miner_uploads = MinerUpload.__table__
    scripts = Script.__table__
    screeners = Screener.__table__
    screening = ScreeningChallenge.__table__
    comp_challenges = CompetitionChallenge.__table__

    # Active screener challenge IDs per competition (used as anti-join target)
    screener_ids_sq = (
        sa.select(
            screeners.c.competition_fk.label("competition_id"),
            screening.c.challenge_fk.label("challenge_id"),
        )
        .select_from(screeners.join(screening, screening.c.screener_fk == screeners.c.id))
        .where(screeners.c.is_active.is_(True))
        .subquery()
    )

    # Total distinct non-screener (challenge, compression_ratio) pairs per competition.
    # Represents how many task-ratio combos a fully-evaluated miner should have scored.
    total_comp_sq = (
        sa.select(
            comp_challenges.c.competition_fk.label("competition_id"),
            sa.func.count(
                sa.distinct(
                    sa.tuple_(
                        batch_challenges.c.challenge_fk,
                        batch_challenges.c.compression_ratio,
                    )
                )
            ).label("competition_challenges"),
        )
        .select_from(
            batch_challenges
            .join(comp_challenges, comp_challenges.c.challenge_fk == batch_challenges.c.challenge_fk)
            .outerjoin(
                screener_ids_sq,
                sa.and_(
                    screener_ids_sq.c.challenge_id == batch_challenges.c.challenge_fk,
                    screener_ids_sq.c.competition_id == comp_challenges.c.competition_fk,
                ),
            )
        )
        .where(comp_challenges.c.is_active.is_(True))
        .where(screener_ids_sq.c.challenge_id.is_(None))
        .group_by(comp_challenges.c.competition_fk)
        .subquery()
    )

    # Screener stats per (competition_id, miner_id): assigned count, scored count,
    # and weighted avg score (used later to rank eligible screener miners).
    scored_w = sa.case(
        (scores.c.id.is_not(None), weight(batch_challenges.c.compression_ratio)),
        else_=sa.literal(0.0),
    )
    scored_s = sa.case(
        (scores.c.id.is_not(None), weighted_score(scores.c.score, batch_challenges.c.compression_ratio)),
        else_=sa.literal(0.0),
    )

    screener_stats_sq = (
        sa.select(
            miner_uploads.c.competition_fk.label("competition_id"),
            challenge_batches.c.miner_fk.label("miner_id"),
            miners.c.miner_banned_status.label("is_banned"),
            sa.func.count(sa.distinct(batch_challenges.c.id)).label("screener_assigned"),
            sa.func.count(sa.distinct(scores.c.batch_challenge_fk)).label("screener_scored"),
            (
                sa.func.sum(scored_s) / sa.func.nullif(sa.func.sum(scored_w), 0)
            ).label("screener_avg_score"),
        )
        .select_from(
            challenge_batches
            .join(miners, miners.c.id == challenge_batches.c.miner_fk)
            .join(scripts, scripts.c.id == challenge_batches.c.script_fk)
            .join(miner_uploads, miner_uploads.c.script_fk == scripts.c.id)
            .join(batch_challenges, batch_challenges.c.challenge_batch_fk == challenge_batches.c.id)
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
        .where(screeners.c.is_active.is_(True))
        .group_by(
            miner_uploads.c.competition_fk,
            challenge_batches.c.miner_fk,
            miners.c.miner_banned_status,
        )
        .subquery()
    )

    # Eligible screener miners: fully scored (screener_scored >= screener_assigned)
    # and not banned. Ranked by weighted avg screener score per competition.
    # screener_rank / total_eligible_screener let the caller compute is_in_top_screener
    # as: screener_rank <= ceil(total_eligible_screener * top_fraction).
    eligible_screener_sq = (
        sa.select(
            screener_stats_sq.c.competition_id,
            screener_stats_sq.c.miner_id,
            sa.func.row_number()
            .over(
                partition_by=screener_stats_sq.c.competition_id,
                order_by=(
                    screener_stats_sq.c.screener_avg_score.desc().nullslast(),
                    screener_stats_sq.c.miner_id.asc(),
                ),
            )
            .label("screener_rank"),
            sa.func.count(sa.literal(1))
            .over(partition_by=screener_stats_sq.c.competition_id)
            .label("total_eligible_screener"),
        )
        .select_from(screener_stats_sq)
        .where(screener_stats_sq.c.is_banned.is_(False))
        .where(screener_stats_sq.c.screener_scored >= screener_stats_sq.c.screener_assigned)
        .subquery()
    )

    # Competition stats per (competition_id, miner_id), excluding screener challenges.
    comp_stats_sq = (
        sa.select(
            comp_challenges.c.competition_fk.label("competition_id"),
            challenge_batches.c.miner_fk.label("miner_id"),
            sa.func.count(sa.distinct(batch_challenges.c.id)).label("competition_assigned"),
            sa.func.count(sa.distinct(scores.c.batch_challenge_fk)).label("scored_competition_challenges"),
        )
        .select_from(
            challenge_batches
            .join(scripts, scripts.c.id == challenge_batches.c.script_fk)
            .join(miner_uploads, miner_uploads.c.script_fk == scripts.c.id)
            .join(batch_challenges, batch_challenges.c.challenge_batch_fk == challenge_batches.c.id)
            .outerjoin(scores, scores.c.batch_challenge_fk == batch_challenges.c.id)
            .join(comp_challenges, comp_challenges.c.challenge_fk == batch_challenges.c.challenge_fk)
            .outerjoin(
                screener_ids_sq,
                sa.and_(
                    screener_ids_sq.c.challenge_id == batch_challenges.c.challenge_fk,
                    screener_ids_sq.c.competition_id == comp_challenges.c.competition_fk,
                ),
            )
        )
        .where(comp_challenges.c.is_active.is_(True))
        .where(miner_uploads.c.competition_fk == comp_challenges.c.competition_fk)
        .where(screener_ids_sq.c.challenge_id.is_(None))
        .group_by(comp_challenges.c.competition_fk, challenge_batches.c.miner_fk)
        .subquery()
    )

    # Base: every (competition_id, miner) pair where the miner has an upload
    # (= has_script=True). Miners absent from this view are idle.
    base_sq = (
        sa.select(
            miner_uploads.c.competition_fk.label("competition_id"),
            miners.c.id.label("miner_id"),
            miners.c.ss58.label("ss58"),
            miners.c.miner_banned_status.label("is_banned"),
            sa.func.max(miner_uploads.c.created_at).label("last_submit_at"),
        )
        .select_from(
            miner_uploads
            .join(scripts, scripts.c.id == miner_uploads.c.script_fk)
            .join(miners, miners.c.id == scripts.c.miner_fk)
        )
        .group_by(
            miner_uploads.c.competition_fk,
            miners.c.id,
            miners.c.ss58,
            miners.c.miner_banned_status,
        )
        .subquery()
    )

    # Column names mirror _miner_status() parameters for direct mapping.
    selectable = sa.select(
        base_sq.c.competition_id,
        base_sq.c.ss58,
        base_sq.c.is_banned,
        sa.literal(True).label("has_script"),
        total_comp_sq.c.competition_challenges,
        screener_stats_sq.c.screener_assigned.label("screener_challenges"),
        screener_stats_sq.c.screener_scored.label("scored_screened_challenges"),
        (
            sa.func.coalesce(screener_stats_sq.c.screener_assigned, 0)
            - sa.func.coalesce(screener_stats_sq.c.screener_scored, 0)
        ).label("pending_assignments_screener"),
        comp_stats_sq.c.scored_competition_challenges,
        (
            sa.func.coalesce(comp_stats_sq.c.competition_assigned, 0)
            - sa.func.coalesce(comp_stats_sq.c.scored_competition_challenges, 0)
        ).label("pending_assignments_competition"),
        eligible_screener_sq.c.screener_rank,
        eligible_screener_sq.c.total_eligible_screener,
        base_sq.c.last_submit_at,
    ).select_from(
        base_sq
        .outerjoin(
            total_comp_sq,
            total_comp_sq.c.competition_id == base_sq.c.competition_id,
        )
        .outerjoin(
            screener_stats_sq,
            sa.and_(
                screener_stats_sq.c.competition_id == base_sq.c.competition_id,
                screener_stats_sq.c.miner_id == base_sq.c.miner_id,
            ),
        )
        .outerjoin(
            comp_stats_sq,
            sa.and_(
                comp_stats_sq.c.competition_id == base_sq.c.competition_id,
                comp_stats_sq.c.miner_id == base_sq.c.miner_id,
            ),
        )
        .outerjoin(
            eligible_screener_sq,
            sa.and_(
                eligible_screener_sq.c.competition_id == base_sq.c.competition_id,
                eligible_screener_sq.c.miner_id == base_sq.c.miner_id,
            ),
        )
    )

    name = "mv_miner_status" if materialized else "v_miner_status"
    table = view_table(name)
    return ViewDefinition(
        name=table.name,
        table=table,
        selectable=selectable,
        materialized=materialized,
        unique_index_columns=unique_index_columns,
    )
