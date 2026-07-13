"""Cost function helpers for SafeRouteSL."""

from __future__ import annotations

from typing import Any

from utils.constants import (
	BALANCED_MODE,
	DISTANCE_MODE,
	ROAD_CONDITION_PENALTIES,
	SAFETY_MODE,
	TIME_MODE,
)
from utils.exceptions import DataValidationError, InvalidOptimizationModeError


def _require_edge_field(edge_data: dict[str, Any], field_name: str) -> Any:
	if field_name not in edge_data:
		raise DataValidationError(f"Missing edge attribute '{field_name}'")
	return edge_data[field_name]


def calculate_edge_cost(
	edge_data: dict[str, Any],
	optimization_mode: str,
	risk_weight: float = 4.0,
) -> float:
	if risk_weight < 0:
		raise ValueError("risk_weight cannot be negative")

	blocked = bool(edge_data.get("blocked", False))
	if blocked:
		return float("inf")

	distance_km = float(_require_edge_field(edge_data, "distance_km"))
	travel_time_min = float(_require_edge_field(edge_data, "travel_time_min"))
	flood_risk = int(_require_edge_field(edge_data, "flood_risk"))
	road_condition = _require_edge_field(edge_data, "road_condition")

	if road_condition not in ROAD_CONDITION_PENALTIES:
		raise DataValidationError(f"Unsupported road condition: {road_condition!r}")

	if optimization_mode == DISTANCE_MODE:
		cost = distance_km
	elif optimization_mode == TIME_MODE:
		cost = travel_time_min
	elif optimization_mode == SAFETY_MODE:
		cost = distance_km + (risk_weight * flood_risk) + ROAD_CONDITION_PENALTIES[road_condition]
	elif optimization_mode == BALANCED_MODE:
		cost = distance_km + (0.5 * travel_time_min) + (risk_weight * flood_risk) + ROAD_CONDITION_PENALTIES[road_condition]
	else:
		raise InvalidOptimizationModeError(f"Unsupported optimization mode: {optimization_mode!r}")

	if cost < 0:
		raise DataValidationError("Calculated edge cost cannot be negative")

	return float(cost)


def create_networkx_weight_function(optimization_mode: str, risk_weight: float):
	def weight_function(source: str, target: str, edge_data: dict[str, Any]) -> float:
		return calculate_edge_cost(
			edge_data=edge_data,
			optimization_mode=optimization_mode,
			risk_weight=risk_weight,
		)

	return weight_function

