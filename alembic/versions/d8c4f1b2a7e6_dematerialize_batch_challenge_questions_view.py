"""Dematerialize mv_batch_challenge_questions.

Revision ID: d8c4f1b2a7e6
Revises: c14d2be1f9aa
Create Date: 2026-04-02

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_batch_challenge_questions import v_batch_challenge_questions


revision = "d8c4f1b2a7e6"
down_revision = "c14d2be1f9aa"
branch_labels = None
depends_on = None


def _compile(selectable: sa.sql.Select) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)


def upgrade() -> None:
    view = v_batch_challenge_questions(materialized=False)
    sql = _compile(view.selectable)

    # Replace the materialized view with a regular SQL view so frontend reads
    # do not depend on background REFRESH completion.
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_batch_challenge_questions CASCADE"))
    op.execute(sa.text("DROP VIEW IF EXISTS mv_batch_challenge_questions CASCADE"))
    op.execute(sa.text(f"CREATE OR REPLACE VIEW mv_batch_challenge_questions AS {sql}"))


def downgrade() -> None:
    mv = v_batch_challenge_questions(
        materialized=True,
        unique_index_columns=("batch_challenge_id", "question_id"),
    )
    sql = _compile(mv.selectable)

    op.execute(sa.text("DROP VIEW IF EXISTS mv_batch_challenge_questions CASCADE"))
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_batch_challenge_questions CASCADE"))
    op.execute(
        sa.text(
            f"CREATE MATERIALIZED VIEW IF NOT EXISTS mv_batch_challenge_questions AS {sql} WITH NO DATA"
        )
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "mv_batch_challenge_questions_uidx "
            "ON mv_batch_challenge_questions (batch_challenge_id, question_id)"
        )
    )
