"""drop every legacy v_*/mv_* view that may still exist

Revision ID: 79ae4349c7b9
Revises: d8f1a3c5e7b9
Create Date: 2026-10-28

Earlier migrations dropped most of these, but some were only ever created at app
startup by create_or_replace_views (v_miner_competition_rank,
v_screener_challenges_active) and no migration removed them. The list covers every
view name the views registry or a migration has created. Each name is dropped as
whatever it is now: mv_batch_challenge_questions was both a materialized and a
plain view over its life, and DROP VIEW IF EXISTS fails on a materialized view.

Runs before the legacy table drop, which uses no CASCADE and would fail on any
view still reading those tables.
"""

from __future__ import annotations

from alembic import op


revision = "79ae4349c7b9"
down_revision = "d8f1a3c5e7b9"
branch_labels = None
depends_on = None


LEGACY_VIEWS = (
    "mv_batch_challenge_questions",
    "mv_competition_challenges",
    "mv_miner_competition_stats",
    "mv_miner_screener_stats",
    "mv_miner_status",
    "v_active_competition",
    "v_batch_challenge_questions",
    "v_competition_challenges",
    "v_miner_competition_rank",
    "v_miner_competition_ratio_ranked",
    "v_miner_competition_stats",
    "v_miner_screener_eligible_ranked",
    "v_miner_screener_qualified",
    "v_miner_screener_stats",
    "v_miner_status",
    "v_screener_challenges_active",
)


def _drop_view(name: str) -> None:
    # CASCADE only reaches other views built on this one; tables are untouched.
    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM pg_matviews
                WHERE schemaname = 'public' AND matviewname = '{name}'
            ) THEN
                EXECUTE 'DROP MATERIALIZED VIEW public.{name} CASCADE';
            ELSIF EXISTS (
                SELECT 1 FROM pg_views
                WHERE schemaname = 'public' AND viewname = '{name}'
            ) THEN
                EXECUTE 'DROP VIEW public.{name} CASCADE';
            END IF;
        END $$;
        """
    )


def upgrade() -> None:
    for name in LEGACY_VIEWS:
        _drop_view(name)


def downgrade() -> None:
    raise NotImplementedError("Legacy views are not recreated.")
