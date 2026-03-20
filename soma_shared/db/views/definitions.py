from __future__ import annotations

from .base import ViewDefinition
from .v_active_competition import v_active_competition
from .v_competition_challenges import v_competition_challenges
from .v_miner_competition_stats import v_miner_competition_stats
from .v_miner_screener_stats import v_miner_screener_stats
from .v_miner_status import v_miner_status


# Regular (live) views — used by backend for real-time data.
VIEW_DEFINITIONS: tuple[ViewDefinition, ...] = (
    v_active_competition(),
    v_competition_challenges(),
    v_miner_screener_stats(),
    v_miner_competition_stats(),
    v_miner_status(),
)

# Materialized views — snapshots of the heavy regular views above.
# Frontend reads from these; they are refreshed periodically in the background.
# Each entry mirrors a regular view but with materialized=True and a unique
# index definition (required for REFRESH MATERIALIZED VIEW CONCURRENTLY).
MV_DEFINITIONS: tuple[ViewDefinition, ...] = (
    v_competition_challenges(materialized=True, unique_index_columns=("competition_id", "challenge_id")),
    v_miner_screener_stats(materialized=True, unique_index_columns=("competition_id", "ss58")),
    v_miner_competition_stats(materialized=True, unique_index_columns=("competition_id", "ss58")),
    v_miner_status(materialized=True, unique_index_columns=("competition_id", "ss58")),
)
