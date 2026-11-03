"""drop legacy compression-challenge and SWE explorer tables

Revision ID: b6b6ade20fc1
Revises: 79ae4349c7b9
Create Date: 2026-10-28

The compression-challenge pipeline (challenges, Q&A, screeners, challenge batches
and their scores) and the SWE explorer validations are no longer read or written
by any service. No table outside this set has a foreign key into it, so dropping
them deletes no rows elsewhere. All tables go in one statement without CASCADE:
foreign keys among them resolve together, and any dependency outside the set
(a view, a foreign key) fails the migration instead of being dropped silently.

Irreversible: restore the data from the pre-migration dump if needed.
"""

from __future__ import annotations

from alembic import op


revision = "b6b6ade20fc1"
down_revision = "79ae4349c7b9"
branch_labels = None
depends_on = None


LEGACY_TABLES = (
    "swe_explorer_edit_validations",
    "swe_explorer_validations",
    "batch_compressed_texts",
    "batch_question_scores",
    "batch_question_answers",
    "batch_challenge_scores",
    "batch_assignments",
    "batch_challenges",
    "challenge_batches",
    "screening_challenges",
    "screeners",
    "competition_challenges",
    "answers",
    "questions",
    "challenges",
)


def upgrade() -> None:
    # DROP takes ACCESS EXCLUSIVE on these tables and on the tables their foreign
    # keys reference (miners, scripts, validators, competitions,
    # swe_bench_run_validations); give up instead of queueing behind long transactions.
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute(f"DROP TABLE IF EXISTS {', '.join(LEGACY_TABLES)}")


def downgrade() -> None:
    raise NotImplementedError("Legacy tables are not recreated; restore them from the dump.")
