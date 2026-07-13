"""A* search tests for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import pytest

from algorithms.astar import AStarSearch
from algorithms.base import calculate_path_cost
from services.graph_service import load_graph
from tests.support import make_replacement_graph, make_start_goal_config, make_weighted_choice_graph
from utils.constants import DISTANCE_MODE
from utils.cost_functions import create_networkx_weight_function


def test_astar_zero_heuristic_matches_ucs_and_records_f_costs() -> None:
    graph = make_replacement_graph()
    config = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")
    result = AStarSearch().search(graph, config)

    assert result.found is True
    assert result.final_path == ("A", "C", "B", "G")
    assert result.total_cost == pytest.approx(5.0)
    assert result.steps[0].f_cost == pytest.approx(result.steps[0].g_cost + (result.steps[0].h_cost or 0.0))
    assert result.optimality_expected is True


def test_astar_haversine_distance_mode_matches_networkx() -> None:
    graph = make_weighted_choice_graph()
    config = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="haversine")
    result = AStarSearch().search(graph, config)

    weight = create_networkx_weight_function(DISTANCE_MODE, 4.0)
    expected_path = nx.astar_path(
        graph,
        "A",
        "G",
        heuristic=lambda u, v: 0.0 if u == v else 0.0,
        weight=weight,
    )
    expected_cost = calculate_path_cost(graph, tuple(expected_path), DISTANCE_MODE, 4.0)
    assert result.final_path == tuple(expected_path)
    assert result.total_cost == pytest.approx(expected_cost)
    assert result.optimality_expected is True


def test_astar_replaces_paths_and_handles_no_route() -> None:
    graph = make_replacement_graph()
    result = AStarSearch().search(graph, make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero"))

    assert result.final_path == ("A", "C", "B", "G")
    assert result.repeated_state_skips >= 1

    blocked_graph = make_weighted_choice_graph()
    blocked_graph["A"]["B"]["blocked"] = True
    blocked_graph["B"]["G"]["blocked"] = True
    blocked_graph["A"]["C"]["blocked"] = True
    blocked_graph["C"]["D"]["blocked"] = True
    blocked_graph["D"]["G"]["blocked"] = True
    no_route = AStarSearch().search(blocked_graph, make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE))
    assert no_route.found is False
    assert no_route.final_path == ()
"""Phase 1 placeholder for A* tests."""
