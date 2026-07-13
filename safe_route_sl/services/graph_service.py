"""Graph loading and validation helpers for SafeRouteSL."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import networkx as nx

from models.graph_models import Location, Road
from utils.constants import SUPPORTED_LOCATION_TYPES
from utils.exceptions import DataValidationError, GraphValidationError


def parse_bool(value: object, field_name: str) -> bool:
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()

    if normalized in {"true", "1", "yes"}:
        return True

    if normalized in {"false", "0", "no"}:
        return False

    raise DataValidationError(f"Invalid Boolean value for {field_name}: {value!r}")


def _ensure_file_exists(file_path: Path) -> None:
    if not file_path.exists():
        raise DataValidationError(f"File does not exist: {file_path}")
    if file_path.is_dir():
        raise DataValidationError(f"Expected a file but found a directory: {file_path}")
    if not file_path.read_text(encoding="utf-8").strip():
        raise DataValidationError(f"File is empty: {file_path}")


def _require_columns(field_names: list[str] | None, required: set[str], file_path: Path) -> None:
    if not field_names:
        raise DataValidationError(f"Missing header row in file: {file_path}")

    missing = required - set(field_names)
    if missing:
        raise DataValidationError(
            f"Missing required columns in {file_path.name}: {', '.join(sorted(missing))}"
        )


def _parse_int(value: Any, field_name: str, row_number: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise DataValidationError(
            f"Invalid integer for {field_name} at row {row_number}: {value!r}"
        ) from exc


def _parse_float(value: Any, field_name: str, row_number: int) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise DataValidationError(
            f"Invalid number for {field_name} at row {row_number}: {value!r}"
        ) from exc


def load_locations(file_path: Path) -> dict[str, Location]:
    _ensure_file_exists(file_path)

    locations: dict[str, Location] = {}
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _require_columns(
            reader.fieldnames,
            {"id", "name", "short_name", "type", "latitude", "longitude", "capacity", "available", "description"},
            file_path,
        )

        for row_number, row in enumerate(reader, start=2):
            if not row:
                continue

            node_id = (row.get("id") or "").strip()
            if not node_id:
                raise DataValidationError(f"Missing location id at row {row_number}")
            if node_id in locations:
                raise DataValidationError(f"Duplicate location id {node_id!r} at row {row_number}")

            latitude = _parse_float(row.get("latitude"), f"latitude for location {node_id}", row_number)
            longitude = _parse_float(row.get("longitude"), f"longitude for location {node_id}", row_number)
            capacity = _parse_int(row.get("capacity"), f"capacity for location {node_id}", row_number)
            available = parse_bool(row.get("available"), f"available for location {node_id}")

            locations[node_id] = Location(
                id=node_id,
                name=(row.get("name") or "").strip(),
                short_name=(row.get("short_name") or "").strip(),
                location_type=(row.get("type") or "").strip(),
                latitude=latitude,
                longitude=longitude,
                capacity=capacity,
                available=available,
                description=(row.get("description") or "").strip(),
            )

    return locations


def load_roads(file_path: Path) -> list[Road]:
    _ensure_file_exists(file_path)

    roads: list[Road] = []
    seen_pairs: set[tuple[str, str]] = set()
    with file_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        _require_columns(
            reader.fieldnames,
            {"source", "target", "road_name", "distance_km", "travel_time_min", "flood_risk", "road_condition", "blocked"},
            file_path,
        )

        for row_number, row in enumerate(reader, start=2):
            if not row:
                continue

            source = (row.get("source") or "").strip()
            target = (row.get("target") or "").strip()
            if not source or not target:
                raise DataValidationError(f"Missing road endpoints at row {row_number}")

            road_key = tuple(sorted((source, target)))
            if road_key in seen_pairs:
                raise DataValidationError(
                    f"Duplicate road definition between {source!r} and {target!r} at row {row_number}"
                )
            seen_pairs.add(road_key)

            roads.append(
                Road(
                    source=source,
                    target=target,
                    road_name=(row.get("road_name") or "").strip(),
                    distance_km=_parse_float(row.get("distance_km"), f"distance_km for road {source}-{target}", row_number),
                    travel_time_min=_parse_float(
                        row.get("travel_time_min"), f"travel_time_min for road {source}-{target}", row_number
                    ),
                    flood_risk=_parse_int(row.get("flood_risk"), f"flood_risk for road {source}-{target}", row_number),
                    road_condition=(row.get("road_condition") or "").strip(),
                    blocked=parse_bool(row.get("blocked"), f"blocked for road {source}-{target}"),
                )
            )

    return roads


def build_graph(locations: dict[str, Location], roads: list[Road]) -> nx.Graph:
    graph = nx.Graph()

    for location in locations.values():
        graph.add_node(
            location.id,
            id=location.id,
            name=location.name,
            short_name=location.short_name,
            location_type=location.location_type,
            latitude=location.latitude,
            longitude=location.longitude,
            capacity=location.capacity,
            available=location.available,
            description=location.description,
        )

    for road in roads:
        if road.source not in locations or road.target not in locations:
            raise DataValidationError(
                f"Road {road.source!r} -> {road.target!r} references an unknown location"
            )
        if road.source == road.target:
            raise DataValidationError(f"Road {road.source!r} -> {road.target!r} cannot be a self-loop")

        graph.add_edge(
            road.source,
            road.target,
            road_name=road.road_name,
            distance_km=road.distance_km,
            travel_time_min=road.travel_time_min,
            flood_risk=road.flood_risk,
            road_condition=road.road_condition,
            blocked=road.blocked,
        )

    return graph


def load_graph(locations_path: Path, roads_path: Path) -> nx.Graph:
    locations = load_locations(locations_path)
    roads = load_roads(roads_path)
    return build_graph(locations, roads)


def get_edge_data(graph: nx.Graph, source: str, target: str) -> dict[str, Any]:
    if not graph.has_edge(source, target):
        raise DataValidationError(f"Edge does not exist between {source!r} and {target!r}")
    return dict(graph.get_edge_data(source, target) or {})


def get_traversable_neighbors(graph: nx.Graph, node_id: str) -> list[str]:
    if node_id not in graph:
        raise DataValidationError(f"Unknown node: {node_id!r}")

    neighbors: list[str] = []
    for neighbor in graph.neighbors(node_id):
        edge_data = graph.get_edge_data(node_id, neighbor) or {}
        if not edge_data.get("blocked", False):
            neighbors.append(neighbor)
    return sorted(neighbors)


def create_traversable_graph(graph: nx.Graph) -> nx.Graph:
    traversable = graph.copy(as_view=False)
    blocked_edges = [
        (source, target)
        for source, target, edge_data in traversable.edges(data=True)
        if edge_data.get("blocked", False)
    ]
    traversable.remove_edges_from(blocked_edges)
    return traversable


def get_available_goal_nodes(graph: nx.Graph) -> list[str]:
    allowed_types = {"shelter", "hospital", "school", "community_hall", "temple", "relief_centre"}
    goal_nodes = [
        node_id
        for node_id, node_data in graph.nodes(data=True)
        if node_data.get("available", False) and node_data.get("location_type") in allowed_types
    ]
    return sorted(goal_nodes)
