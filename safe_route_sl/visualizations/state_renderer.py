"""Final-state rendering helpers for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import pandas as pd
import streamlit as st

from models.configuration import SearchConfiguration
from models.search_models import SearchResult, SearchStep
from utils.formatting import format_node_name, format_path, humanize_identifier
from visualizations.card_renderer import render_centered_card
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


def build_step_summary_values(graph: nx.Graph, step: SearchStep) -> tuple[tuple[str, str], ...]:
	"""Return compact human-readable values for the search-state summary cards."""
	current_node = (
		format_node_name(graph, step.current_node)
		if step.current_node is not None
		else "None"
	)
	return (
		("Step", str(step.step_number)),
		("Event", humanize_identifier(step.event_type)),
		("Current node", current_node),
		("Goal status", "Reached" if step.goal_found else "Not reached"),
	)


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
	summary_columns = st.columns([0.65, 0.85, 1.4, 1.0])
	for column, (label, value) in zip(summary_columns, build_step_summary_values(graph, step)):
		with column:
			render_centered_card(label, value)

	render_centered_card("Current path", format_path(graph, step.current_path))

	cost_values = build_step_cost_values(step, configuration)
	if cost_values:
		cost_columns = st.columns(len(cost_values))
		for column, (label, value) in zip(cost_columns, cost_values.items()):
			with column:
				render_centered_card(label, value, prominent=True)

	st.write("Frontier")
	if step.frontier_entries:
		st.dataframe(build_frontier_dataframe(graph, step), width="stretch", hide_index=True)
	else:
		st.info("The frontier is empty.")

	render_centered_card("Explored nodes", format_explored_nodes(graph, step))

	metric_columns = st.columns(3)
	with metric_columns[0]:
		render_centered_card("Nodes expanded", step.nodes_expanded, prominent=True)
	with metric_columns[1]:
		render_centered_card("Nodes generated", step.nodes_generated, prominent=True)
	with metric_columns[2]:
		render_centered_card("Max frontier", step.maximum_frontier_size, prominent=True)

	st.write("Step explanation")
	st.info(step.explanation or "No explanation recorded for this step.")

	if step.goal_found:
		st.success("The goal has been reached.")
		render_centered_card("Final path", format_path(graph, result.final_path))
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
