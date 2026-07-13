"""Final-state rendering helpers for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import pandas as pd
import streamlit as st

from models.configuration import SearchConfiguration
from models.search_models import SearchResult, SearchStep
from utils.formatting import format_cost, format_node_name, format_path, humanize_identifier
from visualizations.metrics_renderer import render_search_metrics


def _format_numeric(value: object) -> str:
	"""Format a recorded numeric search value consistently."""
	return f"{float(value):.2f}"


def build_step_cost_values(
	step: SearchStep,
	configuration: SearchConfiguration,
) -> dict[str, str]:
	"""Return only the cost values meaningful for the selected algorithm."""
	field_names: tuple[tuple[str, str], ...]
	if configuration.algorithm == "Uniform-Cost Search":
		field_names = (("g(n)", "g_cost"),)
	elif configuration.algorithm == "Greedy Best-First Search":
		field_names = (("g(n)", "g_cost"), ("h(n)", "h_cost"))
	elif configuration.algorithm == "A* Search":
		field_names = (("g(n)", "g_cost"), ("h(n)", "h_cost"), ("f(n)", "f_cost"))
	else:
		field_names = ()

	return {
		label: _format_numeric(value)
		for label, attribute_name in field_names
		if (value := getattr(step, attribute_name)) is not None
	}


def build_frontier_dataframe(graph: nx.Graph, step: SearchStep) -> pd.DataFrame:
	"""Build a human-readable frontier table with irrelevant columns removed."""
	optional_fields = (
		("Priority", "priority"),
		("g", "g"),
		("h", "h"),
		("f", "f"),
	)
	meaningful_fields = [
		(label, key)
		for label, key in optional_fields
		if any(entry.get(key) is not None for entry in step.frontier_entries)
	]

	rows: list[dict[str, object]] = []
	for entry in step.frontier_entries:
		node_id = str(entry.get("node", ""))
		path_value = entry.get("path", ())
		path = tuple(str(node_id) for node_id in path_value) if isinstance(path_value, (list, tuple)) else ()
		row: dict[str, object] = {"Node": format_node_name(graph, node_id)}
		for label, key in meaningful_fields:
			value = entry.get(key)
			row[label] = "" if value is None else _format_numeric(value)
		row["Path"] = format_path(graph, path)
		rows.append(row)

	columns = ["Node", *(label for label, _ in meaningful_fields), "Path"]
	return pd.DataFrame(rows, columns=columns)


def format_explored_nodes(graph: nx.Graph, step: SearchStep) -> str:
	"""Return explored nodes as readable names or an explicit empty state."""
	if not step.explored_nodes:
		return "No nodes have been explored yet."
	return ", ".join(format_node_name(graph, node_id) for node_id in step.explored_nodes)


def is_completed_step(step: SearchStep) -> bool:
	"""Return whether a step represents a completed successful or failed search."""
	return step.goal_found or step.event_type in {"goal", "failure"}


def render_search_step_state(
	graph: nx.Graph,
	step: SearchStep,
	result: SearchResult,
	configuration: SearchConfiguration,
) -> None:
	"""Render the currently selected recorded search state."""
	st.subheader("Search State")
	st.write(f"Step number: {step.step_number}")
	st.write(f"Event type: {humanize_identifier(step.event_type)}")
	st.write(
		f"Current node: {format_node_name(graph, step.current_node)}"
		if step.current_node is not None
		else "Current node: None"
	)
	st.write(f"Current path: {format_path(graph, step.current_path)}")
	st.write(f"Goal status: {'Reached' if step.goal_found else 'Not reached'}")

	cost_values = build_step_cost_values(step, configuration)
	if cost_values:
		cost_columns = st.columns(len(cost_values))
		for column, (label, value) in zip(cost_columns, cost_values.items()):
			column.metric(label, value)

	st.write("Frontier")
	if step.frontier_entries:
		st.dataframe(build_frontier_dataframe(graph, step), use_container_width=True, hide_index=True)
	else:
		st.info("The frontier is empty.")

	st.write("Explored nodes")
	st.write(format_explored_nodes(graph, step))

	metric_columns = st.columns(3)
	metric_columns[0].metric("Nodes expanded", str(step.nodes_expanded))
	metric_columns[1].metric("Nodes generated", str(step.nodes_generated))
	metric_columns[2].metric("Max frontier", str(step.maximum_frontier_size))

	st.write("Step explanation")
	st.info(step.explanation or "No explanation recorded for this step.")

	if step.goal_found:
		st.success("The goal has been reached.")
		st.write(f"Final path: {format_path(graph, result.final_path)}")
		st.write(f"Final cost: {format_cost(result.total_cost, configuration.optimization_mode)}")
	elif step.event_type == "failure":
		st.warning("The search finished without finding a traversable route.")

	if is_completed_step(step):
		render_search_metrics(result, configuration.optimization_mode)


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
