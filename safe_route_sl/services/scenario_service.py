"""Scenario loading and application helpers for SafeRouteSL."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import networkx as nx

from models.graph_models import EdgeOverride, NodeOverride, Scenario
from services.graph_service import parse_bool
from utils.constants import ROAD_CONDITION_PENALTIES
from utils.exceptions import DataValidationError, InvalidScenarioError, ScenarioNotFoundError


def _require_scenario_file(file_path: Path) -> None:
    if not file_path.exists():
        raise DataValidationError(f"File does not exist: {file_path}")
    if not file_path.read_text(encoding="utf-8").strip():
        raise DataValidationError(f"File is empty: {file_path}")


def _parse_optional_int(value: Any, field_name: str, scenario_id: str) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise DataValidationError(
            f"Invalid integer for {field_name} in scenario {scenario_id!r}: {value!r}"
        ) from exc


def _parse_optional_float(value: Any, field_name: str, scenario_id: str) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise DataValidationError(
            f"Invalid number for {field_name} in scenario {scenario_id!r}: {value!r}"
        ) from exc


def load_scenarios(file_path: Path) -> dict[str, Scenario]:
    _require_scenario_file(file_path)

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DataValidationError(f"Invalid JSON in {file_path.name}: {exc.msg}") from exc

    if not isinstance(payload, list):
        raise DataValidationError(f"Scenario file must contain a JSON array: {file_path}")

    scenarios: dict[str, Scenario] = {}
    for index, item in enumerate(payload, start=1):
        if not isinstance(item, dict):
            raise DataValidationError(f"Invalid scenario entry at index {index}: expected object")

        scenario_id = str(item.get("id", "")).strip()
        if not scenario_id:
            raise DataValidationError(f"Scenario entry at index {index} is missing an id")
        if scenario_id in scenarios:
            raise DataValidationError(f"Duplicate scenario id {scenario_id!r} at index {index}")

        edge_overrides: list[EdgeOverride] = []
        for edge_index, override in enumerate(item.get("edge_overrides", []), start=1):
            if not isinstance(override, dict):
                raise DataValidationError(
                    f"Invalid edge override in scenario {scenario_id!r} at position {edge_index}"
                )

            blocked_value = override.get("blocked")
            blocked = None if blocked_value is None else parse_bool(blocked_value, f"blocked override for scenario {scenario_id}")
            edge_overrides.append(
                EdgeOverride(
                    source=str(override.get("source", "")).strip(),
                    target=str(override.get("target", "")).strip(),
                    blocked=blocked,
                    flood_risk=_parse_optional_int(override.get("flood_risk"), f"flood_risk override for scenario {scenario_id}", scenario_id),
                    distance_km=_parse_optional_float(override.get("distance_km"), f"distance_km override for scenario {scenario_id}", scenario_id),
                    travel_time_min=_parse_optional_float(override.get("travel_time_min"), f"travel_time_min override for scenario {scenario_id}", scenario_id),
                    road_condition=None if override.get("road_condition") is None else str(override.get("road_condition")).strip(),
                )
            )

        node_overrides: list[NodeOverride] = []
        for node_index, override in enumerate(item.get("node_overrides", []), start=1):
            if not isinstance(override, dict):
                raise DataValidationError(
                    f"Invalid node override in scenario {scenario_id!r} at position {node_index}"
                )

            available_value = override.get("available")
            available = None if available_value is None else parse_bool(available_value, f"available override for scenario {scenario_id}")
            node_overrides.append(
                NodeOverride(
                    node_id=str(override.get("id", "")).strip(),
                    available=available,
                    capacity=_parse_optional_int(override.get("capacity"), f"capacity override for scenario {scenario_id}", scenario_id),
                )
            )

        scenarios[scenario_id] = Scenario(
            id=scenario_id,
            name=str(item.get("name", "")).strip(),
            description=str(item.get("description", "")).strip(),
            edge_overrides=tuple(edge_overrides),
            node_overrides=tuple(node_overrides),
        )

    return scenarios


def get_scenario(scenarios: dict[str, Scenario], scenario_id: str) -> Scenario:
    try:
        return scenarios[scenario_id]
    except KeyError as exc:
        raise ScenarioNotFoundError(f"Unknown scenario id: {scenario_id!r}") from exc


def _validate_edge_override(graph: nx.Graph, scenario_id: str, override: EdgeOverride) -> tuple[str, str]:
    if not graph.has_edge(override.source, override.target):
        raise InvalidScenarioError(
            f"Scenario {scenario_id!r} references a missing edge: {override.source!r} -> {override.target!r}"
        )
    return override.source, override.target


def _apply_edge_override(graph: nx.Graph, scenario_id: str, override: EdgeOverride) -> None:
    source, target = _validate_edge_override(graph, scenario_id, override)
    edge_data = graph[source][target]

    if override.blocked is not None:
        edge_data["blocked"] = parse_bool(override.blocked, f"blocked override for edge {source}-{target}")
    if override.flood_risk is not None:
        if not 1 <= override.flood_risk <= 5:
            raise InvalidScenarioError(
                f"Scenario {scenario_id!r} has invalid flood risk for edge {source!r} -> {target!r}: {override.flood_risk!r}"
            )
        edge_data["flood_risk"] = override.flood_risk
    if override.distance_km is not None:
        if override.distance_km <= 0:
            raise InvalidScenarioError(
                f"Scenario {scenario_id!r} has invalid distance for edge {source!r} -> {target!r}: {override.distance_km!r}"
            )
        edge_data["distance_km"] = override.distance_km
    if override.travel_time_min is not None:
        if override.travel_time_min <= 0:
            raise InvalidScenarioError(
                f"Scenario {scenario_id!r} has invalid travel time for edge {source!r} -> {target!r}: {override.travel_time_min!r}"
            )
        edge_data["travel_time_min"] = override.travel_time_min
    if override.road_condition is not None:
        if override.road_condition not in ROAD_CONDITION_PENALTIES:
            raise InvalidScenarioError(
                f"Scenario {scenario_id!r} has unsupported road condition for edge {source!r} -> {target!r}: {override.road_condition!r}"
            )
        edge_data["road_condition"] = override.road_condition


def _apply_node_override(graph: nx.Graph, scenario_id: str, override: NodeOverride) -> None:
    if override.node_id not in graph:
        raise InvalidScenarioError(
            f"Scenario {scenario_id!r} references a missing node: {override.node_id!r}"
        )

    node_data = graph.nodes[override.node_id]
    if override.available is not None:
        node_data["available"] = parse_bool(override.available, f"available override for node {override.node_id}")
    if override.capacity is not None:
        if override.capacity < 0:
            raise InvalidScenarioError(
                f"Scenario {scenario_id!r} has invalid capacity for node {override.node_id!r}: {override.capacity!r}"
            )
        node_data["capacity"] = override.capacity


def apply_scenario(base_graph: nx.Graph, scenario: Scenario) -> nx.Graph:
    scenario_graph = copy.deepcopy(base_graph)
    scenario_graph.graph["scenario_id"] = scenario.id
    scenario_graph.graph["scenario_name"] = scenario.name
    scenario_graph.graph["scenario_description"] = scenario.description

    for edge_override in scenario.edge_overrides:
        _apply_edge_override(scenario_graph, scenario.id, edge_override)

    for node_override in scenario.node_overrides:
        _apply_node_override(scenario_graph, scenario.id, node_override)

    return scenario_graph


def apply_scenario_by_id(base_graph: nx.Graph, scenarios: dict[str, Scenario], scenario_id: str) -> nx.Graph:
    return apply_scenario(base_graph, get_scenario(scenarios, scenario_id))
