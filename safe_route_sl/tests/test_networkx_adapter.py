"""NetworkX adapter tests for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import pytest

from algorithms.astar import AStarSearch
from algorithms.networkx_adapter import run_networkx_astar, run_networkx_bfs_shortest_path, run_networkx_dijkstra
from algorithms.uniform_cost import UniformCostSearch
from services.graph_service import create_traversable_graph
from tests.support import make_replacement_graph, make_start_goal_config, make_unweighted_choice_graph, make_weighted_choice_graph
from utils.constants import DISTANCE_MODE
from utils.exceptions import GraphValidationError


def test_dijkstra_cost_matches_custom_ucs() -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("Uniform-Cost Search", "A", "G", optimization_mode=DISTANCE_MODE)

    custom_result = UniformCostSearch().search(graph, configuration)
    path, cost = run_networkx_dijkstra(graph, configuration)

    assert path == custom_result.final_path
    assert cost == pytest.approx(custom_result.total_cost)


def test_astar_cost_matches_custom_astar() -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")

    custom_result = AStarSearch().search(graph, configuration)
    path, cost = run_networkx_astar(graph, configuration)

    assert path == custom_result.final_path
    assert cost == pytest.approx(custom_result.total_cost)


def test_bfs_path_has_minimum_edge_count() -> None:
    graph = make_unweighted_choice_graph()
    path = run_networkx_bfs_shortest_path(graph, "A", "G")
    traversable_graph = create_traversable_graph(graph)

    assert len(path) - 1 == nx.shortest_path_length(traversable_graph, "A", "G")


def test_blocked_edges_are_excluded() -> None:
    graph = make_weighted_choice_graph()
    graph["A"]["B"]["blocked"] = True

    path, _ = run_networkx_dijkstra(graph, make_start_goal_config("Uniform-Cost Search", "A", "G", optimization_mode=DISTANCE_MODE))

    assert ("A", "B") not in list(zip(path, path[1:]))


def test_no_path_case_raises_expected_error() -> None:
    graph = make_weighted_choice_graph()
    for source, target in list(graph.edges()):
        graph[source][target]["blocked"] = True

    configuration = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")
    with pytest.raises(GraphValidationError):
        run_networkx_dijkstra(graph, configuration)
