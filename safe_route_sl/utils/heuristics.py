"""Heuristic helpers for SafeRouteSL."""

from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Any, Callable

from utils.exceptions import DataValidationError


def haversine_distance(
	lat1: float,
	lon1: float,
	lat2: float,
	lon2: float,
) -> float:
	for field_name, value, lower, upper in (
		("lat1", lat1, -90.0, 90.0),
		("lat2", lat2, -90.0, 90.0),
		("lon1", lon1, -180.0, 180.0),
		("lon2", lon2, -180.0, 180.0),
	):
		if not (lower <= value <= upper):
			raise DataValidationError(f"Invalid coordinate for {field_name}: {value!r}")

	if lat1 == lat2 and lon1 == lon2:
		return 0.0

	earth_radius_km = 6371.0
	delta_lat = radians(lat2 - lat1)
	delta_lon = radians(lon2 - lon1)
	value = (
		sin(delta_lat / 2) ** 2
		+ cos(radians(lat1))
		* cos(radians(lat2))
		* sin(delta_lon / 2) ** 2
	)
	value = min(1.0, max(0.0, value))
	return 2 * earth_radius_km * atan2(sqrt(value), sqrt(1 - value))


def _get_coordinates(graph: Any, node_id: str) -> tuple[float, float]:
	if node_id not in graph:
		raise DataValidationError(f"Unknown node: {node_id!r}")

	node_data = graph.nodes[node_id]
	if "latitude" not in node_data or "longitude" not in node_data:
		raise DataValidationError(f"Missing coordinates for node: {node_id!r}")

	return float(node_data["latitude"]), float(node_data["longitude"])


def calculate_heuristic(
	graph: Any,
	current_node: str,
	goal_node: str,
	heuristic_type: str,
) -> float:
	if heuristic_type == "zero":
		return 0.0
	if heuristic_type != "haversine":
		raise DataValidationError(f"Unsupported heuristic type: {heuristic_type!r}")

	current_lat, current_lon = _get_coordinates(graph, current_node)
	goal_lat, goal_lon = _get_coordinates(graph, goal_node)
	return haversine_distance(current_lat, current_lon, goal_lat, goal_lon)


def create_heuristic_function(graph: Any, goal_node: str, heuristic_type: str) -> Callable[[str], float]:
	def heuristic(node_id: str) -> float:
		return calculate_heuristic(graph, node_id, goal_node, heuristic_type)

	return heuristic

