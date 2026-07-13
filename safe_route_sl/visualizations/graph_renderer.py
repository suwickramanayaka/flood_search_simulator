"""Graph rendering helpers for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import plotly.graph_objects as go

from models.configuration import SearchConfiguration
from models.search_models import SearchResult, SearchStep
from utils.constants import EDGE_COLORS, NODE_COLORS
from utils.formatting import format_node_name, humanize_identifier


NODE_STATE_PRECEDENCE = (
	"current",
	"start",
	"goal",
	"final_path",
	"current_path",
	"frontier",
	"explored",
	"unavailable",
	"unvisited",
)

EDGE_STATE_PRECEDENCE = (
	"blocked",
	"final_route",
	"current_path",
	"high_risk",
	"normal",
)

STEP_NODE_COLORS = {
	**NODE_COLORS,
	"current_path": "#7dd3fc",
}

NODE_STATE_LABELS = {
	"current": "Current node",
	"start": "Start",
	"goal": "Goal",
	"final_path": "Final route nodes",
	"current_path": "Current path",
	"frontier": "Frontier",
	"explored": "Explored",
	"unavailable": "Unavailable",
	"unvisited": "Unvisited",
}

EDGE_STATE_LABELS = {
	"final_route": "Final route",
	"current_path": "Current path",
	"blocked": "Blocked roads",
	"high_risk": "Higher-risk roads",
	"normal": "Normal roads",
}


def _node_position(graph: nx.Graph, node_id: str) -> tuple[float, float]:
	node_data = graph.nodes[node_id]
	return float(node_data["longitude"]), float(node_data["latitude"])


def get_geographic_positions(graph: nx.Graph) -> dict[str, tuple[float, float]]:
	"""Return stable longitude/latitude positions without modifying the graph."""
	return {node_id: _node_position(graph, node_id) for node_id in graph.nodes}


def _path_edge_keys(path: tuple[str, ...]) -> set[frozenset[str]]:
	"""Return undirected edge keys for a recorded path."""
	return {frozenset((source, target)) for source, target in zip(path, path[1:])}


def classify_node_states(
	graph: nx.Graph,
	step: SearchStep,
	result: SearchResult,
) -> dict[str, str]:
	"""Classify nodes using the documented deterministic precedence order."""
	current_path_nodes = set(step.current_path)
	frontier_nodes = set(step.frontier_nodes)
	explored_nodes = set(step.explored_nodes)
	final_path_nodes = set(result.final_path) if step.goal_found else set()

	states: dict[str, str] = {}
	for node_id, node_data in graph.nodes(data=True):
		candidates = {
			"current": step.current_node == node_id,
			"start": result.start_node == node_id,
			"goal": result.goal_node == node_id,
			"final_path": node_id in final_path_nodes,
			"current_path": node_id in current_path_nodes,
			"frontier": node_id in frontier_nodes,
			"explored": node_id in explored_nodes,
			"unavailable": not node_data.get("available", False),
			"unvisited": True,
		}
		states[node_id] = next(state for state in NODE_STATE_PRECEDENCE if candidates[state])
	return states


def classify_edge_states(
	graph: nx.Graph,
	step: SearchStep,
	result: SearchResult,
) -> dict[tuple[str, str], str]:
	"""Classify edges deterministically, never promoting blocked roads into paths."""
	current_path_edges = _path_edge_keys(step.current_path)
	final_route_edges = _path_edge_keys(result.final_path) if step.goal_found else set()
	states: dict[tuple[str, str], str] = {}

	for source, target, edge_data in graph.edges(data=True):
		edge_key = frozenset((source, target))
		if edge_data.get("blocked", False):
			state = "blocked"
		elif edge_key in final_route_edges:
			state = "final_route"
		elif edge_key in current_path_edges:
			state = "current_path"
		elif int(edge_data.get("flood_risk", 0)) >= 4:
			state = "high_risk"
		else:
			state = "normal"
		states[(source, target)] = state

	return states


def _edge_trace(
	graph: nx.Graph,
	edges: list[tuple[str, str]],
	*,
	color: str,
	width: float,
	dash: str = "solid",
	name: str,
	opacity: float = 1.0,
) -> go.Scatter:
	x_values: list[float | None] = []
	y_values: list[float | None] = []

	for source, target in edges:
		x0, y0 = _node_position(graph, source)
		x1, y1 = _node_position(graph, target)
		x_values.extend([x0, x1, None])
		y_values.extend([y0, y1, None])

	return go.Scatter(
		x=x_values,
		y=y_values,
		mode="lines",
		line={"color": color, "width": width, "dash": dash},
		name=name,
		hoverinfo="skip",
		opacity=opacity,
	)


def _node_trace(
	graph: nx.Graph,
	node_ids: list[str],
	*,
	color: str,
	name: str,
	size: int = 14,
	line_color: str = "#334155",
	line_width: int = 1,
) -> go.Scatter:
	x_values: list[float] = []
	y_values: list[float] = []
	hover_texts: list[str] = []

	for node_id in node_ids:
		x, y = _node_position(graph, node_id)
		node_data = graph.nodes[node_id]
		x_values.append(x)
		y_values.append(y)
		hover_texts.append(
			"<br>".join(
				[
					f"<b>{format_node_name(graph, node_id)}</b>",
					f"Type: {humanize_identifier(str(node_data.get('location_type', 'unknown')))}",
					f"Capacity: {node_data.get('capacity', 0)}",
					f"Available: {'Yes' if node_data.get('available', False) else 'No'}",
					f"Coordinates: {float(node_data.get('latitude', 0.0)):.4f}, {float(node_data.get('longitude', 0.0)):.4f}",
				]
			)
		)

	return go.Scatter(
		x=x_values,
		y=y_values,
		mode="markers+text",
		text=[format_node_name(graph, node_id) for node_id in node_ids],
		textposition="top center",
		hovertext=hover_texts,
		hoverinfo="text",
		marker={"size": size, "color": color, "line": {"color": line_color, "width": line_width}},
		name=name,
	)


def build_graph_figure(
	graph: nx.Graph,
	start_node: str | None = None,
	goal_node: str | None = None,
	final_path: tuple[str, ...] = (),
	optimization_mode: str = "balanced",
	risk_weight: float = 4.0,
) -> go.Figure:
	del optimization_mode, risk_weight

	path_edges = list(zip(final_path, final_path[1:]))
	final_path_nodes = set(final_path)

	blocked_edges: list[tuple[str, str]] = []
	final_edges: list[tuple[str, str]] = []
	severe_edges: list[tuple[str, str]] = []
	normal_edges: list[tuple[str, str]] = []

	for source, target, edge_data in graph.edges(data=True):
		edge = (source, target)
		if edge in path_edges or (target, source) in path_edges:
			final_edges.append(edge)
			continue
		if edge_data.get("blocked", False):
			blocked_edges.append(edge)
		elif int(edge_data.get("flood_risk", 0)) >= 4:
			severe_edges.append(edge)
		else:
			normal_edges.append(edge)

	unavailable_nodes = [node_id for node_id, data in graph.nodes(data=True) if not data.get("available", False)]
	path_only_nodes = [node_id for node_id in final_path if node_id not in {start_node, goal_node}]
	other_nodes = [
		node_id
		for node_id, data in graph.nodes(data=True)
		if node_id not in final_path_nodes and node_id not in unavailable_nodes
	]

	fig = go.Figure()
	if normal_edges:
		fig.add_trace(_edge_trace(graph, normal_edges, color=EDGE_COLORS["normal"], width=1.5, name="Normal roads", opacity=0.75))
	if severe_edges:
		fig.add_trace(_edge_trace(graph, severe_edges, color=EDGE_COLORS["high_risk"], width=2.2, name="Higher-risk roads", opacity=0.9))
	if blocked_edges:
		fig.add_trace(_edge_trace(graph, blocked_edges, color=EDGE_COLORS["blocked"], width=2.0, dash="dash", name="Blocked roads", opacity=0.95))
	if final_edges:
		fig.add_trace(_edge_trace(graph, final_edges, color=EDGE_COLORS["final_route"], width=4.2, name="Final route", opacity=1.0))

	if other_nodes:
		fig.add_trace(_node_trace(graph, other_nodes, color=NODE_COLORS["unvisited"], name="Locations", size=13))
	if path_only_nodes:
		fig.add_trace(_node_trace(graph, path_only_nodes, color=NODE_COLORS["final_path"], name="Route nodes", size=15))
	if start_node and start_node in graph:
		fig.add_trace(_node_trace(graph, [start_node], color=NODE_COLORS["start"], name="Start", size=18))
	if goal_node and goal_node in graph:
		fig.add_trace(_node_trace(graph, [goal_node], color=NODE_COLORS["goal"], name="Goal", size=18))
	if unavailable_nodes:
		fig.add_trace(_node_trace(graph, unavailable_nodes, color=NODE_COLORS["unavailable"], name="Unavailable", size=13, line_color="#1f2937"))

	longitudes = [float(data["longitude"]) for _, data in graph.nodes(data=True)]
	latitudes = [float(data["latitude"]) for _, data in graph.nodes(data=True)]
	lon_min, lon_max = min(longitudes), max(longitudes)
	lat_min, lat_max = min(latitudes), max(latitudes)
	lon_pad = max(0.001, (lon_max - lon_min) * 0.08)
	lat_pad = max(0.001, (lat_max - lat_min) * 0.08)

	fig.update_layout(
		template="plotly_white",
		showlegend=True,
		margin={"l": 20, "r": 20, "t": 20, "b": 20},
		xaxis={"visible": False, "range": [lon_min - lon_pad, lon_max + lon_pad]},
		yaxis={"visible": False, "range": [lat_min - lat_pad, lat_max + lat_pad], "scaleanchor": "x", "scaleratio": 1},
		legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
	)
	fig.update_traces(cliponaxis=False)
	return fig


def build_search_step_figure(
	graph: nx.Graph,
	step: SearchStep,
	result: SearchResult,
	configuration: SearchConfiguration,
) -> go.Figure:
	"""Build a Plotly graph for one recorded search step without mutating inputs."""
	node_states = classify_node_states(graph, step, result)
	edge_states = classify_edge_states(graph, step, result)
	nodes_by_state = {
		state: [node_id for node_id in graph.nodes if node_states[node_id] == state]
		for state in NODE_STATE_PRECEDENCE
	}
	edges_by_state = {
		state: [edge for edge, edge_state in edge_states.items() if edge_state == state]
		for state in EDGE_STATE_PRECEDENCE
	}

	figure = go.Figure()
	edge_styles = {
		"normal": (EDGE_COLORS["normal"], 1.5, "solid", 0.75),
		"high_risk": (EDGE_COLORS["high_risk"], 2.2, "solid", 0.9),
		"blocked": (EDGE_COLORS["blocked"], 2.0, "dash", 0.95),
		"current_path": (EDGE_COLORS["current_path"], 3.4, "solid", 1.0),
		"final_route": (EDGE_COLORS["final_route"], 4.2, "solid", 1.0),
	}
	for state in ("normal", "high_risk", "blocked", "current_path", "final_route"):
		edges = edges_by_state[state]
		if edges:
			color, width, dash, opacity = edge_styles[state]
			figure.add_trace(
				_edge_trace(
					graph,
					edges,
					color=color,
					width=width,
					dash=dash,
					name=EDGE_STATE_LABELS[state],
					opacity=opacity,
				)
			)

	node_sizes = {
		"current": 20,
		"start": 18,
		"goal": 18,
		"final_path": 15,
		"current_path": 15,
		"frontier": 15,
		"explored": 14,
		"unavailable": 13,
		"unvisited": 13,
	}
	for state in reversed(NODE_STATE_PRECEDENCE):
		node_ids = nodes_by_state[state]
		if node_ids:
			figure.add_trace(
				_node_trace(
					graph,
					node_ids,
					color=STEP_NODE_COLORS[state],
					name=NODE_STATE_LABELS[state],
					size=node_sizes[state],
					line_color="#1f2937" if state == "unavailable" else "#334155",
					line_width=2 if state in {"current", "start", "goal"} else 1,
				)
			)

	positions = get_geographic_positions(graph)
	longitudes = [position[0] for position in positions.values()]
	latitudes = [position[1] for position in positions.values()]
	lon_min, lon_max = min(longitudes), max(longitudes)
	lat_min, lat_max = min(latitudes), max(latitudes)
	lon_pad = max(0.001, (lon_max - lon_min) * 0.08)
	lat_pad = max(0.001, (lat_max - lat_min) * 0.08)
	current_name = format_node_name(graph, step.current_node) if step.current_node is not None else "None"

	figure.update_layout(
		title={
			"text": (
				f"{configuration.algorithm} — Step {step.step_number} — "
				f"{humanize_identifier(step.event_type)} — Current: {current_name}"
			),
			"x": 0.01,
		},
		template="plotly_white",
		showlegend=True,
		margin={"l": 20, "r": 20, "t": 55, "b": 20},
		xaxis={"visible": False, "range": [lon_min - lon_pad, lon_max + lon_pad]},
		yaxis={"visible": False, "range": [lat_min - lat_pad, lat_max + lat_pad], "scaleanchor": "x", "scaleratio": 1},
		legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
	)
	figure.update_traces(cliponaxis=False)
	return figure
