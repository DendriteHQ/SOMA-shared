"""Materialize batch challenge questions for frontend challenge pages.

Revision ID: c14d2be1f9aa
Revises: a8f2d6c4b1e9
Create Date: 2026-04-02

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_batch_challenge_questions import v_batch_challenge_questions


revision = "c14d2be1f9aa"
down_revision = "a8f2d6c4b1e9"
branch_labels = None
depends_on = None


def _compile(selectable: sa.sql.Select) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)


def upgrade() -> None:
    mv = v_batch_challenge_questions(
        materialized=True,
        unique_index_columns=("batch_challenge_id", "question_id"),
    )
    sql = _compile(mv.selectable)

    op.execute(sa.text(f"DROP MATERIALIZED VIEW IF EXISTS {mv.name} CASCADE"))
    op.execute(sa.text(f"CREATE MATERIALIZED VIEW IF NOT EXISTS {mv.name} AS {sql}"))
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "mv_batch_challenge_questions_uidx "
            "ON mv_batch_challenge_questions (batch_challenge_id, question_id)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS mv_batch_challenge_questions CASCADE"))
