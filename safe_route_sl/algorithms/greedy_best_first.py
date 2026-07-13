"""Greedy best-first search for SafeRouteSL."""

from __future__ import annotations

import heapq
from itertools import count
from time import perf_counter

import networkx as nx

from algorithms.base import (
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
from utils.heuristics import calculate_heuristic


class GreedyBestFirstSearch(SearchAlgorithm):
    name = "Greedy Best-First Search"
    optimality_expected = False
    completeness_expected = True

    def search(self, graph: nx.Graph, configuration: SearchConfiguration) -> SearchResult:
        start_time = perf_counter()
        start_node = configuration.start_node
        goal_node = configuration.goal_node
        sequence = count()

        start_h = calculate_heuristic(graph, start_node, goal_node, configuration.heuristic_type)
        heap: list[tuple[float, str, int, float, tuple[str, ...]]] = []
        heapq.heappush(heap, (start_h, start_node, next(sequence), 0.0, (start_node,)))
        frontier_state: dict[str, tuple[float, float, tuple[str, ...], int]] = {
            start_node: (start_h, 0.0, (start_node,), 0)
        }
        explored: set[str] = set()
        repeated_state_skips = 0
        nodes_generated = 1
        nodes_expanded = 0
        maximum_frontier_size = 1
        steps = [
            make_initial_step(
                start_node,
                [serialize_frontier_entry(start_node, (start_node,), priority=start_h, g=0.0, h=start_h)],
                g_cost=0.0,
                h_cost=start_h,
                f_cost=start_h,
                explanation=f"The search starts at {start_node} with heuristic h(n)={start_h}.",
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
                h_cost=start_h,
                f_cost=start_h,
                nodes_expanded=1,
                nodes_generated=1,
                maximum_frontier_size=1,
                goal_found=True,
                explanation=f"Greedy Best-First Search reached the goal immediately at {start_node}.",
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
            heuristic_value, current_node, _, accumulated_cost, current_path = heapq.heappop(heap)
            frontier_entry = frontier_state.get(current_node)
            if frontier_entry is None or heuristic_value != frontier_entry[0] or accumulated_cost != frontier_entry[1]:
                repeated_state_skips += 1
                continue

            frontier_state.pop(current_node, None)

            if current_node in explored:
                repeated_state_skips += 1
                continue

            explored.add(current_node)
            nodes_expanded += 1

            if current_node == goal_node:
                total_cost = calculate_path_cost(graph, current_path, configuration.optimization_mode, configuration.risk_weight)
                goal_step = make_step(
                    len(steps),
                    "goal",
                    current_node,
                    clean_frontier_entries(
                        serialize_frontier_entry(node, path, priority=h, g=g, h=h)
                        for node, (h, g, path, _) in frontier_state.items()
                    ),
                    explored,
                    current_path,
                    g_cost=accumulated_cost,
                    h_cost=heuristic_value,
                    f_cost=heuristic_value,
                    nodes_expanded=nodes_expanded,
                    nodes_generated=nodes_generated,
                    maximum_frontier_size=maximum_frontier_size,
                    goal_found=True,
                    explanation=(
                        f"Greedy Best-First Search selected {current_node} because it had the smallest heuristic estimate h(n)={heuristic_value}. "
                        "It did not use the full accumulated path cost to choose the node."
                    ),
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
            skipped_nodes: list[str] = []
            for neighbor in get_traversable_neighbors(graph, current_node):
                if neighbor in explored or neighbor in frontier_state:
                    repeated_state_skips += 1
                    skipped_nodes.append(neighbor)
                    continue
                edge_cost = calculate_path_cost(graph, current_path + (neighbor,), configuration.optimization_mode, configuration.risk_weight)
                h_cost = calculate_heuristic(graph, neighbor, goal_node, configuration.heuristic_type)
                seq = next(sequence)
                next_path = current_path + (neighbor,)
                heapq.heappush(heap, (h_cost, neighbor, seq, edge_cost, next_path))
                frontier_state[neighbor] = (h_cost, edge_cost, next_path, seq)
                nodes_generated += 1
                generated_nodes.append(neighbor)

            maximum_frontier_size = max(maximum_frontier_size, len(frontier_state))
            step = make_step(
                len(steps),
                "expand",
                current_node,
                clean_frontier_entries(
                    serialize_frontier_entry(node, path, priority=h, g=g, h=h)
                    for node, (h, g, path, _) in frontier_state.items()
                ),
                explored,
                current_path,
                g_cost=accumulated_cost,
                h_cost=heuristic_value,
                f_cost=heuristic_value,
                nodes_expanded=nodes_expanded,
                nodes_generated=nodes_generated,
                maximum_frontier_size=maximum_frontier_size,
                explanation=(
                    f"Greedy Best-First Search selected {current_node} because it had the smallest heuristic estimate h(n)={heuristic_value}. "
                    + (
                        f"Generated {', '.join(generated_nodes)}."
                        if generated_nodes
                        else ""
                    )
                    + (
                        f" Skipped {', '.join(skipped_nodes)} because they were already explored or on the frontier."
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
