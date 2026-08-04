from __future__ import annotations

from .base import ViewDefinition

# Regular (live) views — used by backend for real-time data.
# None currently defined; the last reader (v_miner_screener_eligible_ranked)
# was removed along with its only caller.
VIEW_DEFINITIONS: tuple[ViewDefinition, ...] = ()

# Materialized views — snapshots of heavier regular views.
# None currently defined; frontend reads live-query data directly instead.
MV_DEFINITIONS: tuple[ViewDefinition, ...] = ()
