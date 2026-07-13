"""Final-state rendering helpers for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import streamlit as st

from models.search_models import SearchResult
from utils.formatting import format_node_name, format_path


def render_final_search_state(result: SearchResult, graph: nx.Graph) -> None:
	st.subheader("Final State")
	st.write(f"Algorithm: {result.algorithm_name}")
	st.write(f"Start: {format_node_name(graph, result.start_node)}")
	st.write(f"Goal: {format_node_name(graph, result.goal_node)}")
	st.write(f"Goal status: {'Reached' if result.found else 'Not reached'}")
	st.write(f"Final route: {format_path(graph, result.final_path)}")

	if result.error_message:
		st.warning(result.error_message)

	if result.steps:
		st.write("Final explanation:")
		st.info(result.steps[-1].explanation or "No final explanation recorded.")
