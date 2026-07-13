"""NetworkX validation adapters for SafeRouteSL."""

from __future__ import annotations

from typing import Callable

import networkx as nx

from algorithms.base import calculate_path_cost
from services.graph_service import create_traversable_graph
from utils.cost_functions import create_networkx_weight_function
from utils.exceptions import GraphValidationError
from utils.heuristics import create_heuristic_function


def _traversable_graph(graph: nx.Graph) -> nx.Graph:
	return create_traversable_graph(graph)


def _raise_no_path(message: str) -> None:
	raise GraphValidationError(message)


def run_networkx_dijkstra(graph: nx.Graph, configuration) -> tuple[tuple[str, ...], float]:
	traversable_graph = _traversable_graph(graph)
	weight = create_networkx_weight_function(configuration.optimization_mode, configuration.risk_weight)
	try:
		path = nx.dijkstra_path(traversable_graph, configuration.start_node, configuration.goal_node, weight=weight)
		total_cost = nx.dijkstra_path_length(
			traversable_graph,
			configuration.start_node,
			configuration.goal_node,
			weight=weight,
		)
	except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
		_raise_no_path(
			f"No traversable route exists between {configuration.start_node!r} and {configuration.goal_node!r}"
		)
	return tuple(path), float(total_cost)


def run_networkx_astar(graph: nx.Graph, configuration) -> tuple[tuple[str, ...], float]:
	traversable_graph = _traversable_graph(graph)
	weight = create_networkx_weight_function(configuration.optimization_mode, configuration.risk_weight)
	heuristic = create_heuristic_function(graph, configuration.goal_node, configuration.heuristic_type)
	try:
		path = nx.astar_path(
			traversable_graph,
			configuration.start_node,
			configuration.goal_node,
			heuristic=lambda node, target: heuristic(node),
			weight=weight,
		)
		total_cost = calculate_path_cost(
			traversable_graph,
			tuple(path),
			configuration.optimization_mode,
			configuration.risk_weight,
		)
	except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
		_raise_no_path(
			f"No traversable route exists between {configuration.start_node!r} and {configuration.goal_node!r}"
		)
	return tuple(path), float(total_cost)


def run_networkx_bfs_shortest_path(graph: nx.Graph, start_node: str, goal_node: str) -> tuple[str, ...]:
	traversable_graph = _traversable_graph(graph)
	try:
		path = nx.shortest_path(traversable_graph, start_node, goal_node)
	except (nx.NetworkXNoPath, nx.NodeNotFound) as exc:
		_raise_no_path(f"No traversable route exists between {start_node!r} and {goal_node!r}")
	return tuple(path)
