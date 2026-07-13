"""Breadth-first search tests for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import pytest

from algorithms.breadth_first import BreadthFirstSearch
from algorithms.base import calculate_path_cost
from services.graph_service import create_traversable_graph
from tests.support import add_edge, add_node, make_start_goal_config, make_unweighted_choice_graph
from utils.constants import BALANCED_MODE


def test_bfs_finds_minimum_edge_path_and_records_steps() -> None:
    graph = make_unweighted_choice_graph()
    config = make_start_goal_config("Breadth-First Search", "A", "G", optimization_mode=BALANCED_MODE)

    result = BreadthFirstSearch().search(graph, config)

    assert result.found is True
    assert result.final_path == ("A", "B", "G")
    assert result.steps[0].event_type == "initialize"
    assert result.steps[-1].event_type == "goal"
    assert result.steps[-1].goal_found is True
    assert result.total_cost == calculate_path_cost(graph, result.final_path, BALANCED_MODE, 4.0)
    assert result.path_length_edges == 2


def test_bfs_ignores_blocked_roads_and_handles_cycles() -> None:
    graph = nx.Graph()
    for node_id, coords in (("A", (0.0, 0.0)), ("B", (0.0, 1.0)), ("C", (1.0, 0.0)), ("G", (1.0, 1.0))):
        add_node(graph, node_id, *coords)
    add_edge(graph, "A", "B", distance_km=1.0)
    add_edge(graph, "B", "C", distance_km=1.0)
    add_edge(graph, "C", "A", distance_km=1.0)
    add_edge(graph, "C", "G", distance_km=1.0, blocked=True)
    add_edge(graph, "B", "G", distance_km=1.0)

    config = make_start_goal_config("Breadth-First Search", "A", "G")
    result = BreadthFirstSearch().search(graph, config)

    assert result.final_path == ("A", "B", "G")
    assert all(not graph[path_a][path_b]["blocked"] for path_a, path_b in zip(result.final_path, result.final_path[1:]))
    assert result.repeated_state_skips >= 1


def test_bfs_start_equals_goal_and_no_route() -> None:
    graph = make_unweighted_choice_graph()
    same = BreadthFirstSearch().search(graph, make_start_goal_config("Breadth-First Search", "A", "A"))
    assert same.found is True
    assert same.final_path == ("A",)
    assert same.total_cost == 0.0

    blocked_graph = make_unweighted_choice_graph()
    blocked_graph["A"]["B"]["blocked"] = True
    blocked_graph["B"]["G"]["blocked"] = True
    blocked_graph["A"]["C"]["blocked"] = True
    blocked_graph["C"]["D"]["blocked"] = True
    blocked_graph["D"]["G"]["blocked"] = True
    no_route = BreadthFirstSearch().search(blocked_graph, make_start_goal_config("Breadth-First Search", "A", "G"))
    assert no_route.found is False
    assert no_route.final_path == ()
    assert no_route.total_cost == float("inf")
    assert no_route.steps[-1].event_type == "failure"


def test_bfs_deterministic_choice_on_equal_frontier() -> None:
    graph = nx.Graph()
    for node_id, coords in (("A", (0.0, 0.0)), ("B", (0.0, 1.0)), ("C", (1.0, 0.0)), ("G", (1.0, 1.0))):
        add_node(graph, node_id, *coords)
    add_edge(graph, "A", "B", distance_km=1.0)
    add_edge(graph, "B", "G", distance_km=1.0)
    add_edge(graph, "A", "C", distance_km=1.0)
    add_edge(graph, "C", "G", distance_km=1.0)

    result = BreadthFirstSearch().search(graph, make_start_goal_config("Breadth-First Search", "A", "G"))
    assert result.final_path == ("A", "B", "G")


def test_recorded_explored_nodes_are_sorted() -> None:
    graph = make_unweighted_choice_graph()
    result = BreadthFirstSearch().search(
        graph,
        make_start_goal_config("Breadth-First Search", "A", "G"),
    )

    assert all(step.explored_nodes == tuple(sorted(step.explored_nodes)) for step in result.steps)
"""Phase 1 placeholder for BFS tests."""
