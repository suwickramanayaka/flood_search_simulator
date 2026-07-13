"""Tests for custom-versus-NetworkX toolkit validation."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from algorithms import simpleai_adapter
from services import toolkit_validation_service
from services.toolkit_validation_service import validate_against_toolkits
from tests.support import (
    add_edge,
    make_unweighted_choice_graph,
    make_weighted_choice_graph,
    make_start_goal_config,
)
from utils.constants import BALANCED_MODE, DISTANCE_MODE
from utils.exceptions import GraphValidationError


def test_bfs_equal_edge_validation_passes() -> None:
    graph = make_unweighted_choice_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")

    record = validate_against_toolkits(
        graph,
        configuration,
        ("Breadth-First Search",),
    )[0]

    assert record.validation_status in {"Passed", "Passed with alternate equal path"}
    assert record.custom_path_edges == record.toolkit_path_edges == 2


def test_bfs_alternate_equal_length_path_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = make_unweighted_choice_graph()
    add_edge(graph, "C", "G", distance_km=1.0)
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    monkeypatch.setattr(
        toolkit_validation_service,
        "run_networkx_bfs_shortest_path",
        lambda graph_arg, start, goal: ("A", "C", "G"),
    )

    record = validate_against_toolkits(
        graph,
        configuration,
        ("Breadth-First Search",),
    )[0]

    assert record.custom_path != record.toolkit_path
    assert record.custom_path_edges == record.toolkit_path_edges
    assert record.validation_status == "Passed with alternate equal path"


def test_ucs_matching_cost_passes() -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config(
        "Uniform-Cost Search",
        "A",
        "G",
        optimization_mode=DISTANCE_MODE,
    )

    record = validate_against_toolkits(
        graph,
        configuration,
        ("Uniform-Cost Search",),
    )[0]

    assert record.validation_status == "Passed"
    assert record.custom_cost == pytest.approx(record.toolkit_cost)


def test_ucs_cost_mismatch_is_detected(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config(
        "Uniform-Cost Search",
        "A",
        "G",
        optimization_mode=DISTANCE_MODE,
    )
    original_adapter = toolkit_validation_service.run_networkx_dijkstra

    def mismatched_adapter(graph_arg, configuration_arg):
        path, cost = original_adapter(graph_arg, configuration_arg)
        return path, cost + 1.0

    monkeypatch.setattr(toolkit_validation_service, "run_networkx_dijkstra", mismatched_adapter)

    record = validate_against_toolkits(
        graph,
        configuration,
        ("Uniform-Cost Search",),
    )[0]

    assert record.validation_status == "Failed"
    assert record.error_message is not None


def test_astar_zero_heuristic_is_validated_as_ucs_behavior() -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config(
        "A* Search",
        "A",
        "G",
        optimization_mode=DISTANCE_MODE,
        heuristic_type="zero",
    )

    record = validate_against_toolkits(graph, configuration, ("A* Search",))[0]

    assert record.validation_status == "Passed"
    assert "behaves like UCS" in record.validation_message
    assert "Zero heuristic" in record.optimality_scope


def test_astar_distance_haversine_validation_passes() -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config(
        "A* Search",
        "A",
        "G",
        optimization_mode=DISTANCE_MODE,
        heuristic_type="haversine",
    )

    record = validate_against_toolkits(graph, configuration, ("A* Search",))[0]

    assert record.validation_status == "Passed"
    assert record.custom_cost == pytest.approx(record.toolkit_cost)
    assert "Distance-mode Haversine" in record.optimality_scope


def test_astar_balanced_haversine_is_conditional_not_passed() -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config(
        "A* Search",
        "A",
        "G",
        optimization_mode=BALANCED_MODE,
        heuristic_type="haversine",
    )

    record = validate_against_toolkits(graph, configuration, ("A* Search",))[0]

    assert record.validation_status == "Conditional"
    assert "educational estimate" in record.validation_message
    assert "Conditional" in record.optimality_scope


def test_no_route_is_handled_safely_for_all_default_validations() -> None:
    graph = make_weighted_choice_graph()
    for source, target in graph.edges():
        graph[source][target]["blocked"] = True
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")

    records = validate_against_toolkits(graph, configuration)

    assert tuple(record.validation_status for record in records) == (
        "No route",
        "No route",
        "No route",
    )
    assert all(record.error_message is None for record in records)


def test_toolkit_exception_is_returned_as_readable_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config("Uniform-Cost Search", "A", "G")

    def fail_adapter(graph_arg, configuration_arg):
        raise GraphValidationError("reference unavailable")

    monkeypatch.setattr(toolkit_validation_service, "run_networkx_dijkstra", fail_adapter)

    record = validate_against_toolkits(
        graph,
        configuration,
        ("Uniform-Cost Search",),
    )[0]

    assert record.validation_status == "Failed"
    assert record.error_message == "NetworkX validation failed: reference unavailable"
    assert "GraphValidationError" not in record.error_message


def test_validation_does_not_mutate_graph_or_configuration() -> None:
    graph = make_weighted_choice_graph()
    original_graph = graph.copy()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    original_configuration = configuration

    validate_against_toolkits(graph, configuration)

    assert nx.utils.graphs_equal(graph, original_graph)
    assert configuration is original_configuration


def test_validation_order_is_deterministic_and_custom_search_runs_once_per_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    requested = ("A* Search", "Breadth-First Search", "Uniform-Cost Search")
    original_run_search = toolkit_validation_service.run_search
    calls: list[str] = []

    def spy_run_search(graph_arg, configuration_arg):
        calls.append(configuration_arg.algorithm)
        return original_run_search(graph_arg, configuration_arg)

    monkeypatch.setattr(toolkit_validation_service, "run_search", spy_run_search)

    records = validate_against_toolkits(graph, configuration, requested)

    assert tuple(record.algorithm_name for record in records) == requested
    assert calls == list(requested)


def test_algorithm_without_reference_adapter_reports_toolkit_unavailable() -> None:
    graph = make_weighted_choice_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")

    record = validate_against_toolkits(graph, configuration, ("Depth-First Search",))[0]

    assert record.validation_status == "Toolkit unavailable"
    assert record.custom_path == ()
    assert record.error_message is None


def test_simpleai_available_and_unavailable_statuses(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(simpleai_adapter, "simpleai", None)
    assert simpleai_adapter.is_simpleai_available() is False
    assert simpleai_adapter.get_simpleai_status() == "SimpleAI unavailable (optional)"

    class FakeSimpleAI:
        __version__ = "test-version"

    monkeypatch.setattr(simpleai_adapter, "simpleai", FakeSimpleAI())
    assert simpleai_adapter.is_simpleai_available() is True
    assert simpleai_adapter.get_simpleai_status() == "SimpleAI available (test-version)"


def test_toolkit_page_and_primary_simulator_wiring_remain_separate() -> None:
    root = Path(__file__).resolve().parents[1]
    toolkit_page = (root / "pages" / "4_Toolkit_Validation.py").read_text(encoding="utf-8")
    simulation_page = (root / "pages" / "1_Interactive_Simulation.py").read_text(encoding="utf-8")
    search_service = (root / "services" / "search_service.py").read_text(encoding="utf-8")
    algorithm_sources = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (root / "algorithms").glob("*.py")
    )

    assert toolkit_page.count("validate_against_toolkits(") == 1
    assert "from services.toolkit_validation_service import validate_against_toolkits" in toolkit_page
    assert "toolkit_validation" not in simulation_page.lower()
    assert '"Breadth-First Search": BreadthFirstSearch' in search_service
    assert '"Uniform-Cost Search": UniformCostSearch' in search_service
    assert '"A* Search": AStarSearch' in search_service
    assert "import streamlit" not in algorithm_sources
