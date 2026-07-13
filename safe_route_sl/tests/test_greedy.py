"""Greedy best-first search tests for SafeRouteSL."""

from __future__ import annotations

from algorithms.greedy_best_first import GreedyBestFirstSearch
from tests.support import make_greedy_trap_graph, make_start_goal_config, make_weighted_choice_graph


def test_greedy_selects_by_heuristic_and_can_be_suboptimal() -> None:
    graph = make_greedy_trap_graph()
    result = GreedyBestFirstSearch().search(graph, make_start_goal_config("Greedy Best-First Search", "A", "G", heuristic_type="haversine"))

    assert result.found is True
    assert result.final_path == ("A", "B", "G")
    assert result.steps[0].h_cost is not None
    assert result.steps[-1].g_cost is not None
    assert result.total_cost > 0


def test_greedy_zero_heuristic_and_no_route() -> None:
    graph = make_weighted_choice_graph()
    zero_result = GreedyBestFirstSearch().search(graph, make_start_goal_config("Greedy Best-First Search", "A", "G", heuristic_type="zero"))
    assert zero_result.found is True
    assert zero_result.final_path[0] == "A"

    blocked_graph = make_weighted_choice_graph()
    blocked_graph["A"]["B"]["blocked"] = True
    blocked_graph["B"]["G"]["blocked"] = True
    blocked_graph["A"]["C"]["blocked"] = True
    blocked_graph["C"]["D"]["blocked"] = True
    blocked_graph["D"]["G"]["blocked"] = True
    no_route = GreedyBestFirstSearch().search(blocked_graph, make_start_goal_config("Greedy Best-First Search", "A", "G"))
    assert no_route.found is False
    assert no_route.final_path == ()
"""Phase 1 placeholder for Greedy Best-First Search tests."""
