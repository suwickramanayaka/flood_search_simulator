"""Pure preparation and Plotly rendering helpers for algorithm comparisons."""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Callable

import networkx as nx
import pandas as pd
import plotly.graph_objects as go

from services.comparison_service import AlgorithmComparisonRecord
from utils.formatting import format_node_name


@dataclass(frozen=True, slots=True)
class ComparisonInsight:
    """A tied minimum and the algorithms that achieved it."""

    label: str
    algorithm_names: tuple[str, ...]
    value: float
    value_format: str


TABLE_COLUMNS = (
    "Algorithm",
    "Found",
    "Path",
    "Total cost",
    "Nodes expanded",
    "Nodes generated",
    "Maximum frontier",
    "Approximate execution time",
    "Path edge count",
    "Optimality expected",
    "Completeness expected",
    "Error message",
)


def format_comparison_path(
    record: AlgorithmComparisonRecord,
    graph: nx.Graph | None = None,
) -> str:
    """Return a human-readable path, or the standard failed-search label."""
    if not record.found or not record.path:
        return "No route found"
    if graph is None:
        return " → ".join(record.path)
    return " → ".join(format_node_name(graph, node_id) for node_id in record.path)


def format_total_cost(record: AlgorithmComparisonRecord) -> str:
    """Format a finite route cost consistently for the comparison table."""
    if not record.found or not isfinite(record.total_cost):
        return "No finite route"
    return f"{record.total_cost:.2f}"


def prepare_comparison_table_rows(
    records: tuple[AlgorithmComparisonRecord, ...],
    graph: nx.Graph | None = None,
) -> tuple[dict[str, object], ...]:
    """Prepare ordered, presentation-ready comparison table rows."""
    return tuple(
        {
            "Algorithm": record.algorithm_name,
            "Found": "Yes" if record.found else "No",
            "Path": format_comparison_path(record, graph),
            "Total cost": format_total_cost(record),
            "Nodes expanded": record.nodes_expanded,
            "Nodes generated": record.nodes_generated,
            "Maximum frontier": record.maximum_frontier_size,
            "Approximate execution time": f"{record.execution_time_ms:.2f} ms",
            "Path edge count": record.path_length_edges,
            "Optimality expected": "Yes" if record.optimality_expected else "No",
            "Completeness expected": "Yes" if record.completeness_expected else "No",
            "Error message": record.error_message or "—",
        }
        for record in records
    )


def build_comparison_dataframe(
    records: tuple[AlgorithmComparisonRecord, ...],
    graph: nx.Graph | None = None,
) -> pd.DataFrame:
    """Build the ordered human-readable comparison table."""
    return pd.DataFrame(prepare_comparison_table_rows(records, graph), columns=TABLE_COLUMNS)


def prepare_metric_chart_rows(
    records: tuple[AlgorithmComparisonRecord, ...],
    metric: str,
    *,
    successful_only: bool = False,
    finite_only: bool = False,
) -> tuple[dict[str, float | str], ...]:
    """Prepare ordered algorithm/value rows for a numeric comparison chart."""
    rows: list[dict[str, float | str]] = []
    for record in records:
        if successful_only and not record.found:
            continue
        value = float(getattr(record, metric))
        if finite_only and not isfinite(value):
            continue
        rows.append({"Algorithm": record.algorithm_name, "Value": value})
    return tuple(rows)


