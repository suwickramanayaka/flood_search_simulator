"""Immutable search data models used by SafeRouteSL."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class SearchStep:
    step_number: int
    event_type: str
    current_node: str | None
    frontier_nodes: tuple[str, ...]
    explored_nodes: tuple[str, ...]
    current_path: tuple[str, ...]
    frontier_entries: tuple[dict[str, object], ...] = field(default_factory=tuple)
    g_cost: float | None = None
    h_cost: float | None = None
    f_cost: float | None = None
    nodes_expanded: int = 0
    nodes_generated: int = 0
    maximum_frontier_size: int = 0
    goal_found: bool = False
    explanation: str = ""


@dataclass(frozen=True, slots=True)
class SearchResult:
    algorithm_name: str
    toolkit_source: str
    found: bool
    start_node: str
    goal_node: str
    final_path: tuple[str, ...]
    total_cost: float
    nodes_expanded: int
    nodes_generated: int
    maximum_frontier_size: int
    path_length_edges: int
    repeated_state_skips: int
    execution_time_ms: float
    steps: tuple[SearchStep, ...]
    optimality_expected: bool
    completeness_expected: bool
    error_message: str | None = None
