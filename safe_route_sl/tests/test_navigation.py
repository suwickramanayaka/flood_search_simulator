"""Tests for session-state navigation through stored search steps."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from algorithms.breadth_first import BreadthFirstSearch
from services.session_state_service import get_simulation_progress, set_simulation_step
from services.simulation_service import (
    first_step,
    get_step,
    last_step,
    next_step,
    previous_step,
    simulation_complete,
)
from tests.support import make_start_goal_config, make_unweighted_choice_graph


@pytest.fixture
def navigation_result():
    """Return a real multi-step search result for navigation tests."""
    graph = make_unweighted_choice_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    return BreadthFirstSearch().search(graph, configuration)


def test_previous_and_next_update_the_current_step(navigation_result) -> None:
    state = {
        "current_step_index": 0,
        "simulation_initialized": True,
        "simulation_finished": False,
    }

    set_simulation_step(state, navigation_result, next_step(navigation_result, 0))
    assert state["current_step_index"] == 1
    assert get_step(navigation_result, state["current_step_index"]) is navigation_result.steps[1]

    set_simulation_step(state, navigation_result, previous_step(navigation_result, 1))
    assert state["current_step_index"] == 0
    assert get_step(navigation_result, state["current_step_index"]) is first_step(navigation_result)


def test_navigation_boundaries_remain_on_existing_steps(navigation_result) -> None:
    final_step = last_step(navigation_result)

    assert previous_step(navigation_result, 0) is first_step(navigation_result)
    assert next_step(navigation_result, final_step.step_number) is final_step
    assert simulation_complete(navigation_result, 0) is False
    assert simulation_complete(navigation_result, final_step.step_number) is True


def test_reset_returns_to_first_step_without_clearing_result(navigation_result) -> None:
    state = {
        "latest_result": navigation_result,
        "current_step_index": last_step(navigation_result).step_number,
        "simulation_initialized": True,
        "simulation_finished": True,
    }

    set_simulation_step(state, navigation_result, first_step(navigation_result))

    assert state["latest_result"] is navigation_result
    assert state["current_step_index"] == 0
    assert state["simulation_finished"] is False


def test_run_to_completion_selects_final_step_without_clearing_result(navigation_result) -> None:
    state = {
        "latest_result": navigation_result,
        "current_step_index": 0,
        "simulation_initialized": True,
        "simulation_finished": False,
    }

    final_step = last_step(navigation_result)
    set_simulation_step(state, navigation_result, final_step)

    assert state["latest_result"] is navigation_result
    assert state["current_step_index"] == final_step.step_number
    assert state["simulation_finished"] is True


def test_step_counter_and_progress_follow_current_index(navigation_result) -> None:
    first_number, step_count, first_progress = get_simulation_progress(navigation_result, 0)
    final_number, final_count, final_progress = get_simulation_progress(
        navigation_result,
        last_step(navigation_result).step_number,
    )

    assert first_number == 1
    assert first_progress == pytest.approx(1 / step_count)
    assert final_number == final_count == step_count
    assert final_progress == pytest.approx(1.0)


def test_interactive_page_contains_only_one_search_execution_call() -> None:
    page_path = Path(__file__).resolve().parents[1] / "pages" / "1_Interactive_Simulation.py"
    syntax_tree = ast.parse(page_path.read_text(encoding="utf-8"))
    run_search_calls = [
        node
        for node in ast.walk(syntax_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_search"
    ]

    assert len(run_search_calls) == 1


def test_reset_controls_uses_a_callback_instead_of_late_widget_assignment() -> None:
    page_path = Path(__file__).resolve().parents[1] / "pages" / "1_Interactive_Simulation.py"
    source = page_path.read_text(encoding="utf-8")

    assert '"Reset Controls"' in source
    assert "on_click=reset_controls" in source
    assert "st.session_state.scenario_id =" not in source
    assert "st.session_state.algorithm =" not in source
