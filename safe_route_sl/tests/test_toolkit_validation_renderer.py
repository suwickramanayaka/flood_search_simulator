"""Tests for human-readable toolkit validation presentation."""

from __future__ import annotations

import networkx as nx

from services.toolkit_validation_service import ToolkitValidationRecord
from visualizations.toolkit_validation_renderer import (
    build_validation_dataframe,
    format_validation_path,
    prepare_validation_table_rows,
)


def _record() -> ToolkitValidationRecord:
    return ToolkitValidationRecord(
        algorithm_name="Breadth-First Search",
        custom_path=("A", "B"),
        toolkit_path=("A", "C", "B"),
        custom_cost=4.0,
        toolkit_cost=4.0,
        custom_path_edges=1,
        toolkit_path_edges=2,
        validation_status="Failed",
        validation_message="edge count differs",
        toolkit_name="NetworkX unweighted shortest path",
        optimality_scope="Minimum edge-count validation",
        error_message="edge count differs",
    )


def test_human_readable_paths_and_ordered_table_rows() -> None:
    graph = nx.Graph()
    graph.add_node("A", name="Millaniya Village")
    graph.add_node("B", name="School Evacuation Centre")
    graph.add_node("C", name="Temple Shelter")
    record = _record()

    rows = prepare_validation_table_rows((record,), graph)
    dataframe = build_validation_dataframe((record,), graph)

    assert format_validation_path(graph, record.custom_path) == (
        "Millaniya Village → School Evacuation Centre"
    )
    assert rows[0]["Toolkit path"] == (
        "Millaniya Village → Temple Shelter → School Evacuation Centre"
    )
    assert rows[0]["Custom cost"] == "4.00"
    assert rows[0]["Status"] == "Failed"
    assert dataframe["Algorithm"].tolist() == ["Breadth-First Search"]


def test_empty_paths_and_infinite_costs_are_readable() -> None:
    graph = nx.Graph()
    record = ToolkitValidationRecord(
        algorithm_name="A* Search",
        custom_path=(),
        toolkit_path=(),
        custom_cost=float("inf"),
        toolkit_cost=float("inf"),
        custom_path_edges=0,
        toolkit_path_edges=0,
        validation_status="No route",
        validation_message="Neither found a route",
        toolkit_name="NetworkX A*",
        optimality_scope="Conditional",
    )

    row = prepare_validation_table_rows((record,), graph)[0]

    assert row["Custom path"] == "No route found"
    assert row["Toolkit path"] == "No route found"
    assert row["Custom cost"] == "No finite route"
    assert row["Toolkit cost"] == "No finite route"
