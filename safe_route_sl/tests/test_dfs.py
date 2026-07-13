"""Depth-first search tests for SafeRouteSL."""

from __future__ import annotations

import networkx as nx

from algorithms.depth_first import DepthFirstSearch
from tests.support import add_edge, add_node, make_greedy_trap_graph, make_start_goal_config, make_unweighted_choice_graph


def test_dfs_returns_a_valid_deterministic_path() -> None:
    graph = make_greedy_trap_graph()
    result = DepthFirstSearch().search(graph, make_start_goal_config("Depth-First Search", "A", "G"))

    assert result.found is True
    assert result.final_path == ("A", "B", "G")
    assert result.steps[0].event_type == "initialize"
    assert result.steps[-1].event_type == "goal"


def test_dfs_avoids_cycles_and_ignores_blocked_roads() -> None:
    graph = nx.Graph()
    for node_id, coords in (("A", (0.0, 0.0)), ("B", (0.0, 1.0)), ("C", (1.0, 0.0)), ("G", (1.0, 1.0))):
        add_node(graph, node_id, *coords)
    add_edge(graph, "A", "B", distance_km=1.0)
    add_edge(graph, "B", "C", distance_km=1.0)
    add_edge(graph, "C", "A", distance_km=1.0)
    add_edge(graph, "C", "G", distance_km=1.0, blocked=True)
    add_edge(graph, "B", "G", distance_km=1.0)

    result = DepthFirstSearch().search(graph, make_start_goal_config("Depth-First Search", "A", "G"))
    assert result.final_path == ("A", "B", "G")
    assert result.repeated_state_skips >= 1


def test_dfs_start_equals_goal_and_no_route() -> None:
    graph = make_unweighted_choice_graph()
    same = DepthFirstSearch().search(graph, make_start_goal_config("Depth-First Search", "A", "A"))
    assert same.found is True
    assert same.final_path == ("A",)

    blocked_graph = make_unweighted_choice_graph()
    blocked_graph["A"]["B"]["blocked"] = True
    blocked_graph["B"]["G"]["blocked"] = True
    blocked_graph["A"]["C"]["blocked"] = True
    blocked_graph["C"]["D"]["blocked"] = True
    blocked_graph["D"]["G"]["blocked"] = True
    no_route = DepthFirstSearch().search(blocked_graph, make_start_goal_config("Depth-First Search", "A", "G"))
    assert no_route.found is False
    assert no_route.final_path == ()
"""Phase 1 placeholder for DFS tests."""
