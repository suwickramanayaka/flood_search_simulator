"""Comparison service tests for SafeRouteSL."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from models.search_models import SearchResult, SearchStep
from services.comparison_service import AlgorithmComparisonRecord, compare_algorithms
from services import comparison_service
from tests.support import make_replacement_graph, make_start_goal_config
from utils.constants import BALANCED_MODE, SEARCH_ALGORITHM_LABELS
from utils.exceptions import SafeRouteError


def _dummy_result(algorithm_name: str) -> SearchResult:
    step = SearchStep(
        step_number=0,
        event_type="initialize",
        current_node=None,
        frontier_nodes=("A",),
        explored_nodes=(),
        current_path=("A",),
        nodes_expanded=0,
        nodes_generated=1,
        maximum_frontier_size=1,
        explanation="dummy",
    )
    return SearchResult(
        algorithm_name=algorithm_name,
        toolkit_source="Custom Python",
        found=True,
        start_node="A",
        goal_node="G",
        final_path=("A", "B"),
        total_cost=1.0,
        nodes_expanded=1,
        nodes_generated=1,
        maximum_frontier_size=1,
        path_length_edges=1,
        repeated_state_skips=0,
        execution_time_ms=1.0,
        steps=(step,),
        optimality_expected=True,
        completeness_expected=True,
    )


def test_compare_algorithms_returns_all_algorithms_in_order() -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G", optimization_mode=BALANCED_MODE)

    records = compare_algorithms(graph, configuration)

    assert tuple(record.algorithm_name for record in records) == SEARCH_ALGORITHM_LABELS
    assert len(records) == 5


def test_compare_algorithms_preserves_requested_order(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G", optimization_mode=BALANCED_MODE)

    def fake_run_search(graph_arg, configuration_arg):
        return _dummy_result(configuration_arg.algorithm)

    monkeypatch.setattr(comparison_service, "run_search", fake_run_search)

    records = compare_algorithms(graph, configuration, ("A* Search", "Breadth-First Search"))

    assert [record.algorithm_name for record in records] == ["A* Search", "Breadth-First Search"]
    assert all(isinstance(record.path, tuple) for record in records)


def test_compare_algorithms_uses_same_configuration_and_records_failures(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = make_replacement_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G", optimization_mode=BALANCED_MODE)
    seen_configurations = []

    def fake_run_search(graph_arg, configuration_arg):
        seen_configurations.append(configuration_arg)
        if configuration_arg.algorithm == "Depth-First Search":
            raise SafeRouteError("planned failure")
        return _dummy_result(configuration_arg.algorithm)

    monkeypatch.setattr(comparison_service, "run_search", fake_run_search)

    records = compare_algorithms(graph, configuration, ("Breadth-First Search", "Depth-First Search"))

    assert len(records) == 2
    assert records[0].found is True
    assert records[1].found is False
    assert records[1].error_message == "planned failure"
    assert all(record.start_node == "A" for record in seen_configurations)
    assert all(record.goal_node == "G" for record in seen_configurations)
    assert all(record.optimization_mode == BALANCED_MODE for record in seen_configurations)


def test_comparison_records_are_immutable() -> None:
    record = AlgorithmComparisonRecord(
        algorithm_name="Breadth-First Search",
        found=True,
        path=("A", "B"),
        total_cost=1.0,
        nodes_expanded=1,
        nodes_generated=2,
        maximum_frontier_size=3,
        execution_time_ms=4.0,
        path_length_edges=1,
        optimality_expected=False,
        completeness_expected=True,
    )

    with pytest.raises(FrozenInstanceError):
        record.algorithm_name = "Depth-First Search"  # type: ignore[misc]
