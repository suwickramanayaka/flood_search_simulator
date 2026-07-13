"""Metrics rendering helpers for SafeRouteSL."""

from __future__ import annotations

import streamlit as st

from models.search_models import SearchResult
from utils.formatting import format_cost, format_execution_time


def render_search_metrics(result: SearchResult, optimization_mode: str = "balanced") -> None:
	row_one = st.columns(3)
	row_two = st.columns(3)

	row_one[0].metric("Result", "Found" if result.found else "Not found")
	row_one[1].metric("Total cost", format_cost(result.total_cost, optimization_mode))
	row_one[2].metric("Path edges", str(result.path_length_edges))

	row_two[0].metric("Nodes expanded", str(result.nodes_expanded))
	row_two[1].metric("Nodes generated", str(result.nodes_generated))
	row_two[2].metric("Max frontier", str(result.maximum_frontier_size))

	st.caption(f"Execution time (approx.): {format_execution_time(result.execution_time_ms)}")
	st.caption(
		f"Completeness expected: {'Yes' if result.completeness_expected else 'No'} | Optimality expected: {'Yes' if result.optimality_expected else 'No'}"
	)
