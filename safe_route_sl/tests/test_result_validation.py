"""Search result validation tests for SafeRouteSL."""

from __future__ import annotations

from dataclasses import replace

import pytest

from algorithms.astar import AStarSearch
from algorithms.breadth_first import BreadthFirstSearch
from services.validation_service import validate_search_result
from tests.support import make_replacement_graph, make_start_goal_config, make_weighted_choice_graph
from utils.constants import DISTANCE_MODE
from utils.exceptions import GraphValidationError


def test_valid_path_passes_validation() -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")
    result = AStarSearch().search(graph, configuration)

    validate_search_result(graph, result, configuration)


def test_wrong_start_fails_validation() -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")
    result = AStarSearch().search(graph, configuration)
    invalid_result = replace(result, final_path=("B", "C", "B", "G"))

    with pytest.raises(GraphValidationError):
        validate_search_result(graph, invalid_result, configuration)


def test_wrong_goal_fails_validation() -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")
    result = AStarSearch().search(graph, configuration)
    invalid_result = replace(result, final_path=("A", "C", "B", "C"), total_cost=result.total_cost)

    with pytest.raises(GraphValidationError):
        validate_search_result(graph, invalid_result, configuration)


def test_missing_and_blocked_edges_fail_validation() -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")
    result = AStarSearch().search(graph, configuration)

    missing_edge_result = replace(result, final_path=("A", "G"), path_length_edges=1, total_cost=1.0)
    with pytest.raises(GraphValidationError):
        validate_search_result(graph, missing_edge_result, configuration)

    blocked_graph = make_weighted_choice_graph()
    blocked_graph["C"]["D"]["blocked"] = True
    blocked_result = AStarSearch().search(make_weighted_choice_graph(), configuration)
    with pytest.raises(GraphValidationError):
        validate_search_result(blocked_graph, blocked_result, configuration)


def test_incorrect_total_cost_non_sequential_steps_and_invalid_metrics_fail_validation() -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero")
    result = AStarSearch().search(graph, configuration)

    wrong_cost = replace(result, total_cost=result.total_cost + 1.0)
    with pytest.raises(GraphValidationError):
        validate_search_result(graph, wrong_cost, configuration)

    bad_steps = list(result.steps)
    bad_steps[1] = replace(bad_steps[1], step_number=7)
    bad_sequence = replace(result, steps=tuple(bad_steps))
    with pytest.raises(GraphValidationError):
        validate_search_result(graph, bad_sequence, configuration)

    bad_metrics = replace(result, nodes_expanded=-1)
    with pytest.raises(GraphValidationError):
        validate_search_result(graph, bad_metrics, configuration)


def test_valid_and_invalid_no_route_results() -> None:
    graph = make_weighted_choice_graph()
    for source, target in list(graph.edges()):
        graph[source][target]["blocked"] = True

    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    failure_result = BreadthFirstSearch().search(graph, configuration)
    validate_search_result(graph, failure_result, configuration)

    invalid_failure = replace(failure_result, final_path=("A",), total_cost=0.0)
    with pytest.raises(GraphValidationError):
        validate_search_result(graph, invalid_failure, configuration)
