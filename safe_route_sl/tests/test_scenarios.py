"""Scenario loading and application tests for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.graph_service import load_graph
from services.scenario_service import apply_scenario, apply_scenario_by_id, get_scenario, load_scenarios
from utils.exceptions import DataValidationError, InvalidScenarioError, ScenarioNotFoundError


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def test_load_scenarios_and_get_scenario() -> None:
    scenarios = load_scenarios(DATA_DIR / "scenarios.json")

    assert len(scenarios) == 5
    assert list(scenarios) == [
        "normal_conditions",
        "bridge_flooded",
        "severe_flooding",
        "shelter_unavailable",
        "multiple_equal_cost_paths",
    ]

    scenario = get_scenario(scenarios, "bridge_flooded")
    assert scenario.name == "Bridge Flooded"

    with pytest.raises(ScenarioNotFoundError):
        get_scenario(scenarios, "missing_scenario")


def test_apply_scenario_does_not_mutate_base_graph() -> None:
    base_graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")
    scenarios = load_scenarios(DATA_DIR / "scenarios.json")

    original_blocked = base_graph["K"]["L"]["blocked"]
    scenario_graph = apply_scenario(base_graph, scenarios["bridge_flooded"])

    assert base_graph["K"]["L"]["blocked"] is original_blocked
    assert scenario_graph["K"]["L"]["blocked"] is True
    assert scenario_graph.graph["scenario_id"] == "bridge_flooded"
    assert scenario_graph.graph["scenario_name"] == "Bridge Flooded"
    assert scenario_graph.graph["scenario_description"]


def test_apply_scenario_by_id_and_node_override() -> None:
    base_graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")
    scenarios = load_scenarios(DATA_DIR / "scenarios.json")

    scenario_graph = apply_scenario_by_id(base_graph, scenarios, "shelter_unavailable")

    assert scenario_graph.nodes["H"]["available"] is False
    assert scenario_graph.nodes["H"]["capacity"] == 0
    assert base_graph.nodes["H"]["available"] is True


def test_scenarios_are_independent() -> None:
    base_graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")
    scenarios = load_scenarios(DATA_DIR / "scenarios.json")

    first = apply_scenario(base_graph, scenarios["bridge_flooded"])
    second = apply_scenario(base_graph, scenarios["severe_flooding"])

    assert first["K"]["L"]["blocked"] is True
    assert second["K"]["L"]["blocked"] is False
    assert base_graph["K"]["L"]["blocked"] is False


def test_invalid_scenario_references_raise(tmp_path: Path) -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")

    invalid_edge = tmp_path / "invalid_edge.json"
    invalid_edge.write_text(
        '[{"id": "bad", "name": "Bad", "description": "bad", "edge_overrides": [{"source": "X", "target": "Y"}], "node_overrides": []}]',
        encoding="utf-8",
    )
    scenarios = load_scenarios(invalid_edge)
    with pytest.raises(InvalidScenarioError):
        apply_scenario_by_id(graph, scenarios, "bad")

    invalid_node = tmp_path / "invalid_node.json"
    invalid_node.write_text(
        '[{"id": "bad_node", "name": "Bad Node", "description": "bad", "edge_overrides": [], "node_overrides": [{"id": "Z"}]}]',
        encoding="utf-8",
    )
    scenarios = load_scenarios(invalid_node)
    with pytest.raises(InvalidScenarioError):
        apply_scenario_by_id(graph, scenarios, "bad_node")


def test_load_scenarios_rejects_duplicates(tmp_path: Path) -> None:
    path = tmp_path / "dup.json"
    path.write_text(
        '[{"id": "dup", "name": "One", "description": "d", "edge_overrides": [], "node_overrides": []}, {"id": "dup", "name": "Two", "description": "d", "edge_overrides": [], "node_overrides": []}]',
        encoding="utf-8",
    )

    with pytest.raises(DataValidationError):
        load_scenarios(path)

