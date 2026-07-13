"""Depth-first search for SafeRouteSL."""

from __future__ import annotations

from time import perf_counter

import networkx as nx

from algorithms.base import (
    SearchAlgorithm,
    build_failure_result,
    build_start_equals_goal_result,
    build_success_result,
    calculate_path_cost,
    make_initial_step,
    make_step,
    serialize_frontier_entry,
)
from models.configuration import SearchConfiguration
from models.search_models import SearchResult
from services.graph_service import get_traversable_neighbors


class DepthFirstSearch(SearchAlgorithm):
    name = "Depth-First Search"
    optimality_expected = False
    completeness_expected = True

    def search(self, graph: nx.Graph, configuration: SearchConfiguration) -> SearchResult:
        start_time = perf_counter()
        start_node = configuration.start_node
        goal_node = configuration.goal_node

        frontier = [(start_node, (start_node,))]
        frontier_members = {start_node}
        explored: set[str] = set()
        repeated_state_skips = 0
        nodes_generated = 1
        nodes_expanded = 0
        maximum_frontier_size = 1
        steps = [
            make_initial_step(
                start_node,
                [serialize_frontier_entry(start_node, (start_node,))],
                explanation=f"The search starts at {start_node}. The stack contains only the start node.",
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
                nodes_expanded=1,
                nodes_generated=1,
                maximum_frontier_size=1,
                goal_found=True,
                explanation=f"DFS reached the goal immediately at {start_node}.",
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

        while frontier:
            current_node, current_path = frontier.pop()
            frontier_members.remove(current_node)

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
                    [serialize_frontier_entry(node, path) for node, path in frontier],
                    explored,
                    current_path,
                    nodes_expanded=nodes_expanded,
                    nodes_generated=nodes_generated,
                    maximum_frontier_size=maximum_frontier_size,
                    goal_found=True,
                    explanation=f"DFS removed {current_node} from the top of the LIFO stack and found the goal.",
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
            neighbors = list(reversed(get_traversable_neighbors(graph, current_node)))
            for neighbor in neighbors:
                if neighbor in explored or neighbor in frontier_members:
                    repeated_state_skips += 1
                    skipped_nodes.append(neighbor)
                    continue
                next_path = current_path + (neighbor,)
                frontier.append((neighbor, next_path))
                frontier_members.add(neighbor)
                nodes_generated += 1
                generated_nodes.append(neighbor)

            maximum_frontier_size = max(maximum_frontier_size, len(frontier))
            step = make_step(
                len(steps),
                "expand",
                current_node,
                [serialize_frontier_entry(node, path) for node, path in frontier],
                explored,
                current_path,
                nodes_expanded=nodes_expanded,
                nodes_generated=nodes_generated,
                maximum_frontier_size=maximum_frontier_size,
                explanation=(
                    f"DFS removed {current_node} from the top of the LIFO stack and continued along the most recently discovered branch. "
                    + (
                        f"It pushed {', '.join(generated_nodes[::-1])} onto the stack."
                        if generated_nodes
                        else "It did not push any new neighbours."
                    )
                    + (
                        f" Skipped {', '.join(skipped_nodes)} because they were already explored or on the stack."
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
            explanation=(
                f"The stack is empty. No traversable route exists between {start_node} and {goal_node} under the current scenario."
            ),
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
