"""Common search algorithm interface and shared helpers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import replace
from typing import Any, Iterable, Sequence

import networkx as nx

from models.configuration import SearchConfiguration
from models.search_models import SearchResult, SearchStep
from services.graph_service import get_edge_data
from utils.cost_functions import calculate_edge_cost
from utils.exceptions import GraphValidationError

EPSILON = 1e-9


class SearchAlgorithm(ABC):
    name: str
    toolkit_source: str = "Custom Python"
    optimality_expected: bool = False
    completeness_expected: bool = False

    @abstractmethod
    def search(self, graph: nx.Graph, configuration: SearchConfiguration) -> SearchResult:
        raise NotImplementedError


def validate_inputs(graph: nx.Graph, configuration: SearchConfiguration) -> None:
    if graph is None or graph.number_of_nodes() == 0:
        raise GraphValidationError("Graph must contain at least one node")
    if configuration.start_node not in graph:
        raise GraphValidationError(f"Unknown start node: {configuration.start_node!r}")
    if configuration.goal_node not in graph:
        raise GraphValidationError(f"Unknown goal node: {configuration.goal_node!r}")


def calculate_path_cost(
    graph: nx.Graph,
    path: tuple[str, ...],
    optimization_mode: str,
    risk_weight: float,
) -> float:
    if len(path) <= 1:
        return 0.0

    total = 0.0
    for source, target in zip(path, path[1:]):
        edge_data = graph.get_edge_data(source, target)
        if edge_data is None:
            raise GraphValidationError(f"Path contains missing edge: {source} to {target}")

        edge_cost = calculate_edge_cost(edge_data, optimization_mode, risk_weight)
        if edge_cost == float("inf"):
            raise GraphValidationError(f"Path contains blocked edge: {source} to {target}")
        total += edge_cost

    return total


def build_failure_result(
    algorithm_name: str,
    configuration: SearchConfiguration,
    steps: list[SearchStep],
    nodes_expanded: int,
    nodes_generated: int,
    maximum_frontier_size: int,
    repeated_state_skips: int,
    execution_time_ms: float,
    error_message: str,
    *,
    toolkit_source: str = "Custom Python",
    optimality_expected: bool = False,
    completeness_expected: bool = True,
) -> SearchResult:
    return SearchResult(
        algorithm_name=algorithm_name,
        toolkit_source=toolkit_source,
        found=False,
        start_node=configuration.start_node,
        goal_node=configuration.goal_node,
        final_path=(),
        total_cost=float("inf"),
        nodes_expanded=nodes_expanded,
        nodes_generated=nodes_generated,
        maximum_frontier_size=maximum_frontier_size,
        path_length_edges=0,
        repeated_state_skips=repeated_state_skips,
        execution_time_ms=execution_time_ms,
        steps=tuple(steps),
        optimality_expected=optimality_expected,
        completeness_expected=completeness_expected,
        error_message=error_message,
    )


def build_success_result(
    algorithm_name: str,
    configuration: SearchConfiguration,
    final_path: tuple[str, ...],
    steps: list[SearchStep],
    nodes_expanded: int,
    nodes_generated: int,
    maximum_frontier_size: int,
    repeated_state_skips: int,
    execution_time_ms: float,
    total_cost: float,
    *,
    toolkit_source: str = "Custom Python",
    optimality_expected: bool = False,
    completeness_expected: bool = True,
) -> SearchResult:
    return SearchResult(
        algorithm_name=algorithm_name,
        toolkit_source=toolkit_source,
        found=True,
        start_node=configuration.start_node,
        goal_node=configuration.goal_node,
        final_path=final_path,
        total_cost=total_cost,
        nodes_expanded=nodes_expanded,
        nodes_generated=nodes_generated,
        maximum_frontier_size=maximum_frontier_size,
        path_length_edges=max(0, len(final_path) - 1),
        repeated_state_skips=repeated_state_skips,
        execution_time_ms=execution_time_ms,
        steps=tuple(steps),
        optimality_expected=optimality_expected,
        completeness_expected=completeness_expected,
        error_message=None,
    )


def build_start_equals_goal_result(
    algorithm_name: str,
    configuration: SearchConfiguration,
    initial_step: SearchStep,
    goal_step: SearchStep,
    execution_time_ms: float,
    *,
    toolkit_source: str = "Custom Python",
    optimality_expected: bool = False,
    completeness_expected: bool = True,
) -> SearchResult:
    return SearchResult(
        algorithm_name=algorithm_name,
        toolkit_source=toolkit_source,
        found=True,
        start_node=configuration.start_node,
        goal_node=configuration.goal_node,
        final_path=(configuration.start_node,),
        total_cost=0.0,
        nodes_expanded=goal_step.nodes_expanded,
        nodes_generated=goal_step.nodes_generated,
        maximum_frontier_size=max(initial_step.maximum_frontier_size, goal_step.maximum_frontier_size),
        path_length_edges=0,
        repeated_state_skips=goal_step.nodes_expanded - 1 if goal_step.nodes_expanded > 0 else 0,
        execution_time_ms=execution_time_ms,
        steps=(initial_step, goal_step),
        optimality_expected=optimality_expected,
        completeness_expected=completeness_expected,
        error_message=None,
    )


def make_initial_step(
    start_node: str,
    frontier_entries: Sequence[dict[str, object]],
    *,
    step_number: int = 0,
    g_cost: float | None = None,
    h_cost: float | None = None,
    f_cost: float | None = None,
    explanation: str,
) -> SearchStep:
    frontier_nodes = tuple(entry["node"] for entry in frontier_entries)
    return SearchStep(
        step_number=step_number,
        event_type="initialize",
        current_node=None,
        frontier_nodes=frontier_nodes,
        explored_nodes=(),
        current_path=(start_node,),
        frontier_entries=tuple(dict(entry) for entry in frontier_entries),
        g_cost=g_cost,
        h_cost=h_cost,
        f_cost=f_cost,
        nodes_expanded=0,
        nodes_generated=1,
        maximum_frontier_size=len(frontier_entries),
        goal_found=False,
        explanation=explanation,
    )


def make_step(
    step_number: int,
    event_type: str,
    current_node: str | None,
    frontier_entries: Sequence[dict[str, object]],
    explored_nodes: Iterable[str],
    current_path: Sequence[str],
    *,
    g_cost: float | None = None,
    h_cost: float | None = None,
    f_cost: float | None = None,
    nodes_expanded: int = 0,
    nodes_generated: int = 0,
    maximum_frontier_size: int = 0,
    goal_found: bool = False,
    explanation: str = "",
) -> SearchStep:
    frontier_nodes = tuple(entry["node"] for entry in frontier_entries)
    return SearchStep(
        step_number=step_number,
        event_type=event_type,
        current_node=current_node,
        frontier_nodes=frontier_nodes,
        explored_nodes=tuple(sorted(explored_nodes)),
        current_path=tuple(current_path),
        frontier_entries=tuple(dict(entry) for entry in frontier_entries),
        g_cost=g_cost,
        h_cost=h_cost,
        f_cost=f_cost,
        nodes_expanded=nodes_expanded,
        nodes_generated=nodes_generated,
        maximum_frontier_size=maximum_frontier_size,
        goal_found=goal_found,
        explanation=explanation,
    )


def serialize_frontier_entry(
    node: str,
    path: Sequence[str],
    *,
    priority: float | None = None,
    g: float | None = None,
    h: float | None = None,
    f: float | None = None,
) -> dict[str, object]:
    return {
        "node": node,
        "priority": priority,
        "g": g,
        "h": h,
        "f": f,
        "path": tuple(path),
    }


def sort_frontier_entries(entries: Iterable[dict[str, object]]) -> list[dict[str, object]]:
    def sort_key(entry: dict[str, object]) -> tuple[int, float, str]:
        priority = entry["priority"]
        numeric_priority = float(priority) if priority is not None else 0.0
        return (0 if priority is not None else 1, numeric_priority, str(entry["node"]))

    return sorted(entries, key=sort_key)


def clean_frontier_entries(entries: Iterable[dict[str, object]]) -> tuple[dict[str, object], ...]:
    return tuple(sort_frontier_entries(entries))
