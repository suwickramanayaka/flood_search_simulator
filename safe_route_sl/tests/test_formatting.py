"""Formatting helper tests for SafeRouteSL."""

from __future__ import annotations

from utils.constants import BALANCED_MODE, DISTANCE_MODE, TIME_MODE
from utils.formatting import format_cost, format_node_name, format_path, humanize_identifier
from tests.support import load_project_dataset_graph


def test_path_is_converted_to_names_and_empty_path_is_handled() -> None:
    graph = load_project_dataset_graph()

    formatted = format_path(graph, ("A", "D", "H"))
    assert "Millaniya Village" in formatted
    assert "School Evacuation Centre" in formatted
    assert format_path(graph, ()) == "No path available"


def test_infinity_and_units_are_formatted_correctly() -> None:
    assert format_cost(float("inf"), DISTANCE_MODE) == "No finite route"
    assert format_cost(12.345, DISTANCE_MODE) == "12.35 km"
    assert format_cost(12.345, TIME_MODE) == "12.35 min"
    assert format_cost(12.345, BALANCED_MODE) == "12.35"


def test_identifiers_and_node_names_are_humanized() -> None:
    graph = load_project_dataset_graph()

    assert humanize_identifier("bridge_flooded") == "Bridge Flooded"
    assert humanize_identifier("balanced") == "Balanced"
    assert format_node_name(graph, "A") == "Millaniya Village"
