"""Formatting helpers for SafeRouteSL."""

from __future__ import annotations

from math import isinf

import networkx as nx

from utils.constants import BALANCED_MODE, DISTANCE_MODE, OPTIMIZATION_MODE_LABELS, SAFETY_MODE, TIME_MODE


def humanize_identifier(value: str) -> str:
	if not value:
		return ""

	normalized = value.replace("_", " ").replace("-", " ").strip()
	if normalized.upper() == normalized and len(normalized) <= 4:
		return normalized
	return " ".join(part.capitalize() if part and part.lower() != "a*" else part.upper() for part in normalized.split())


def format_node_name(graph: nx.Graph, node_id: str) -> str:
	if node_id not in graph:
		return humanize_identifier(node_id)

	node_data = graph.nodes[node_id]
	name = str(node_data.get("name", "")).strip()
	if name:
		return name

	short_name = str(node_data.get("short_name", "")).strip()
	if short_name:
		return short_name

	return humanize_identifier(node_id)


def format_path(graph: nx.Graph, path: tuple[str, ...]) -> str:
	if not path:
		return "No path available"
	return " → ".join(format_node_name(graph, node_id) for node_id in path)


def format_cost(cost: float, optimization_mode: str) -> str:
	if isinf(cost):
		return "No finite route"

	if optimization_mode == DISTANCE_MODE:
		return f"{cost:.2f} km"
	if optimization_mode == TIME_MODE:
		return f"{cost:.2f} min"
	if optimization_mode in {SAFETY_MODE, BALANCED_MODE}:
		return f"{cost:.2f}"

	return f"{cost:.2f}"


def format_execution_time(execution_time_ms: float) -> str:
	return f"{execution_time_ms:.2f} ms"


def format_optimization_mode_label(optimization_mode: str) -> str:
	return OPTIMIZATION_MODE_LABELS.get(optimization_mode, humanize_identifier(optimization_mode))