def prepare_cost_chart_rows(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[dict[str, float | str], ...]:
    """Return successful, finite route costs in service order."""
    return prepare_metric_chart_rows(
        records,
        "total_cost",
        successful_only=True,
        finite_only=True,
    )


def prepare_nodes_expanded_chart_rows(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[dict[str, float | str], ...]:
    """Return nodes-expanded chart rows in service order."""
    return prepare_metric_chart_rows(records, "nodes_expanded")


def prepare_frontier_chart_rows(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[dict[str, float | str], ...]:
    """Return maximum-frontier chart rows in service order."""
    return prepare_metric_chart_rows(records, "maximum_frontier_size")


def prepare_runtime_chart_rows(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[dict[str, float | str], ...]:
    """Return finite approximate-runtime chart rows in service order."""
    return prepare_metric_chart_rows(records, "execution_time_ms", finite_only=True)


def prepare_path_edge_chart_rows(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[dict[str, float | str], ...]:
    """Return successful path-edge counts in service order."""
    return prepare_metric_chart_rows(records, "path_length_edges", successful_only=True)


def excluded_cost_algorithm_names(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[str, ...]:
    """Return algorithms excluded from the finite route-cost chart."""
    return tuple(
        record.algorithm_name
        for record in records
        if not record.found or not isfinite(record.total_cost)
    )


def failed_algorithm_names(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[str, ...]:
    """Return algorithms that did not produce a route."""
    return tuple(record.algorithm_name for record in records if not record.found)


def build_metric_bar_chart(
    rows: tuple[dict[str, float | str], ...],
    *,
    title: str,
    y_axis_title: str,
    value_format: str,
) -> go.Figure | None:
    """Build a single ordered Plotly bar chart, or ``None`` for no data."""
    if not rows:
        return None

    algorithms = [str(row["Algorithm"]) for row in rows]
    values = [float(row["Value"]) for row in rows]
    labels = [format(value, value_format) for value in values]
    figure = go.Figure(
        data=[
            go.Bar(
                x=algorithms,
                y=values,
                text=labels,
                textposition="auto",
                hovertemplate="%{x}<br>%{y}<extra></extra>",
            )
        ]
    )
    figure.update_layout(
        title=title,
        xaxis_title="Algorithm",
        yaxis_title=y_axis_title,
        showlegend=False,
        margin=dict(l=40, r=20, t=60, b=80),
    )
    return figure


def build_total_cost_chart(records: tuple[AlgorithmComparisonRecord, ...]) -> go.Figure | None:
    """Build the finite total-route-cost chart."""
    return build_metric_bar_chart(
        prepare_cost_chart_rows(records),
        title="Total Route Cost",
        y_axis_title="Total route cost",
        value_format=".2f",
    )


def build_nodes_expanded_chart(records: tuple[AlgorithmComparisonRecord, ...]) -> go.Figure | None:
    """Build the nodes-expanded chart."""
    return build_metric_bar_chart(
        prepare_nodes_expanded_chart_rows(records),
        title="Nodes Expanded",
        y_axis_title="Nodes expanded",
        value_format=".0f",
    )


def build_frontier_chart(records: tuple[AlgorithmComparisonRecord, ...]) -> go.Figure | None:
    """Build the maximum-frontier-size chart."""
    return build_metric_bar_chart(
        prepare_frontier_chart_rows(records),
        title="Maximum Frontier Size",
        y_axis_title="Maximum frontier size",
        value_format=".0f",
    )


def build_runtime_chart(records: tuple[AlgorithmComparisonRecord, ...]) -> go.Figure | None:
    """Build the approximate educational execution-time chart."""
    return build_metric_bar_chart(
        prepare_runtime_chart_rows(records),
        title="Approximate Execution Time (Educational)",
        y_axis_title="Approximate execution time (ms)",
        value_format=".2f",
    )


def build_path_edge_chart(records: tuple[AlgorithmComparisonRecord, ...]) -> go.Figure | None:
    """Build the successful-route path-edge-count chart."""
    return build_metric_bar_chart(
        prepare_path_edge_chart_rows(records),
        title="Path Edge Count",
        y_axis_title="Path edges",
        value_format=".0f",
    )


def calculate_tied_minimum(
    records: tuple[AlgorithmComparisonRecord, ...],
    value_getter: Callable[[AlgorithmComparisonRecord], float],
    *,
    successful_only: bool = True,
) -> tuple[tuple[str, ...], float] | None:
    """Return every algorithm tied at the minimum finite eligible value."""
    eligible = [
        (record.algorithm_name, float(value_getter(record)))
        for record in records
        if (record.found or not successful_only) and isfinite(float(value_getter(record)))
    ]
    if not eligible:
        return None

    minimum = min(value for _, value in eligible)
    winners = tuple(
        name
        for name, value in eligible
        if isclose(value, minimum, rel_tol=1e-9, abs_tol=1e-9)
    )
    return winners, minimum


def prepare_summary_insights(
    records: tuple[AlgorithmComparisonRecord, ...],
) -> tuple[ComparisonInsight, ...]:
    """Calculate requested successful-search minima, preserving all ties."""
    definitions = (
        ("Lowest finite route cost", lambda record: record.total_cost, ".2f"),
        ("Fewest nodes expanded", lambda record: float(record.nodes_expanded), ".0f"),
        ("Smallest maximum frontier", lambda record: float(record.maximum_frontier_size), ".0f"),
        ("Fewest path edges", lambda record: float(record.path_length_edges), ".0f"),
        ("Fastest approximate execution time", lambda record: record.execution_time_ms, ".2f"),
    )
    insights: list[ComparisonInsight] = []
    for label, getter, value_format in definitions:
        minimum = calculate_tied_minimum(records, getter)
        if minimum is None:
            continue
        algorithm_names, value = minimum
        insights.append(ComparisonInsight(label, algorithm_names, value, value_format))
    return tuple(insights)


def format_summary_insight(insight: ComparisonInsight) -> str:
    """Format one tied-winner summary as concise display text."""
    algorithms = " and ".join(insight.algorithm_names)
    value = format(insight.value, insight.value_format)
    suffix = " ms" if "execution time" in insight.label.lower() else ""
    return f"{insight.label}: {algorithms} at {value}{suffix}"


def render_comparison_results(
    records: tuple[AlgorithmComparisonRecord, ...],
    graph: nx.Graph | None = None,
) -> None:
    """Render the comparison table while preserving the original public helper."""
    import streamlit as st

    st.dataframe(
        build_comparison_dataframe(records, graph),
        width="stretch",
        hide_index=True,
    )
