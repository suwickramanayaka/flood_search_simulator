"""Metrics rendering helpers for SafeRouteSL."""

from __future__ import annotations

import streamlit as st

from models.search_models import SearchResult
from utils.formatting import format_cost, format_execution_time
from visualizations.card_renderer import render_centered_card


def render_search_metrics(result: SearchResult, optimization_mode: str = "balanced") -> None:
	row_one = st.columns(3)
	row_two = st.columns(3)

	with row_one[0]:
		render_centered_card("Result", "Found" if result.found else "Not found", prominent=True)
	with row_one[1]:
		render_centered_card("Total cost", format_cost(result.total_cost, optimization_mode), prominent=True)
	with row_one[2]:
		render_centered_card("Path edges", result.path_length_edges, prominent=True)

	with row_two[0]:
		render_centered_card("Nodes expanded", result.nodes_expanded, prominent=True)
	with row_two[1]:
		render_centered_card("Nodes generated", result.nodes_generated, prominent=True)
	with row_two[2]:
		render_centered_card("Max frontier", result.maximum_frontier_size, prominent=True)

	detail_columns = st.columns(2)
	with detail_columns[0]:
		render_centered_card("Approximate execution time", format_execution_time(result.execution_time_ms))
	with detail_columns[1]:
		render_centered_card(
			"Expected properties",
			f"Completeness: {'Yes' if result.completeness_expected else 'No'}\n"
			f"Optimality: {'Yes' if result.optimality_expected else 'No'}",
		)
