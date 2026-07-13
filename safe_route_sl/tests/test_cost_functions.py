"""Cost-function tests for SafeRouteSL."""

from __future__ import annotations

import pytest

from utils.constants import BALANCED_MODE, DISTANCE_MODE, SAFETY_MODE, TIME_MODE
from utils.cost_functions import calculate_edge_cost, create_networkx_weight_function
from utils.exceptions import DataValidationError, InvalidOptimizationModeError


EDGE = {
	"distance_km": 2.0,
	"travel_time_min": 6.0,
	"flood_risk": 3,
	"road_condition": "poor",
	"blocked": False,
}


def test_calculate_edge_cost_for_supported_modes() -> None:
	assert calculate_edge_cost(EDGE, DISTANCE_MODE, risk_weight=4.0) == 2.0
	assert calculate_edge_cost(EDGE, TIME_MODE, risk_weight=4.0) == 6.0
	assert calculate_edge_cost(EDGE, SAFETY_MODE, risk_weight=4.0) == 20.0
	assert calculate_edge_cost(EDGE, BALANCED_MODE, risk_weight=4.0) == 23.0


def test_blocked_roads_return_infinity() -> None:
	blocked_edge = dict(EDGE, blocked=True)
	assert calculate_edge_cost(blocked_edge, BALANCED_MODE, risk_weight=4.0) == float("inf")


def test_reject_invalid_cost_inputs() -> None:
	with pytest.raises(ValueError):
		calculate_edge_cost(EDGE, BALANCED_MODE, risk_weight=-1.0)

	with pytest.raises(InvalidOptimizationModeError):
		calculate_edge_cost(EDGE, "unknown", risk_weight=4.0)

	with pytest.raises(DataValidationError):
		calculate_edge_cost(
			{"travel_time_min": 6.0, "flood_risk": 3, "road_condition": "poor", "blocked": False},
			BALANCED_MODE,
		)

	with pytest.raises(DataValidationError):
		calculate_edge_cost(
			{"distance_km": 2.0, "travel_time_min": 6.0, "flood_risk": 3, "road_condition": "mystery", "blocked": False},
			BALANCED_MODE,
		)


def test_networkx_weight_function_wraps_cost() -> None:
	weight_function = create_networkx_weight_function(BALANCED_MODE, 4.0)
	assert weight_function("A", "B", EDGE) == 23.0
