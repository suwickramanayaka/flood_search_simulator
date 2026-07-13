"""Search configuration models used by SafeRouteSL."""

from __future__ import annotations

from dataclasses import dataclass

from utils.constants import (
    ALGORITHM_NAMES,
    BALANCED_MODE,
    DISTANCE_MODE,
    SAFETY_MODE,
    SUPPORTED_HEURISTIC_TYPES,
    TIME_MODE,
)
from utils.exceptions import DataValidationError

SUPPORTED_TIE_BREAKING = {"alphabetical", "left_to_right", "lowest_heuristic", "lowest_path_length", "priority_first"}
SUPPORTED_OPTIMIZATION_MODES = {DISTANCE_MODE, TIME_MODE, SAFETY_MODE, BALANCED_MODE}


@dataclass(frozen=True, slots=True)
class SearchConfiguration:
    algorithm: str
    start_node: str
    goal_node: str
    optimization_mode: str = BALANCED_MODE
    risk_weight: float = 4.0
    heuristic_type: str = "haversine"
    tie_breaking: str = "alphabetical"
    scenario_id: str = ""

    def __post_init__(self) -> None:
        if self.algorithm not in ALGORITHM_NAMES.values():
            raise DataValidationError(f"Unsupported algorithm: {self.algorithm!r}")
        if not self.start_node.strip():
            raise DataValidationError("start_node cannot be empty")
        if not self.goal_node.strip():
            raise DataValidationError("goal_node cannot be empty")
        if self.risk_weight < 0:
            raise DataValidationError("risk_weight cannot be negative")
        if self.optimization_mode not in SUPPORTED_OPTIMIZATION_MODES:
            raise DataValidationError(f"Unsupported optimization mode: {self.optimization_mode!r}")
        if self.heuristic_type not in SUPPORTED_HEURISTIC_TYPES:
            raise DataValidationError(f"Unsupported heuristic type: {self.heuristic_type!r}")
        if self.tie_breaking not in SUPPORTED_TIE_BREAKING:
            raise DataValidationError(f"Unsupported tie-breaking rule: {self.tie_breaking!r}")
