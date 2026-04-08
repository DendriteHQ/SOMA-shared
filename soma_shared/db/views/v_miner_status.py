from __future__ import annotations

import os
import sqlalchemy as sa

from soma_shared.db.models.batch_challenge import BatchChallenge
from soma_shared.db.models.batch_challenge_score import BatchChallengeScore
from soma_shared.db.models.challenge_batch import ChallengeBatch
from soma_shared.db.models.competition_challenge import CompetitionChallenge
from soma_shared.db.models.competition_config import CompetitionConfig
from soma_shared.db.models.compression_competition_config import CompressionCompetitionConfig
from soma_shared.db.models.miner import Miner
from soma_shared.db.models.miner_upload import MinerUpload
from soma_shared.db.models.screener import Screener
from soma_shared.db.models.screening_challenge import ScreeningChallenge
from soma_shared.db.models.script import Script

from .base import ViewDefinition, view_table, weight, weighted_score


def v_miner_status(
    materialized: bool = False,
    unique_index_columns: tuple[str, ...] = (),
    top_screener_fraction: float | None = None,
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

    # Shared: one row per competition with the configured compression ratio count.
    # Used by both total_screener_sq and total_comp_sq so scored/required counts
    # are always in the same units (challenge × ratio pairs).
    comp_configs = CompetitionConfig.__table__
    compression_configs = CompressionCompetitionConfig.__table__

    _comp_ratio_sq = (
        sa.select(
            comp_configs.c.competition_fk.label("competition_id"),
            sa.func.coalesce(
                sa.func.json_array_length(compression_configs.c.compression_ratios),
                sa.literal(1),
            ).label("ratio_count"),
        )
        .select_from(
            comp_configs.outerjoin(
                compression_configs,
                compression_configs.c.competition_config_fk == comp_configs.c.id,
            )
        )
        .where(comp_configs.c.is_active.is_(True))
        .subquery()
    )

    # Total screener (challenge × ratio) pairs per competition.
    # scored_screened_challenges counts batch_challenge IDs (one per challenge×ratio),
    # so screener_challenges must use the same unit for the backlog check to work.
    _total_screener_challenges_sq = (
        sa.select(
            screeners.c.competition_fk.label("competition_id"),
            sa.func.count(
                sa.distinct(screening.c.challenge_fk)
            ).label("screener_challenge_count"),
        )
        .select_from(
            screeners.join(screening, screening.c.screener_fk == screeners.c.id)
        )
        .where(screeners.c.is_active.is_(True))
        .group_by(screeners.c.competition_fk)
        .subquery()
    )

    total_screener_sq = (
        sa.select(
            _total_screener_challenges_sq.c.competition_id,
            (
                _total_screener_challenges_sq.c.screener_challenge_count
                * _comp_ratio_sq.c.ratio_count
            ).label("screener_challenges"),
        )
        .select_from(
            _total_screener_challenges_sq.join(
                _comp_ratio_sq,
                _comp_ratio_sq.c.competition_id == _total_screener_challenges_sq.c.competition_id,
            )
        )
        .subquery()
    )

    # One row per competition: count of active non-screener competition challenges.
    _comp_challenge_count_sq = (
        sa.select(
            comp_challenges.c.competition_fk.label("competition_id"),
            sa.func.count(sa.distinct(comp_challenges.c.challenge_fk)).label("nonscreener_count"),
        )
        .select_from(
            comp_challenges.outerjoin(
                screener_ids_sq,
                sa.and_(
                    screener_ids_sq.c.challenge_id == comp_challenges.c.challenge_fk,
                    screener_ids_sq.c.competition_id == comp_challenges.c.competition_fk,
                ),
            )
        )
        .where(comp_challenges.c.is_active.is_(True))
        .where(screener_ids_sq.c.challenge_id.is_(None))
        .group_by(comp_challenges.c.competition_fk)
        .subquery()
    )

    total_comp_sq = (
        sa.select(
            _comp_challenge_count_sq.c.competition_id,
            (
                _comp_challenge_count_sq.c.nonscreener_count
                * _comp_ratio_sq.c.ratio_count
            ).label("competition_challenges"),
        )
        .select_from(
            _comp_challenge_count_sq.join(
                _comp_ratio_sq,
                _comp_ratio_sq.c.competition_id == _comp_challenge_count_sq.c.competition_id,
            )
        )
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
    # screener_rank / total_eligible_screener are also used to compute status.
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

    has_script_expr = sa.literal(True)
    competition_challenges_expr = total_comp_sq.c.competition_challenges
    screener_challenges_expr = total_screener_sq.c.screener_challenges
    scored_screened_challenges_expr = screener_stats_sq.c.screener_scored
    pending_assignments_screener_expr = (
        sa.func.coalesce(screener_stats_sq.c.screener_assigned, 0)
        - sa.func.coalesce(screener_stats_sq.c.screener_scored, 0)
    )
    scored_competition_challenges_expr = comp_stats_sq.c.scored_competition_challenges
    pending_assignments_competition_expr = (
        sa.func.coalesce(comp_stats_sq.c.competition_assigned, 0)
        - sa.func.coalesce(comp_stats_sq.c.scored_competition_challenges, 0)
    )

    resolved_top_fraction = top_screener_fraction
    if resolved_top_fraction is None:
        raw_fraction = os.getenv("TOP_SCREENER_SCRIPTS")
        try:
            resolved_top_fraction = float(raw_fraction) if raw_fraction is not None else 0.2
        except ValueError:
            resolved_top_fraction = 0.2
    if resolved_top_fraction > 1:
        resolved_top_fraction = min(resolved_top_fraction, 100.0) / 100.0
    resolved_top_fraction = min(max(resolved_top_fraction, 0.0), 1.0)

    top_fraction_expr = sa.literal(resolved_top_fraction)
    is_in_top_screener_expr = sa.and_(
        top_fraction_expr > 0,
        eligible_screener_sq.c.screener_rank.is_not(None),
        eligible_screener_sq.c.total_eligible_screener.is_not(None),
        eligible_screener_sq.c.screener_rank
        <= sa.func.greatest(
            sa.literal(1),
            sa.func.ceil(eligible_screener_sq.c.total_eligible_screener * top_fraction_expr),
        ),
    )

    # Status logic mirrors mcp_platform.app.api.routes.utils._miner_status.
    status_expr = sa.case(
        (base_sq.c.is_banned.is_(True), sa.literal("banned")),
        (has_script_expr.is_(False), sa.literal("idle")),
        (
            sa.and_(
                competition_challenges_expr.is_not(None),
                scored_competition_challenges_expr.is_not(None),
                scored_competition_challenges_expr >= competition_challenges_expr,
            ),
            sa.literal("scored"),
        ),
        (
            sa.and_(
                competition_challenges_expr.is_not(None),
                scored_competition_challenges_expr.is_not(None),
                scored_competition_challenges_expr > 0,
                scored_competition_challenges_expr < competition_challenges_expr,
            ),
            sa.literal("evaluating"),
        ),
        (
            sa.and_(
                pending_assignments_screener_expr.is_not(None),
                pending_assignments_screener_expr > 0,
            ),
            sa.literal("screening"),
        ),
        (
            sa.and_(
                screener_challenges_expr.is_not(None),
                screener_challenges_expr > 0,
                scored_screened_challenges_expr.is_not(None),
                scored_screened_challenges_expr < screener_challenges_expr,
            ),
            sa.literal("screening"),
        ),
        (
            sa.and_(
                screener_challenges_expr.is_not(None),
                screener_challenges_expr > 0,
                scored_screened_challenges_expr.is_not(None),
                scored_screened_challenges_expr >= screener_challenges_expr,
                is_in_top_screener_expr,
                sa.or_(
                    pending_assignments_competition_expr.is_(None),
                    pending_assignments_competition_expr == 0,
                ),
                sa.or_(
                    scored_competition_challenges_expr.is_(None),
                    scored_competition_challenges_expr == 0,
                ),
            ),
            sa.literal("qualified"),
        ),
        (
            sa.and_(
                screener_challenges_expr.is_not(None),
                screener_challenges_expr > 0,
                scored_screened_challenges_expr.is_not(None),
                scored_screened_challenges_expr >= screener_challenges_expr,
                sa.not_(is_in_top_screener_expr),
            ),
            sa.literal("not qualified"),
        ),
        (
            sa.and_(
                pending_assignments_competition_expr.is_not(None),
                pending_assignments_competition_expr > 0,
            ),
            sa.literal("evaluating"),
        ),
        else_=sa.literal("in queue"),
    )

    # Columns are kept for API compatibility; status is precomputed here.
    selectable = sa.select(
        base_sq.c.competition_id,
        base_sq.c.ss58,
        base_sq.c.is_banned,
        has_script_expr.label("has_script"),
        competition_challenges_expr.label("competition_challenges"),
        screener_challenges_expr.label("screener_challenges"),
        scored_screened_challenges_expr.label("scored_screened_challenges"),
        pending_assignments_screener_expr.label("pending_assignments_screener"),
        scored_competition_challenges_expr.label("scored_competition_challenges"),
        pending_assignments_competition_expr.label("pending_assignments_competition"),
        eligible_screener_sq.c.screener_rank,
        eligible_screener_sq.c.total_eligible_screener,
        status_expr.label("status"),
        base_sq.c.last_submit_at,
    ).select_from(
        base_sq
        .outerjoin(
            total_comp_sq,
            total_comp_sq.c.competition_id == base_sq.c.competition_id,
        )
        .outerjoin(
            total_screener_sq,
            total_screener_sq.c.competition_id == base_sq.c.competition_id,
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
