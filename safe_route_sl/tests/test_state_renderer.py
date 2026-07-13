"""Tests for dynamic search-state data preparation."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from algorithms.astar import AStarSearch
from algorithms.breadth_first import BreadthFirstSearch
from algorithms.greedy_best_first import GreedyBestFirstSearch
from algorithms.uniform_cost import UniformCostSearch
from models.search_models import SearchStep
from tests.support import make_start_goal_config, make_weighted_choice_graph
from utils.constants import DISTANCE_MODE
from visualizations.state_renderer import (
    build_frontier_dataframe,
    build_step_cost_values,
    build_step_summary_values,
    format_explored_nodes,
    is_completed_step,
)


@pytest.fixture
def graph():
    """Return a graph with recognizable human-readable node names."""
    value = make_weighted_choice_graph()
    value.nodes["A"]["name"] = "Millaniya Village"
    value.nodes["C"]["name"] = "Temple Shelter"
    return value


def _result_for(graph, algorithm_name: str, heuristic_type: str = "zero"):
    configuration = make_start_goal_config(
        algorithm_name,
        "A",
        "G",
        optimization_mode=DISTANCE_MODE,
        heuristic_type=heuristic_type,
    )
    implementations = {
        "Breadth-First Search": BreadthFirstSearch,
        "Uniform-Cost Search": UniformCostSearch,
        "Greedy Best-First Search": GreedyBestFirstSearch,
        "A* Search": AStarSearch,
    }
    return implementations[algorithm_name]().search(graph, configuration), configuration


def test_initialization_and_bfs_steps_hide_costs_and_humanize_frontier(graph) -> None:
    result, configuration = _result_for(graph, "Breadth-First Search")
    initial_step = result.steps[0]
    expansion_step = result.steps[1]

    assert initial_step.event_type == "initialize"
    assert format_explored_nodes(graph, initial_step) == "No nodes have been explored yet."
    assert build_step_cost_values(initial_step, configuration) == {}
    assert build_step_cost_values(expansion_step, configuration) == {}

    dataframe = build_frontier_dataframe(graph, initial_step)
    assert list(dataframe.columns) == ["Node", "Path"]
    assert dataframe.iloc[0]["Node"] == "Millaniya Village"
    assert dataframe.iloc[0]["Path"] == "Millaniya Village"


@pytest.mark.parametrize(
    ("algorithm_name", "heuristic_type", "expected_keys"),
    [
        ("Uniform-Cost Search", "zero", {"g(n)"}),
        ("Greedy Best-First Search", "zero", {"g(n)", "h(n)"}),
        ("A* Search", "zero", {"g(n)", "h(n)", "f(n)"}),
    ],
)
def test_algorithm_specific_step_costs(graph, algorithm_name, heuristic_type, expected_keys) -> None:
    result, configuration = _result_for(graph, algorithm_name, heuristic_type)
    step_with_costs = next(
        step
        for step in result.steps
        if all(
            getattr(step, field_name) is not None
            for field_name in {
                "g(n)": "g_cost",
                "h(n)": "h_cost",
                "f(n)": "f_cost",
            }.values()
            if field_name.replace("_cost", "(n)") in expected_keys
        )
    )

    assert set(build_step_cost_values(step_with_costs, configuration)) == expected_keys


def test_frontier_table_hides_irrelevant_columns_and_humanizes_paths(graph) -> None:
    result, _ = _result_for(graph, "A* Search", "zero")
    populated_step = result.steps[1]
    dataframe = build_frontier_dataframe(graph, populated_step)

    assert list(dataframe.columns) == ["Node", "Priority", "g", "h", "f", "Path"]
    assert any("Millaniya Village" in path for path in dataframe["Path"])
    assert all("{" not in path for path in dataframe["Path"])

    empty_frontier_step = replace(populated_step, frontier_entries=(), frontier_nodes=())
    empty_dataframe = build_frontier_dataframe(graph, empty_frontier_step)
    assert empty_dataframe.empty
    assert list(empty_dataframe.columns) == ["Node", "Path"]


def test_explored_nodes_and_current_path_use_readable_names(graph) -> None:
    step = SearchStep(
        step_number=1,
        event_type="expand",
        current_node="C",
        frontier_nodes=(),
        explored_nodes=("A", "C"),
        current_path=("A", "C", "G"),
        explanation="Expanded a readable path.",
    )

    assert format_explored_nodes(graph, step) == "Millaniya Village, Temple Shelter"
    dataframe = build_frontier_dataframe(
        graph,
        replace(
            step,
            frontier_entries=(
                {"node": "G", "priority": None, "g": None, "h": None, "f": None, "path": step.current_path},
            ),
        ),
    )
    assert dataframe.iloc[0]["Path"] == "Millaniya Village → Temple Shelter → Goal Shelter"


def test_goal_and_failure_steps_are_completed(graph) -> None:
    result, _ = _result_for(graph, "Breadth-First Search")
    assert result.steps[-1].goal_found is True
    assert is_completed_step(result.steps[-1]) is True

    failure_step = replace(
        result.steps[-1],
        event_type="failure",
        goal_found=False,
        current_path=("A",),
    )
    intermediate_step = replace(result.steps[1], event_type="expand", goal_found=False)
    assert is_completed_step(failure_step) is True
    assert is_completed_step(intermediate_step) is False


def test_step_summary_values_are_compact_and_human_readable(graph) -> None:
    result, _ = _result_for(graph, "Breadth-First Search")
    summary = dict(build_step_summary_values(graph, result.steps[-1]))

    assert summary == {
        "Step": str(result.steps[-1].step_number),
        "Event": "Goal",
        "Current node": "Goal Shelter",
        "Goal status": "Reached",
    }


def test_page_uses_step_renderer_without_direct_step_or_search_history_rendering() -> None:
    page_path = Path(__file__).resolve().parents[1] / "pages" / "1_Interactive_Simulation.py"
    source = page_path.read_text(encoding="utf-8")
    syntax_tree = ast.parse(source)
    run_search_calls = [
        node
        for node in ast.walk(syntax_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_search"
    ]

    assert "render_search_step_state" in source
    assert "render_final_search_state" not in source
    assert 'st.write(f"Event Type:' not in source
    assert "result.steps" not in source
    assert len(run_search_calls) == 1
