"""Uniform-cost search for SafeRouteSL."""

from __future__ import annotations

import heapq
from itertools import count
from time import perf_counter

import networkx as nx

from algorithms.base import (
    EPSILON,
    SearchAlgorithm,
    build_failure_result,
    build_start_equals_goal_result,
    build_success_result,
    calculate_path_cost,
    clean_frontier_entries,
    make_initial_step,
    make_step,
    serialize_frontier_entry,
)
from models.configuration import SearchConfiguration
from models.search_models import SearchResult
from services.graph_service import get_traversable_neighbors
from utils.cost_functions import calculate_edge_cost


class UniformCostSearch(SearchAlgorithm):
    name = "Uniform-Cost Search"
    optimality_expected = True
    completeness_expected = True

    def search(self, graph: nx.Graph, configuration: SearchConfiguration) -> SearchResult:
        start_time = perf_counter()
        start_node = configuration.start_node
        goal_node = configuration.goal_node
        sequence = count()

        heap: list[tuple[float, str, int, tuple[str, ...]]] = []
        heapq.heappush(heap, (0.0, start_node, next(sequence), (start_node,)))
        best_cost: dict[str, float] = {start_node: 0.0}
        best_path: dict[str, tuple[str, ...]] = {start_node: (start_node,)}
        frontier_state: dict[str, tuple[float, tuple[str, ...], int]] = {start_node: (0.0, (start_node,), 0)}
        explored: set[str] = set()
        repeated_state_skips = 0
        nodes_generated = 1
        nodes_expanded = 0
        maximum_frontier_size = 1
        steps = [
            make_initial_step(
                start_node,
                [serialize_frontier_entry(start_node, (start_node,), priority=0.0, g=0.0)],
                g_cost=0.0,
                explanation=f"The search starts at {start_node} with accumulated cost g(n)=0.0.",
            )
        ]

        if start_node == goal_node:
            initial_step = steps[0]
            goal_step = make_step(
                1,
                "goal",
                start_node,
                (),
                (),
                (start_node,),
                g_cost=0.0,
                nodes_expanded=1,
                nodes_generated=1,
                maximum_frontier_size=1,
                goal_found=True,
                explanation=f"UCS reached the goal immediately at {start_node}.",
            )
            execution_time_ms = (perf_counter() - start_time) * 1000
            return build_start_equals_goal_result(
                self.name,
                configuration,
                initial_step,
                goal_step,
                execution_time_ms,
                toolkit_source=self.toolkit_source,
                optimality_expected=self.optimality_expected,
                completeness_expected=self.completeness_expected,
            )

        while heap:
            accumulated_cost, current_node, _, current_path = heapq.heappop(heap)
            best_known_cost = best_cost.get(current_node)
            if best_known_cost is None or accumulated_cost > best_known_cost + EPSILON:
                repeated_state_skips += 1
                continue

            frontier_state.pop(current_node, None)

            if current_node in explored:
                repeated_state_skips += 1
                continue

            explored.add(current_node)
            nodes_expanded += 1

            if current_node == goal_node:
                total_cost = accumulated_cost
                goal_step = make_step(
                    len(steps),
                    "goal",
                    current_node,
                    clean_frontier_entries(
                        serialize_frontier_entry(node, path, priority=cost, g=cost)
                        for node, (cost, path, _) in frontier_state.items()
                    ),
                    explored,
                    current_path,
                    g_cost=accumulated_cost,
                    nodes_expanded=nodes_expanded,
                    nodes_generated=nodes_generated,
                    maximum_frontier_size=maximum_frontier_size,
                    goal_found=True,
                    explanation=f"UCS selected {current_node} because it had the lowest accumulated path cost g(n)={accumulated_cost} in the priority queue.",
                )
                steps.append(goal_step)
                execution_time_ms = (perf_counter() - start_time) * 1000
                return build_success_result(
                    self.name,
                    configuration,
                    current_path,
                    steps,
                    nodes_expanded,
                    nodes_generated,
                    maximum_frontier_size,
                    repeated_state_skips,
                    execution_time_ms,
                    total_cost,
                    toolkit_source=self.toolkit_source,
                    optimality_expected=self.optimality_expected,
                    completeness_expected=self.completeness_expected,
                )

            generated_nodes: list[str] = []
            replaced_nodes: list[str] = []
            skipped_nodes: list[str] = []
            for neighbor in get_traversable_neighbors(graph, current_node):
                edge_data = graph.get_edge_data(current_node, neighbor)
                if edge_data is None:
                    continue
                edge_cost = calculate_edge_cost(edge_data, configuration.optimization_mode, configuration.risk_weight)
                if edge_cost == float("inf"):
                    skipped_nodes.append(neighbor)
                    continue

                tentative_cost = accumulated_cost + edge_cost
                best_neighbor_cost = best_cost.get(neighbor)
                if best_neighbor_cost is not None and tentative_cost >= best_neighbor_cost - EPSILON:
                    repeated_state_skips += 1
                    skipped_nodes.append(neighbor)
                    continue

                next_path = current_path + (neighbor,)
                best_cost[neighbor] = tentative_cost
                best_path[neighbor] = next_path
                seq = next(sequence)
                heapq.heappush(heap, (tentative_cost, neighbor, seq, next_path))
                frontier_state[neighbor] = (tentative_cost, next_path, seq)
                nodes_generated += 1
                if best_neighbor_cost is not None:
                    replaced_nodes.append(neighbor)
                else:
                    generated_nodes.append(neighbor)

            maximum_frontier_size = max(maximum_frontier_size, len(frontier_state))
            step = make_step(
                len(steps),
                "expand",
                current_node,
                clean_frontier_entries(
                    serialize_frontier_entry(node, path, priority=cost, g=cost)
                    for node, (cost, path, _) in frontier_state.items()
                ),
                explored,
                current_path,
                g_cost=accumulated_cost,
                nodes_expanded=nodes_expanded,
                nodes_generated=nodes_generated,
                maximum_frontier_size=maximum_frontier_size,
                explanation=(
                    f"UCS selected {current_node} because it had the lowest accumulated path cost g(n)={accumulated_cost} in the priority queue. "
                    + (
                        f"Generated {', '.join(generated_nodes)}."
                        if generated_nodes
                        else ""
                    )
                    + (
                        f" Replaced more expensive routes to {', '.join(replaced_nodes)}."
                        if replaced_nodes
                        else ""
                    )
                    + (
                        f" Skipped {', '.join(skipped_nodes)} because they were blocked, explored, or not cheaper."
                        if skipped_nodes
                        else ""
                    )
                ).strip(),
            )
            steps.append(step)

        execution_time_ms = (perf_counter() - start_time) * 1000
        failure_step = make_step(
            len(steps),
            "failure",
            None,
            (),
            explored,
            (start_node,),
            nodes_expanded=nodes_expanded,
            nodes_generated=nodes_generated,
            maximum_frontier_size=maximum_frontier_size,
            goal_found=False,
            explanation=f"The priority queue is empty. No traversable route was found between {start_node} and {goal_node}.",
        )
        steps.append(failure_step)
        return build_failure_result(
            self.name,
            configuration,
            steps,
            nodes_expanded,
            nodes_generated,
            maximum_frontier_size,
            repeated_state_skips,
            execution_time_ms,
            "No traversable route was found.",
            toolkit_source=self.toolkit_source,
            optimality_expected=self.optimality_expected,
            completeness_expected=self.completeness_expected,
        )
