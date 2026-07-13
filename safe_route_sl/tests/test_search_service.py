"""Search service tests for SafeRouteSL."""

from __future__ import annotations

import copy

import pytest

from algorithms.astar import AStarSearch
from models.configuration import SearchConfiguration
from services import search_service
from services.search_service import get_algorithm, get_supported_algorithms, run_search
from tests.support import make_replacement_graph, make_start_goal_config, make_weighted_choice_graph
from utils.constants import DISTANCE_MODE
from utils.exceptions import DataValidationError, GraphValidationError, UnavailableGoalError


def _graph_snapshot(graph):
    return {
        "graph": dict(graph.graph),
        "nodes": {node_id: dict(data) for node_id, data in graph.nodes(data=True)},
        "edges": {tuple(sorted((source, target))): dict(data) for source, target, data in graph.edges(data=True)},
    }


def test_algorithm_registry_returns_expected_implementation() -> None:
    assert isinstance(get_algorithm("A* Search"), AStarSearch)
    assert get_supported_algorithms() == (
        "Breadth-First Search",
        "Depth-First Search",
        "Uniform-Cost Search",
        "Greedy Best-First Search",
        "A* Search",
    )


def test_unsupported_algorithm_raises_domain_error() -> None:
    with pytest.raises(DataValidationError):
        get_algorithm("Not an algorithm")


def test_run_search_returns_valid_result_and_invokes_result_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config(
        "A* Search",
        "A",
        "G",
        optimization_mode=DISTANCE_MODE,
        heuristic_type="zero",
    )
    calls: list[tuple[object, object, object]] = []

    def spy(graph_arg, result_arg, configuration_arg):
        calls.append((graph_arg, result_arg, configuration_arg))

    monkeypatch.setattr(search_service, "validate_search_result", spy)

    result = run_search(graph, configuration)

    assert result.found is True
    assert result.final_path == ("A", "C", "B", "G")
    assert calls and calls[0][1] == result


def test_run_search_rejects_invalid_start_goal_and_goal_availability() -> None:
    graph = make_weighted_choice_graph()

    with pytest.raises(GraphValidationError):
        run_search(
            graph,
            make_start_goal_config("A* Search", "Z", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero"),
        )

    with pytest.raises(GraphValidationError):
        run_search(
            graph,
            make_start_goal_config("A* Search", "A", "Z", optimization_mode=DISTANCE_MODE, heuristic_type="zero"),
        )


def test_run_search_rejects_unavailable_goal() -> None:
    from tests.support import load_project_dataset_scenario_graph

    graph = load_project_dataset_scenario_graph("shelter_unavailable")
    configuration = SearchConfiguration(
        algorithm="A* Search",
        start_node="A",
        goal_node="H",
        optimization_mode=DISTANCE_MODE,
        heuristic_type="zero",
    )

    with pytest.raises(UnavailableGoalError):
        run_search(graph, configuration)


def test_run_search_does_not_mutate_graph() -> None:
    graph = make_replacement_graph()
    before = _graph_snapshot(copy.deepcopy(graph))

    run_search(
        graph,
        make_start_goal_config("A* Search", "A", "G", optimization_mode=DISTANCE_MODE, heuristic_type="zero"),
    )

    after = _graph_snapshot(graph)
    assert after == before
