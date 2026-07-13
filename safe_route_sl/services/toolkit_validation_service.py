"""Validate custom searches against deterministic NetworkX references."""

from __future__ import annotations

from dataclasses import dataclass, replace
from math import isclose

import networkx as nx

from algorithms.base import calculate_path_cost
from algorithms.networkx_adapter import (
    run_networkx_astar,
    run_networkx_bfs_shortest_path,
    run_networkx_dijkstra,
)
from models.configuration import SearchConfiguration
from models.search_models import SearchResult
from services.graph_service import create_traversable_graph
from services.search_service import run_search
from utils.constants import DISTANCE_MODE
from utils.exceptions import SafeRouteError


DEFAULT_VALIDATION_ALGORITHMS = (
    "Breadth-First Search",
    "Uniform-Cost Search",
    "A* Search",
)
COST_RELATIVE_TOLERANCE = 1e-9
COST_ABSOLUTE_TOLERANCE = 1e-8


@dataclass(frozen=True, slots=True)
class ToolkitValidationRecord:
    """Immutable comparison between one custom and toolkit search result."""

    algorithm_name: str
    custom_path: tuple[str, ...]
    toolkit_path: tuple[str, ...]
    custom_cost: float
    toolkit_cost: float
    custom_path_edges: int
    toolkit_path_edges: int
    validation_status: str
    validation_message: str
    toolkit_name: str
    optimality_scope: str
    error_message: str | None = None


def is_valid_traversable_path(
    graph: nx.Graph,
    path: tuple[str, ...],
    start_node: str,
    goal_node: str,
) -> bool:
    """Return whether ``path`` connects the endpoints through open roads."""
    if not path or path[0] != start_node or path[-1] != goal_node:
        return False
    traversable_graph = create_traversable_graph(graph)
    return all(
        traversable_graph.has_edge(source, target)
        for source, target in zip(path, path[1:])
    )


def _toolkit_result(
    graph: nx.Graph,
    configuration: SearchConfiguration,
) -> tuple[tuple[str, ...], float]:
    """Run the matching NetworkX reference for one configured algorithm."""
    if configuration.algorithm == "Breadth-First Search":
        path = run_networkx_bfs_shortest_path(
            graph,
            configuration.start_node,
            configuration.goal_node,
        )
        cost = calculate_path_cost(
            graph,
            path,
            configuration.optimization_mode,
            configuration.risk_weight,
        )
        return path, float(cost)
    if configuration.algorithm == "Uniform-Cost Search":
        return run_networkx_dijkstra(graph, configuration)
    if configuration.algorithm == "A* Search":
        return run_networkx_astar(graph, configuration)
    raise ValueError(f"No NetworkX validation adapter for {configuration.algorithm!r}")


def _optimality_scope(configuration: SearchConfiguration) -> str:
    """Describe what an A* agreement can establish for this heuristic."""
    if configuration.algorithm != "A* Search":
        return "Reference behavior comparison"
    if configuration.heuristic_type == "zero":
        return "Zero heuristic; A* behaves like UCS"
    if configuration.optimization_mode == DISTANCE_MODE:
        return "Distance-mode Haversine optimality validation"
    return "Conditional: Haversine is an educational estimate for this cost mode"


def _failed_record(
    algorithm_name: str,
    message: str,
    *,
    custom_result: SearchResult | None = None,
    toolkit_path: tuple[str, ...] = (),
    toolkit_cost: float = float("inf"),
) -> ToolkitValidationRecord:
    """Build a failure record without exposing exception objects."""
    custom_path = custom_result.final_path if custom_result is not None else ()
    custom_cost = custom_result.total_cost if custom_result is not None else float("inf")
    configuration_scope = "Reference validation could not be completed"
    return ToolkitValidationRecord(
        algorithm_name=algorithm_name,
        custom_path=custom_path,
        toolkit_path=toolkit_path,
        custom_cost=custom_cost,
        toolkit_cost=toolkit_cost,
        custom_path_edges=max(0, len(custom_path) - 1),
        toolkit_path_edges=max(0, len(toolkit_path) - 1),
        validation_status="Failed",
        validation_message=message,
        toolkit_name="NetworkX",
        optimality_scope=configuration_scope,
        error_message=message,
    )


def _compare_bfs(
    graph: nx.Graph,
    configuration: SearchConfiguration,
    custom_result: SearchResult,
    toolkit_path: tuple[str, ...],
    toolkit_cost: float,
) -> ToolkitValidationRecord:
    """Compare BFS path validity and minimum edge count."""
    custom_valid = is_valid_traversable_path(
        graph,
        custom_result.final_path,
        configuration.start_node,
        configuration.goal_node,
    )
    toolkit_valid = is_valid_traversable_path(
        graph,
        toolkit_path,
        configuration.start_node,
        configuration.goal_node,
    )
    custom_edges = custom_result.path_length_edges
    toolkit_edges = max(0, len(toolkit_path) - 1)
    passed = custom_valid and toolkit_valid and custom_edges == toolkit_edges
    if not passed:
        status = "Failed"
        message = "BFS paths must both be valid and use the same minimum number of edges."
    elif custom_result.final_path == toolkit_path:
        status = "Passed"
        message = f"Both BFS implementations produced a valid {custom_edges}-edge shortest path."
    else:
        status = "Passed with alternate equal path"
        message = (
            f"Both BFS paths are valid and use {custom_edges} edges; different equal-length paths are acceptable."
        )
    return ToolkitValidationRecord(
        algorithm_name=configuration.algorithm,
        custom_path=custom_result.final_path,
        toolkit_path=toolkit_path,
        custom_cost=custom_result.total_cost,
        toolkit_cost=toolkit_cost,
        custom_path_edges=custom_edges,
        toolkit_path_edges=toolkit_edges,
        validation_status=status,
        validation_message=message,
        toolkit_name="NetworkX unweighted shortest path",
        optimality_scope="Minimum edge-count validation",
        error_message=None if passed else message,
    )


