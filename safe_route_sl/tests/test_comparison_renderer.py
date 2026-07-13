"""Tests for comparison table, chart, and summary preparation."""

from __future__ import annotations

import ast
from pathlib import Path

import networkx as nx
import pytest

from services.comparison_service import AlgorithmComparisonRecord
from visualizations.comparison_renderer import (
    build_comparison_dataframe,
    build_path_edge_chart,
    build_total_cost_chart,
    calculate_tied_minimum,
    excluded_cost_algorithm_names,
    failed_algorithm_names,
    format_comparison_path,
    format_summary_insight,
    prepare_comparison_table_rows,
    prepare_cost_chart_rows,
    prepare_frontier_chart_rows,
    prepare_nodes_expanded_chart_rows,
    prepare_path_edge_chart_rows,
    prepare_runtime_chart_rows,
    prepare_summary_insights,
)


def _record(
    algorithm: str,
    *,
    found: bool = True,
    path: tuple[str, ...] = ("A", "B"),
    cost: float = 7.7,
    expanded: int = 4,
    generated: int = 6,
    frontier: int = 3,
    runtime: float = 1.25,
    path_edges: int = 1,
    error: str | None = None,
) -> AlgorithmComparisonRecord:
    return AlgorithmComparisonRecord(
        algorithm_name=algorithm,
        found=found,
        path=path,
        total_cost=cost,
        nodes_expanded=expanded,
        nodes_generated=generated,
        maximum_frontier_size=frontier,
        execution_time_ms=runtime,
        path_length_edges=path_edges,
        optimality_expected=True,
        completeness_expected=True,
        error_message=error,
    )


@pytest.fixture
def named_graph() -> nx.Graph:
    graph = nx.Graph()
    graph.add_node("A", name="Millaniya Village")
    graph.add_node("B", name="Temple Shelter")
    return graph


def test_readable_and_failed_path_formatting(named_graph: nx.Graph) -> None:
    success = _record("Uniform-Cost Search")
    failure = _record(
        "Depth-First Search",
        found=False,
        path=(),
        cost=float("inf"),
        error="blocked",
    )

    assert format_comparison_path(success, named_graph) == "Millaniya Village → Temple Shelter"
    assert format_comparison_path(failure, named_graph) == "No route found"


def test_table_preparation_is_readable_and_preserves_algorithm_order(named_graph: nx.Graph) -> None:
    records = (
        _record("A* Search"),
        _record(
            "Breadth-First Search",
            found=False,
            path=(),
            cost=float("inf"),
            error="No connection",
        ),
    )

    rows = prepare_comparison_table_rows(records, named_graph)
    dataframe = build_comparison_dataframe(records, named_graph)

    assert tuple(row["Algorithm"] for row in rows) == ("A* Search", "Breadth-First Search")
    assert rows[0]["Path"] == "Millaniya Village → Temple Shelter"
    assert rows[0]["Total cost"] == "7.70"
    assert rows[0]["Approximate execution time"] == "1.25 ms"
    assert rows[0]["Found"] == "Yes"
    assert rows[1]["Path"] == "No route found"
    assert rows[1]["Total cost"] == "No finite route"
    assert rows[1]["Error message"] == "No connection"
    assert dataframe["Algorithm"].tolist() == ["A* Search", "Breadth-First Search"]
    assert build_comparison_dataframe((records[0],))["Path"].tolist() == ["A → B"]


def test_metric_chart_rows_preserve_order_and_filter_only_where_required() -> None:
    records = (
        _record("BFS", expanded=5, frontier=4, runtime=2.0, path_edges=2),
        _record(
            "DFS",
            found=False,
            path=(),
            cost=float("inf"),
            expanded=8,
            frontier=6,
            runtime=3.0,
            path_edges=0,
        ),
        _record("UCS", cost=6.5, expanded=3, frontier=2, runtime=1.0, path_edges=1),
    )

    assert prepare_cost_chart_rows(records) == (
        {"Algorithm": "BFS", "Value": 7.7},
        {"Algorithm": "UCS", "Value": 6.5},
    )
    assert prepare_nodes_expanded_chart_rows(records) == (
        {"Algorithm": "BFS", "Value": 5.0},
        {"Algorithm": "DFS", "Value": 8.0},
        {"Algorithm": "UCS", "Value": 3.0},
    )
    assert tuple(row["Value"] for row in prepare_frontier_chart_rows(records)) == (4.0, 6.0, 2.0)
    assert tuple(row["Value"] for row in prepare_runtime_chart_rows(records)) == (2.0, 3.0, 1.0)
    assert prepare_path_edge_chart_rows(records) == (
        {"Algorithm": "BFS", "Value": 2.0},
        {"Algorithm": "UCS", "Value": 1.0},
    )
    assert excluded_cost_algorithm_names(records) == ("DFS",)
    assert failed_algorithm_names(records) == ("DFS",)


def test_chart_builders_handle_mixed_and_all_failed_records() -> None:
    mixed = (
        _record("BFS"),
        _record("DFS", found=False, path=(), cost=float("inf")),
    )
    all_failed = (
        _record("BFS", found=False, path=(), cost=float("inf")),
        _record("DFS", found=False, path=(), cost=float("inf")),
    )

    cost_chart = build_total_cost_chart(mixed)
    assert cost_chart is not None
    assert tuple(cost_chart.data[0].x) == ("BFS",)
    assert build_total_cost_chart(all_failed) is None
    assert build_path_edge_chart(all_failed) is None


def test_tied_and_single_minimum_calculation_reports_all_winners() -> None:
    tied = (
        _record("UCS", cost=7.7),
        _record("A*", cost=7.7),
        _record("BFS", cost=9.0),
    )
    single = (
        _record("UCS", expanded=2),
        _record("A*", expanded=5),
    )

    assert calculate_tied_minimum(tied, lambda record: record.total_cost) == (
        ("UCS", "A*"),
        7.7,
    )
    assert calculate_tied_minimum(single, lambda record: float(record.nodes_expanded)) == (
        ("UCS",),
        2.0,
    )

    insights = prepare_summary_insights(tied)
    assert insights[0].algorithm_names == ("UCS", "A*")
    assert format_summary_insight(insights[0]) == "Lowest finite route cost: UCS and A* at 7.70"


def test_all_failed_records_produce_no_misleading_summary() -> None:
    records = (
        _record("BFS", found=False, path=(), cost=float("inf")),
        _record("DFS", found=False, path=(), cost=float("inf")),
    )

    assert prepare_summary_insights(records) == ()
    assert failed_algorithm_names(records) == ("BFS", "DFS")


def test_comparison_page_uses_one_stored_comparison_call_and_no_algorithm_calls() -> None:
    root = Path(__file__).resolve().parents[1]
    page_source = (root / "pages" / "2_Algorithm_Comparison.py").read_text(encoding="utf-8")
    simulation_source = (root / "pages" / "1_Interactive_Simulation.py").read_text(encoding="utf-8")
    syntax_tree = ast.parse(page_source)
    compare_calls = [
        node
        for node in ast.walk(syntax_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "compare_algorithms"
    ]

    assert len(compare_calls) == 1
    assert "if run_clicked:" in page_source
    assert "latest_comparison_records" in page_source
    assert "build_total_cost_chart(records)" in page_source
    assert "build_runtime_chart(records)" in page_source
    assert "from algorithms" not in page_source
    assert ".search(" not in page_source
    assert "comparison" not in simulation_source.lower()
