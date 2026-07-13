"""Graph rendering helpers for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import plotly.graph_objects as go

from utils.constants import EDGE_COLORS, NODE_COLORS
from utils.formatting import format_node_name, humanize_identifier


def _node_position(graph: nx.Graph, node_id: str) -> tuple[float, float]:
	node_data = graph.nodes[node_id]
	return float(node_data["longitude"]), float(node_data["latitude"])


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
