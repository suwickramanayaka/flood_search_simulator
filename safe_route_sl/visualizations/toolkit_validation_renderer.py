"""Presentation preparation for toolkit validation diagnostics."""

from __future__ import annotations

from math import isfinite

import networkx as nx
import pandas as pd

from services.toolkit_validation_service import ToolkitValidationRecord
from utils.formatting import format_node_name


VALIDATION_TABLE_COLUMNS = (
    "Algorithm",
    "Reference toolkit",
    "Status",
    "Custom path",
    "Toolkit path",
    "Custom cost",
    "Toolkit cost",
    "Custom path edges",
    "Toolkit path edges",
    "Optimality scope",
    "Validation explanation",
    "Error message",
)


def format_validation_path(graph: nx.Graph, path: tuple[str, ...]) -> str:
    """Return a path using full location names."""
    if not path:
        return "No route found"
    return " → ".join(format_node_name(graph, node_id) for node_id in path)


def format_validation_cost(cost: float) -> str:
    """Format finite costs while clearly identifying missing routes."""
    return f"{cost:.2f}" if isfinite(cost) else "No finite route"


def prepare_validation_table_rows(
    records: tuple[ToolkitValidationRecord, ...],
    graph: nx.Graph,
) -> tuple[dict[str, object], ...]:
    """Prepare deterministic human-readable validation table rows."""
    return tuple(
        {
            "Algorithm": record.algorithm_name,
            "Reference toolkit": record.toolkit_name,
            "Status": record.validation_status,
            "Custom path": format_validation_path(graph, record.custom_path),
            "Toolkit path": format_validation_path(graph, record.toolkit_path),
            "Custom cost": format_validation_cost(record.custom_cost),
            "Toolkit cost": format_validation_cost(record.toolkit_cost),
            "Custom path edges": record.custom_path_edges,
            "Toolkit path edges": record.toolkit_path_edges,
            "Optimality scope": record.optimality_scope,
            "Validation explanation": record.validation_message,
            "Error message": record.error_message or "—",
        }
        for record in records
    )


def build_validation_dataframe(
    records: tuple[ToolkitValidationRecord, ...],
    graph: nx.Graph,
) -> pd.DataFrame:
    """Build the ordered toolkit validation table."""
    return pd.DataFrame(
        prepare_validation_table_rows(records, graph),
        columns=VALIDATION_TABLE_COLUMNS,
    )
