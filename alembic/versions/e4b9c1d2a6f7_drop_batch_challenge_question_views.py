"""Drop batch challenge question snapshot views.

Revision ID: e4b9c1d2a6f7
Revises: d8c4f1b2a7e6
Create Date: 2026-04-02

"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_batch_challenge_questions import v_batch_challenge_questions


revision = "e4b9c1d2a6f7"
down_revision = "d8c4f1b2a7e6"
branch_labels = None
depends_on = None


def _compile(selectable: sa.sql.Select) -> str:
    compiled = selectable.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    )
    return str(compiled)


def upgrade() -> None:
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_matviews
                    WHERE schemaname = 'public'
                      AND matviewname = 'mv_batch_challenge_questions'
                ) THEN
                    EXECUTE 'DROP MATERIALIZED VIEW public.mv_batch_challenge_questions CASCADE';
                ELSIF EXISTS (
                    SELECT 1
                    FROM pg_views
                    WHERE schemaname = 'public'
                      AND viewname = 'mv_batch_challenge_questions'
                ) THEN
                    EXECUTE 'DROP VIEW public.mv_batch_challenge_questions CASCADE';
                END IF;
            END $$;
            """
        )
    )
    op.execute(sa.text("DROP VIEW IF EXISTS v_batch_challenge_questions CASCADE"))


def downgrade() -> None:
    view = v_batch_challenge_questions(materialized=False)
    sql = _compile(view.selectable)

    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1
                    FROM pg_matviews
                    WHERE schemaname = 'public'
                      AND matviewname = 'mv_batch_challenge_questions'
                ) THEN
                    EXECUTE 'DROP MATERIALIZED VIEW public.mv_batch_challenge_questions CASCADE';
                ELSIF EXISTS (
                    SELECT 1
                    FROM pg_views
                    WHERE schemaname = 'public'
                      AND viewname = 'mv_batch_challenge_questions'
                ) THEN
                    EXECUTE 'DROP VIEW public.mv_batch_challenge_questions CASCADE';
                END IF;
            END $$;
            """
        )
    )
    op.execute(sa.text("DROP VIEW IF EXISTS v_batch_challenge_questions CASCADE"))
    op.execute(sa.text(f"CREATE OR REPLACE VIEW v_batch_challenge_questions AS {sql}"))
    op.execute(sa.text(f"CREATE OR REPLACE VIEW mv_batch_challenge_questions AS {sql}"))
