"""baseline

Revision ID: c5a7e9b1d3f2
Revises:
Create Date: 2026-10-01

Migration history up to this revision was squashed; the removed files are in git
history (SOMA-shared commit cb2d697). Production and dev databases already stand
at this revision, so upgrading from here needs no stamp.

The revision ID is kept from the squashed "add jev columns to swe_bench_runs"
migration so that alembic_version on existing databases still resolves.

A fresh database gets its schema from Base.metadata.create_all (init_db), after
which `alembic upgrade head` applies the later revisions; they are written to be
no-ops on a schema that create_all already built.
"""

from __future__ import annotations


revision = "c5a7e9b1d3f2"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    raise NotImplementedError("Cannot downgrade below the squashed baseline.")
