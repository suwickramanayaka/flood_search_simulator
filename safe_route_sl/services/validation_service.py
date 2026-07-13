"""Graph validation helpers for SafeRouteSL."""

from __future__ import annotations

from math import isinf
from typing import Callable

import networkx as nx

from algorithms.base import EPSILON, calculate_path_cost
from models.configuration import SearchConfiguration
from models.search_models import SearchResult
from services.graph_service import create_traversable_graph, get_available_goal_nodes
from utils.constants import FLOOD_RISK_LABELS, ROAD_CONDITION_PENALTIES
from utils.exceptions import DataValidationError, GraphValidationError, UnavailableGoalError


def validate_search_configuration(configuration: SearchConfiguration) -> None:
    if not isinstance(configuration, SearchConfiguration):
        raise DataValidationError(f"Invalid search configuration: {configuration!r}")
    if not configuration.algorithm.strip():
        raise DataValidationError("algorithm cannot be empty")
    if not configuration.start_node.strip():
        raise DataValidationError("start_node cannot be empty")
    if not configuration.goal_node.strip():
        raise DataValidationError("goal_node cannot be empty")


def validate_graph(graph: nx.Graph) -> None:
    if graph is None or graph.number_of_nodes() == 0:
        raise GraphValidationError("Graph must contain at least one node")

    for node_id, node_data in graph.nodes(data=True):
        required = {"name", "short_name", "location_type", "latitude", "longitude", "capacity", "available", "description"}
        missing = required - set(node_data)
        if missing:
            raise GraphValidationError(
                f"Node {node_id!r} is missing required attributes: {', '.join(sorted(missing))}"
            )
        latitude = node_data["latitude"]
        longitude = node_data["longitude"]
        if not isinstance(latitude, (int, float)) or not -90.0 <= float(latitude) <= 90.0:
            raise GraphValidationError(f"Node {node_id!r} has invalid latitude: {latitude!r}")
        if not isinstance(longitude, (int, float)) or not -180.0 <= float(longitude) <= 180.0:
            raise GraphValidationError(f"Node {node_id!r} has invalid longitude: {longitude!r}")

    for source, target, edge_data in graph.edges(data=True):
        required = {"road_name", "distance_km", "travel_time_min", "flood_risk", "road_condition", "blocked"}
        missing = required - set(edge_data)
        if missing:
            raise GraphValidationError(
                f"Edge {source!r} -> {target!r} is missing required attributes: {', '.join(sorted(missing))}"
            )
        if source not in graph or target not in graph:
            raise GraphValidationError(f"Edge {source!r} -> {target!r} references unknown endpoints")
        if source == target:
            raise GraphValidationError(f"Unexpected self-loop detected at node {source!r}")
        if float(edge_data["distance_km"]) <= 0:
            raise GraphValidationError(f"Edge {source!r} -> {target!r} has invalid distance")
        if float(edge_data["travel_time_min"]) <= 0:
            raise GraphValidationError(f"Edge {source!r} -> {target!r} has invalid travel time")
        if int(edge_data["flood_risk"]) not in FLOOD_RISK_LABELS:
            raise GraphValidationError(f"Edge {source!r} -> {target!r} has invalid flood risk")
        if edge_data["road_condition"] not in ROAD_CONDITION_PENALTIES:
            raise GraphValidationError(f"Edge {source!r} -> {target!r} has unsupported road condition")

    if not get_available_goal_nodes(graph):
        raise GraphValidationError("Graph does not contain any available evacuation destination nodes")

def validate_start_goal(graph: nx.Graph, start_node: str, goal_node: str) -> None:
    if start_node not in graph:
        raise GraphValidationError(f"Unknown start node: {start_node!r}")
    if goal_node not in graph:
        raise GraphValidationError(f"Unknown goal node: {goal_node!r}")
    validate_goal_available(graph, goal_node)


def validate_goal_available(graph: nx.Graph, goal_node: str) -> None:
    if goal_node not in graph:
        raise GraphValidationError(f"Unknown goal node: {goal_node!r}")

    goal_data = graph.nodes[goal_node]
    if not goal_data.get("available", False):
        raise UnavailableGoalError(f"Goal node {goal_node!r} is unavailable")


def validate_non_negative_costs(graph: nx.Graph, cost_function: Callable[[dict], float]) -> None:
    for source, target, edge_data in graph.edges(data=True):
        cost = cost_function(dict(edge_data))
        if cost < 0:
            raise GraphValidationError(f"Negative cost detected on edge {source!r} -> {target!r}")


def validate_search_result(graph: nx.Graph, result: SearchResult, configuration: SearchConfiguration) -> None:
    if not result.steps:
        raise GraphValidationError("Search result must include at least one step")

    expected_numbers = tuple(range(len(result.steps)))
    actual_numbers = tuple(step.step_number for step in result.steps)
    if actual_numbers != expected_numbers:
        raise GraphValidationError("Search step numbers must be sequential starting at zero")

    if result.nodes_expanded < 0 or result.nodes_generated < 0 or result.maximum_frontier_size < 0:
        raise GraphValidationError("Search metrics must be non-negative")
    if result.repeated_state_skips < 0 or result.execution_time_ms < 0:
        raise GraphValidationError("Search metrics must be non-negative")
    if result.path_length_edges < 0:
        raise GraphValidationError("Path length cannot be negative")

    if result.found:
        if not result.final_path:
            raise GraphValidationError("Successful search results must include a final path")
        if result.final_path[0] != configuration.start_node:
            raise GraphValidationError("Final path must start at the configured start node")
        if result.final_path[-1] != configuration.goal_node:
            raise GraphValidationError("Final path must end at the configured goal node")
        if result.path_length_edges != max(0, len(result.final_path) - 1):
            raise GraphValidationError("Path length does not match the final path")
        if any(not graph.has_edge(source, target) for source, target in zip(result.final_path, result.final_path[1:])):
            raise GraphValidationError("Final path contains a missing edge")
        if any(graph[source][target].get("blocked", False) for source, target in zip(result.final_path, result.final_path[1:])):
            raise GraphValidationError("Final path contains a blocked edge")

        recomputed_cost = calculate_path_cost(
            graph,
            result.final_path,
            configuration.optimization_mode,
            configuration.risk_weight,
        )
        if abs(recomputed_cost - result.total_cost) > EPSILON:
            raise GraphValidationError("Stored total cost does not match the recomputed path cost")
        if isinf(result.total_cost) or result.total_cost < 0:
            raise GraphValidationError("Successful search results must have a finite non-negative total cost")
        if result.steps[-1].event_type != "goal" or not result.steps[-1].goal_found:
            raise GraphValidationError("Successful search results must end with a goal step")
    else:
        if result.final_path:
            raise GraphValidationError("Failed search results must not include a final path")
        if not isinf(result.total_cost):
            raise GraphValidationError("Failed search results must report infinite total cost")
        if not result.error_message:
            raise GraphValidationError("Failed search results must include an error message")
        if result.steps[-1].event_type != "failure":
            raise GraphValidationError("Failed search results must end with a failure step")


def has_available_route(graph: nx.Graph, start_node: str, goal_node: str) -> bool:
    if start_node not in graph or goal_node not in graph:
        return False
    traversable_graph = create_traversable_graph(graph)
    return nx.has_path(traversable_graph, start_node, goal_node)
