"""Search execution service for SafeRouteSL."""

from __future__ import annotations

from typing import Type

import networkx as nx

from algorithms.astar import AStarSearch
from algorithms.base import SearchAlgorithm
from algorithms.breadth_first import BreadthFirstSearch
from algorithms.depth_first import DepthFirstSearch
from algorithms.greedy_best_first import GreedyBestFirstSearch
from algorithms.uniform_cost import UniformCostSearch
from models.configuration import SearchConfiguration
from models.search_models import SearchResult
from services.validation_service import (
    validate_goal_available,
    validate_graph,
    validate_non_negative_costs,
    validate_search_configuration,
    validate_search_result,
    validate_start_goal,
)
from utils.cost_functions import calculate_edge_cost
from utils.exceptions import DataValidationError

ALGORITHM_REGISTRY: dict[str, Type[SearchAlgorithm]] = {
    "Breadth-First Search": BreadthFirstSearch,
    "Depth-First Search": DepthFirstSearch,
    "Uniform-Cost Search": UniformCostSearch,
    "Greedy Best-First Search": GreedyBestFirstSearch,
    "A* Search": AStarSearch,
}


def get_supported_algorithms() -> tuple[str, ...]:
    return tuple(ALGORITHM_REGISTRY.keys())


def get_algorithm(algorithm_name: str) -> SearchAlgorithm:
    try:
        return ALGORITHM_REGISTRY[algorithm_name]()
    except KeyError as exc:
        raise DataValidationError(f"Unsupported algorithm: {algorithm_name!r}") from exc


def run_search(graph: nx.Graph, configuration: SearchConfiguration) -> SearchResult:
    validate_search_configuration(configuration)
    validate_graph(graph)
    validate_start_goal(graph, configuration.start_node, configuration.goal_node)
    validate_goal_available(graph, configuration.goal_node)
    validate_non_negative_costs(
        graph,
        lambda edge_data: calculate_edge_cost(edge_data, configuration.optimization_mode, configuration.risk_weight),
    )

    algorithm = get_algorithm(configuration.algorithm)
    result = algorithm.search(graph, configuration)
    validate_search_result(graph, result, configuration)
    return result
