"""Integration tests using the SafeRouteSL dataset."""

from __future__ import annotations

from algorithms.astar import AStarSearch
from algorithms.breadth_first import BreadthFirstSearch
from algorithms.depth_first import DepthFirstSearch
from algorithms.greedy_best_first import GreedyBestFirstSearch
from algorithms.uniform_cost import UniformCostSearch
from services.graph_service import create_traversable_graph
from services.scenario_service import apply_scenario_by_id, load_scenarios
from tests.support import DATA_DIR, load_project_dataset_graph, make_start_goal_config


def test_real_dataset_integration_across_algorithms() -> None:
    graph = load_project_dataset_graph()
    scenarios = load_scenarios(DATA_DIR / "scenarios.json")
    scenario_graph = apply_scenario_by_id(graph, scenarios, "bridge_flooded")

    configurations = {
        "Breadth-First Search": make_start_goal_config("Breadth-First Search", "A", "H"),
        "Depth-First Search": make_start_goal_config("Depth-First Search", "A", "H"),
        "Uniform-Cost Search": make_start_goal_config("Uniform-Cost Search", "A", "H", optimization_mode="balanced"),
        "Greedy Best-First Search": make_start_goal_config("Greedy Best-First Search", "A", "H", optimization_mode="balanced", heuristic_type="haversine"),
        "A* Search": make_start_goal_config("A* Search", "A", "H", optimization_mode="distance", heuristic_type="zero"),
    }
    algorithms = [
        BreadthFirstSearch(),
        DepthFirstSearch(),
        UniformCostSearch(),
        GreedyBestFirstSearch(),
        AStarSearch(),
    ]

    for algorithm in algorithms:
        result = algorithm.search(scenario_graph, configurations[algorithm.name])
        assert result.steps
        assert result.steps[0].event_type == "initialize"
        assert result.steps[-1].event_type in {"goal", "failure"}
        if result.found:
            assert result.final_path[0] == "A"
            assert result.final_path[-1] == "H"
            for source, target in zip(result.final_path, result.final_path[1:]):
                assert scenario_graph.has_edge(source, target)
                assert scenario_graph[source][target]["blocked"] is False
        assert result.maximum_frontier_size >= 1

    assert create_traversable_graph(scenario_graph).has_edge("K", "L") is False