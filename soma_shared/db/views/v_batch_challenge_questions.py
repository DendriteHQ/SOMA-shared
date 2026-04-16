from __future__ import annotations

import sqlalchemy as sa

from soma_shared.db.models.answer import Answer
from soma_shared.db.models.batch_challenge import BatchChallenge
from soma_shared.db.models.batch_challenge_score import BatchChallengeScore
from soma_shared.db.models.batch_question_answer import BatchQuestionAnswer
from soma_shared.db.models.batch_question_score import BatchQuestionScore
from soma_shared.db.models.challenge import Challenge
from soma_shared.db.models.challenge_batch import ChallengeBatch
from soma_shared.db.models.competition import Competition
from soma_shared.db.models.competition_challenge import CompetitionChallenge
from soma_shared.db.models.miner import Miner
from soma_shared.db.models.miner_upload import MinerUpload
from soma_shared.db.models.question import Question
from soma_shared.db.models.script import Script

from .base import ViewDefinition, view_table


def v_batch_challenge_questions(
    materialized: bool = False,
    unique_index_columns: tuple[str, ...] = (),
) -> ViewDefinition:
    batch_challenges = BatchChallenge.__table__
    challenge_batches = ChallengeBatch.__table__
    scripts = Script.__table__
    miners = Miner.__table__
    miner_uploads = MinerUpload.__table__
    challenges = Challenge.__table__
    comp_challenges = CompetitionChallenge.__table__
    competitions = Competition.__table__
    scores = BatchChallengeScore.__table__
    questions = Question.__table__
    answers = Answer.__table__
    bqa = BatchQuestionAnswer.__table__
    bqs = BatchQuestionScore.__table__

    # One row per (batch_challenge_id, question_id).
    # Header columns (challenge/competition metadata) repeat across all question rows.
    # avg_score and score_details are aggregated across all validator scores.
    selectable = (
        sa.select(
            # --- challenge header ---
            batch_challenges.c.id.label("batch_challenge_id"),
            miners.c.ss58.label("miner_ss58"),
            challenges.c.id.label("challenge_id"),
            challenges.c.challenge_name,
            challenges.c.challenge_text,
            competitions.c.id.label("competition_id"),
            competitions.c.competition_name,
            batch_challenges.c.compression_ratio,
            challenge_batches.c.created_at,
            sa.func.avg(scores.c.score).label("overall_score"),
            sa.func.max(scores.c.created_at).label("scored_at"),
            # --- per-question ---
            questions.c.id.label("question_id"),
            questions.c.question.label("question_text"),
            bqa.c.produced_answer,
            answers.c.answer.label("ground_truth"),
            sa.func.avg(bqs.c.score).label("avg_score"),
            sa.func.json_agg(bqs.c.details).label("score_details"),
        )
        .select_from(
            batch_challenges
            .join(challenge_batches, challenge_batches.c.id == batch_challenges.c.challenge_batch_fk)
            .join(scripts, scripts.c.id == challenge_batches.c.script_fk)
            .join(miners, miners.c.id == challenge_batches.c.miner_fk)
            .join(miner_uploads, miner_uploads.c.script_fk == scripts.c.id)
            .join(challenges, challenges.c.id == batch_challenges.c.challenge_fk)
            .join(comp_challenges, comp_challenges.c.challenge_fk == challenges.c.id)
            .join(
                competitions,
                sa.and_(
                    competitions.c.id == comp_challenges.c.competition_fk,
                    competitions.c.id == miner_uploads.c.competition_fk,
                ),
            )
            .outerjoin(scores, scores.c.batch_challenge_fk == batch_challenges.c.id)
            .join(bqa, bqa.c.batch_challenge_fk == batch_challenges.c.id)
            .join(questions, questions.c.id == bqa.c.question_fk)
            .outerjoin(answers, answers.c.question_fk == questions.c.id)
            .outerjoin(
                bqs,
                sa.and_(
                    bqs.c.question_fk == questions.c.id,
                    bqs.c.batch_challenge_fk == bqa.c.batch_challenge_fk,
                ),
            )
        )
        .where(comp_challenges.c.is_active.is_(True))
        .group_by(
            batch_challenges.c.id,
            miners.c.ss58,
            challenges.c.id,
            challenges.c.challenge_name,
            challenges.c.challenge_text,
            competitions.c.id,
            competitions.c.competition_name,
            batch_challenges.c.compression_ratio,
            challenge_batches.c.created_at,
            questions.c.id,
            questions.c.question,
            bqa.c.produced_answer,
            answers.c.answer,
        )
        .order_by(batch_challenges.c.id, questions.c.id)
    )

    name = "mv_batch_challenge_questions" if materialized else "v_batch_challenge_questions"
    table = view_table(name)
    return ViewDefinition(
        name=table.name,
        table=table,
        selectable=selectable,
        materialized=materialized,
        unique_index_columns=unique_index_columns,
    )