def _compare_weighted(
    graph: nx.Graph,
    configuration: SearchConfiguration,
    custom_result: SearchResult,
    toolkit_path: tuple[str, ...],
    toolkit_cost: float,
) -> ToolkitValidationRecord:
    """Compare UCS or A* path validity and weighted route cost."""
    custom_valid = is_valid_traversable_path(
        graph,
        custom_result.final_path,
        configuration.start_node,
        configuration.goal_node,
    )
    toolkit_valid = is_valid_traversable_path(
        graph,
        toolkit_path,
        configuration.start_node,
        configuration.goal_node,
    )
    costs_match = isclose(
        custom_result.total_cost,
        toolkit_cost,
        rel_tol=COST_RELATIVE_TOLERANCE,
        abs_tol=COST_ABSOLUTE_TOLERANCE,
    )
    scope = _optimality_scope(configuration)
    passed = custom_valid and toolkit_valid and costs_match
    conditional = (
        configuration.algorithm == "A* Search"
        and configuration.heuristic_type == "haversine"
        and configuration.optimization_mode != DISTANCE_MODE
    )

    if not passed:
        status = "Failed"
        message = "Custom and NetworkX paths must be valid and their weighted costs must match within tolerance."
    elif conditional:
        status = "Conditional"
        message = (
            "Custom and NetworkX A* costs match, but Haversine is only an educational estimate for this cost mode; "
            "optimality is conditional."
        )
    elif configuration.algorithm == "A* Search" and configuration.heuristic_type == "zero":
        status = "Passed"
        message = "Costs match within tolerance; with a zero heuristic, A* behaves like UCS."
    else:
        status = "Passed"
        message = "Both valid paths have matching weighted cost within floating-point tolerance."

    return ToolkitValidationRecord(
        algorithm_name=configuration.algorithm,
        custom_path=custom_result.final_path,
        toolkit_path=toolkit_path,
        custom_cost=custom_result.total_cost,
        toolkit_cost=toolkit_cost,
        custom_path_edges=custom_result.path_length_edges,
        toolkit_path_edges=max(0, len(toolkit_path) - 1),
        validation_status=status,
        validation_message=message,
        toolkit_name="NetworkX A*" if configuration.algorithm == "A* Search" else "NetworkX Dijkstra",
        optimality_scope=scope,
        error_message=None if passed else message,
    )


def _validate_one(
    graph: nx.Graph,
    base_configuration: SearchConfiguration,
    algorithm_name: str,
) -> ToolkitValidationRecord:
    """Run one custom search and compare it with its NetworkX reference."""
    if algorithm_name not in DEFAULT_VALIDATION_ALGORITHMS:
        return ToolkitValidationRecord(
            algorithm_name=algorithm_name,
            custom_path=(),
            toolkit_path=(),
            custom_cost=float("inf"),
            toolkit_cost=float("inf"),
            custom_path_edges=0,
            toolkit_path_edges=0,
            validation_status="Toolkit unavailable",
            validation_message="No NetworkX reference adapter is configured for this algorithm.",
            toolkit_name="NetworkX",
            optimality_scope="Not available",
            error_message=None,
        )

    configuration = replace(base_configuration, algorithm=algorithm_name)

    try:
        custom_result = run_search(graph, configuration)
    except SafeRouteError as error:
        return _failed_record(algorithm_name, f"Custom search failed: {error}")

    try:
        toolkit_path, toolkit_cost = _toolkit_result(graph, configuration)
    except SafeRouteError as error:
        if not custom_result.found:
            return ToolkitValidationRecord(
                algorithm_name=algorithm_name,
                custom_path=(),
                toolkit_path=(),
                custom_cost=custom_result.total_cost,
                toolkit_cost=float("inf"),
                custom_path_edges=0,
                toolkit_path_edges=0,
                validation_status="No route",
                validation_message="Neither the custom implementation nor NetworkX found a traversable route.",
                toolkit_name="NetworkX",
                optimality_scope=_optimality_scope(configuration),
                error_message=None,
            )
        return _failed_record(
            algorithm_name,
            f"NetworkX validation failed: {error}",
            custom_result=custom_result,
        )

    if not custom_result.found:
        return _failed_record(
            algorithm_name,
            "NetworkX found a route while the custom implementation reported no route.",
            custom_result=custom_result,
            toolkit_path=toolkit_path,
            toolkit_cost=toolkit_cost,
        )

    if algorithm_name == "Breadth-First Search":
        return _compare_bfs(graph, configuration, custom_result, toolkit_path, toolkit_cost)
    return _compare_weighted(graph, configuration, custom_result, toolkit_path, toolkit_cost)


def validate_against_toolkits(
    graph: nx.Graph,
    configuration: SearchConfiguration,
    algorithm_names: tuple[str, ...] | None = None,
) -> tuple[ToolkitValidationRecord, ...]:
    """Validate requested custom algorithms in deterministic request order."""
    requested_names = algorithm_names or DEFAULT_VALIDATION_ALGORITHMS
    return tuple(
        _validate_one(graph, configuration, algorithm_name)
        for algorithm_name in requested_names
    )
