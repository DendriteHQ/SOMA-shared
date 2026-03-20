from __future__ import annotations

from .base import ViewDefinition
from .v_active_competition import v_active_competition
from .v_miner_competition_rank import v_miner_competition_rank
from .v_miner_screener_eligible_ranked import v_miner_screener_eligible_ranked
from .v_miner_screener_stats import v_miner_screener_stats
from .v_screener_challenges_active import v_screener_challenges_active


VIEW_DEFINITIONS: tuple[ViewDefinition, ...] = (
    v_active_competition(),
    v_screener_challenges_active(),
    v_miner_screener_stats(),
    v_miner_screener_eligible_ranked(),
    v_miner_competition_rank(),
)
