"""A* search for SafeRouteSL."""

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
from utils.heuristics import calculate_heuristic


class AStarSearch(SearchAlgorithm):
    name = "A* Search"
    completeness_expected = True

    def search(self, graph: nx.Graph, configuration: SearchConfiguration) -> SearchResult:
        start_time = perf_counter()
        start_node = configuration.start_node
        goal_node = configuration.goal_node
        sequence = count()

        start_h = calculate_heuristic(graph, start_node, goal_node, configuration.heuristic_type)
        heap: list[tuple[float, float, str, int, float, tuple[str, ...]]] = []
        heapq.heappush(heap, (start_h, start_h, start_node, next(sequence), 0.0, (start_node,)))
        best_g: dict[str, float] = {start_node: 0.0}
        frontier_state: dict[str, tuple[float, float, float, tuple[str, ...], int]] = {
            start_node: (start_h, start_h, 0.0, (start_node,), 0)
        }
        explored: set[str] = set()
        repeated_state_skips = 0
        nodes_generated = 1
        nodes_expanded = 0
        maximum_frontier_size = 1
        optimality_expected = (
            configuration.heuristic_type == "zero"
            or (configuration.heuristic_type == "haversine" and configuration.optimization_mode == "distance")
        )
        steps = [
            make_initial_step(
                start_node,
                [serialize_frontier_entry(start_node, (start_node,), priority=start_h, g=0.0, h=start_h, f=start_h)],
                g_cost=0.0,
                h_cost=start_h,
                f_cost=start_h,
                explanation=f"The search starts at {start_node} with g(n)=0.0 and h(n)={start_h}.",
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
                explanation=f"A* reached the goal immediately at {start_node}.",
            )
            execution_time_ms = (perf_counter() - start_time) * 1000
            return build_start_equals_goal_result(
                self.name,
                configuration,
                initial_step,
                goal_step,
                execution_time_ms,
                toolkit_source=self.toolkit_source,
                optimality_expected=optimality_expected,
                completeness_expected=self.completeness_expected,
            )

        while heap:
            f_cost, h_cost, current_node, _, g_cost, current_path = heapq.heappop(heap)
            frontier_entry = frontier_state.get(current_node)
            if frontier_entry is None or abs(frontier_entry[0] - f_cost) > EPSILON or abs(frontier_entry[2] - g_cost) > EPSILON:
                repeated_state_skips += 1
                continue

            frontier_state.pop(current_node, None)

            best_known_g = best_g.get(current_node)
            if best_known_g is None or g_cost > best_known_g + EPSILON:
                repeated_state_skips += 1
                continue

            if current_node in explored:
                repeated_state_skips += 1
                continue

            explored.add(current_node)
            nodes_expanded += 1

            if current_node == goal_node:
                total_cost = g_cost
                goal_step = make_step(
                    len(steps),
                    "goal",
                    current_node,
                    clean_frontier_entries(
                        serialize_frontier_entry(node, path, priority=fv, g=gv, h=hv, f=fv)
                        for node, (fv, hv, gv, path, _) in frontier_state.items()
                    ),
                    explored,
                    current_path,
                    g_cost=g_cost,
                    h_cost=h_cost,
                    f_cost=f_cost,
                    nodes_expanded=nodes_expanded,
                    nodes_generated=nodes_generated,
                    maximum_frontier_size=maximum_frontier_size,
                    goal_found=True,
                    explanation=(
                        f"A* selected {current_node} because it had the lowest estimated total cost f(n)={f_cost}, where g(n)={g_cost} and h(n)={h_cost}."
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
                    optimality_expected=optimality_expected,
                    completeness_expected=self.completeness_expected,
                )

            generated_nodes: list[str] = []
            replaced_nodes: list[str] = []
            skipped_nodes: list[str] = []
            for neighbor in get_traversable_neighbors(graph, current_node):
                edge_cost = calculate_path_cost(graph, current_path + (neighbor,), configuration.optimization_mode, configuration.risk_weight)
                if len(current_path) >= 1:
                    step_cost = edge_cost - g_cost
                else:
                    step_cost = edge_cost
                if step_cost == float("inf"):
                    skipped_nodes.append(neighbor)
                    continue

                tentative_g = g_cost + step_cost
                previous_best = best_g.get(neighbor)
                if previous_best is not None and tentative_g >= previous_best - EPSILON:
                    repeated_state_skips += 1
                    skipped_nodes.append(neighbor)
                    continue

                h_neighbor = calculate_heuristic(graph, neighbor, goal_node, configuration.heuristic_type)
                tentative_f = tentative_g + h_neighbor
                next_path = current_path + (neighbor,)
                seq = next(sequence)
                heapq.heappush(heap, (tentative_f, h_neighbor, neighbor, seq, tentative_g, next_path))
                frontier_state[neighbor] = (tentative_f, h_neighbor, tentative_g, next_path, seq)
                best_g[neighbor] = tentative_g
                nodes_generated += 1
                if previous_best is None:
                    generated_nodes.append(neighbor)
                else:
                    replaced_nodes.append(neighbor)

            maximum_frontier_size = max(maximum_frontier_size, len(frontier_state))
            step = make_step(
                len(steps),
                "expand",
                current_node,
                clean_frontier_entries(
                    serialize_frontier_entry(node, path, priority=fv, g=gv, h=hv, f=fv)
                    for node, (fv, hv, gv, path, _) in frontier_state.items()
                ),
                explored,
                current_path,
                g_cost=g_cost,
                h_cost=h_cost,
                f_cost=f_cost,
                nodes_expanded=nodes_expanded,
                nodes_generated=nodes_generated,
                maximum_frontier_size=maximum_frontier_size,
                explanation=(
                    f"A* selected {current_node} because it had the lowest f(n) value. Its g(n) cost is {g_cost}, h(n) estimate is {h_cost}, and f(n) is {f_cost}. "
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
                        f" Skipped {', '.join(skipped_nodes)} because a cheaper route was already known or the road was blocked."
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
            optimality_expected=optimality_expected,
            completeness_expected=self.completeness_expected,
        )
