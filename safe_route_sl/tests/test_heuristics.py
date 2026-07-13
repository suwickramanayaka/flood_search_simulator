"""Heuristic tests for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.graph_service import load_graph
from utils.exceptions import DataValidationError
from utils.heuristics import calculate_heuristic, create_heuristic_function, haversine_distance


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def test_haversine_distance_basic_properties() -> None:
    assert haversine_distance(6.0, 80.0, 6.0, 80.0) == 0.0

    one_degree_north = haversine_distance(0.0, 0.0, 1.0, 0.0)
    assert 110.0 <= one_degree_north <= 112.5
    assert one_degree_north == pytest.approx(haversine_distance(1.0, 0.0, 0.0, 0.0))


def test_haversine_distance_rejects_invalid_coordinates() -> None:
    with pytest.raises(DataValidationError):
        haversine_distance(91.0, 80.0, 6.0, 80.0)

    with pytest.raises(DataValidationError):
        haversine_distance(6.0, 181.0, 6.0, 80.0)


def test_graph_heuristics_support_zero_and_haversine() -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")

    assert calculate_heuristic(graph, "A", "H", "zero") == 0.0
    h_value = calculate_heuristic(graph, "A", "H", "haversine")
    assert h_value > 0

    heuristic = create_heuristic_function(graph, "H", "haversine")
    assert heuristic("A") == pytest.approx(h_value)


def test_graph_heuristics_reject_missing_nodes() -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")

    with pytest.raises(DataValidationError):
        calculate_heuristic(graph, "Z", "H", "haversine")

    graph.remove_node("H")
    with pytest.raises(DataValidationError):
        calculate_heuristic(graph, "A", "H", "haversine")