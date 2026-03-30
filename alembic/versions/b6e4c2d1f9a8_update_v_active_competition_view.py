"""Update v_active_competition to return all active competitions.

Revision ID: b6e4c2d1f9a8
Revises: a3e1f2c9b8d7
Create Date: 2026-03-24
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from soma_shared.db.views.v_active_competition import v_active_competition


# revision identifiers, used by Alembic.
revision: str = "b6e4c2d1f9a8"
down_revision: Union[str, Sequence[str], None] = "a3e1f2c9b8d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _compile(selectable: sa.sql.Select) -> str:
    return str(
        selectable.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


def _previous_selectable() -> sa.sql.Select:
    competitions = sa.table(
        "competitions",
        sa.column("id"),
        sa.column("competition_name"),
        sa.column("created_at"),
    )
    configs = sa.table(
        "competition_configs",
        sa.column("competition_fk"),
        sa.column("id"),
        sa.column("is_active"),
    )
    timeframes = sa.table(
        "competition_timeframes",
        sa.column("competition_config_fk"),
        sa.column("upload_starts_at"),
        sa.column("upload_ends_at"),
        sa.column("eval_starts_at"),
        sa.column("eval_ends_at"),
    )
    comp_ratios = sa.table(
        "compression_competition_config",
        sa.column("competition_config_fk"),
        sa.column("compression_ratios"),
    )

    return (
        sa.select(
            competitions.c.id.label("competition_id"),
            competitions.c.competition_name.label("competition_name"),
            competitions.c.created_at.label("competition_created_at"),
            comp_ratios.c.compression_ratios.label("compression_ratios"),
            timeframes.c.upload_starts_at.label("upload_starts_at"),
            timeframes.c.upload_ends_at.label("upload_ends_at"),
            timeframes.c.eval_starts_at.label("eval_starts_at"),
            timeframes.c.eval_ends_at.label("eval_ends_at"),
        )
        .select_from(
            competitions.join(configs, configs.c.competition_fk == competitions.c.id)
            .join(timeframes, timeframes.c.competition_config_fk == configs.c.id)
            .join(comp_ratios, comp_ratios.c.competition_config_fk == configs.c.id)
        )
        .where(configs.c.is_active.is_(True))
        .where(timeframes.c.eval_ends_at > sa.func.now())
        .order_by(timeframes.c.eval_ends_at.desc())
        .limit(1)
    )


def upgrade() -> None:
    """Upgrade schema."""
    view_def = v_active_competition()
    sql = _compile(view_def.selectable)
    op.execute(sa.text(f"CREATE OR REPLACE VIEW {view_def.name} AS {sql}"))


def downgrade() -> None:
    """Downgrade schema."""
    sql = _compile(_previous_selectable())
    op.execute(sa.text(f"CREATE OR REPLACE VIEW v_active_competition AS {sql}"))