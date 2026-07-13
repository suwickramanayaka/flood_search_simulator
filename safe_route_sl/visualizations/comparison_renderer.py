"""Comparison rendering helpers for SafeRouteSL."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from services.comparison_service import AlgorithmComparisonRecord


def build_comparison_dataframe(records: tuple[AlgorithmComparisonRecord, ...]) -> pd.DataFrame:
	return pd.DataFrame(
		[
			{
				"Algorithm": record.algorithm_name,
				"Found": record.found,
				"Path": " → ".join(record.path) if record.path else "No path available",
				"Total cost": record.total_cost,
				"Nodes expanded": record.nodes_expanded,
				"Nodes generated": record.nodes_generated,
				"Maximum frontier": record.maximum_frontier_size,
				"Execution time in milliseconds": record.execution_time_ms,
				"Path edges": record.path_length_edges,
				"Optimal expected": record.optimality_expected,
				"Complete expected": record.completeness_expected,
				"Error message": record.error_message,
			}
			for record in records
		]
	)


def render_comparison_results(records: tuple[AlgorithmComparisonRecord, ...]) -> None:
	dataframe = build_comparison_dataframe(records)
	st.dataframe(dataframe, use_container_width=True, hide_index=True)
