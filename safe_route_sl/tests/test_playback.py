"""Tests for automatic playback of stored search histories."""

from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

from algorithms.breadth_first import BreadthFirstSearch
from services.playback_service import (
    PLAYBACK_INTERVALS,
    advance_playback,
    complete_playback,
    normalize_playback_interval,
    normalize_playback_state,
    pause_playback,
    reset_playback,
    start_playback,
)
from services.session_state_service import (
    clear_stale_search_state,
    reset_simulation_state,
    set_simulation_step,
)
from services.simulation_service import get_step, last_step, next_step
from tests.support import make_start_goal_config, make_unweighted_choice_graph


@pytest.fixture
def playback_result():
    """Return a real multi-step result for playback state tests."""
    graph = make_unweighted_choice_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    return BreadthFirstSearch().search(graph, configuration)


def _playing_state(index: int = 0) -> dict[str, object]:
    return {
        "current_step_index": index,
        "simulation_initialized": True,
        "simulation_finished": False,
        "simulation_playing": False,
        "playback_interval_seconds": 1.0,
    }


def test_starting_and_pausing_playback_preserves_current_step(playback_result) -> None:
    state = _playing_state(1)

    assert start_playback(state, playback_result) is True
    assert state["simulation_playing"] is True

    pause_playback(state)

    assert state["simulation_playing"] is False
    assert state["current_step_index"] == 1
    assert get_step(playback_result, 1) is playback_result.steps[1]


def test_active_playback_advances_exactly_one_original_step(playback_result) -> None:
    state = _playing_state()
    start_playback(state, playback_result)

    selected_step = advance_playback(state, playback_result)

    assert state["current_step_index"] == 1
    assert selected_step is playback_result.steps[1]
    assert state["simulation_playing"] is True


def test_playback_stops_and_marks_finished_at_final_step(playback_result) -> None:
    final_index = last_step(playback_result).step_number
    state = _playing_state(final_index - 1)
    start_playback(state, playback_result)

    selected_step = advance_playback(state, playback_result)

    assert selected_step is last_step(playback_result)
    assert state["current_step_index"] == final_index
    assert state["simulation_finished"] is True
    assert state["simulation_playing"] is False
    assert start_playback(state, playback_result) is False


def test_final_failure_step_is_treated_as_playback_completion() -> None:
    graph = make_unweighted_choice_graph()
    graph.remove_edge("B", "G")
    graph.remove_edge("D", "G")
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    failure_result = BreadthFirstSearch().search(graph, configuration)
    final_index = last_step(failure_result).step_number
    state = _playing_state(final_index - 1)
    start_playback(state, failure_result)

    selected_step = advance_playback(state, failure_result)

    assert selected_step is last_step(failure_result)
    assert selected_step.event_type == "failure"
    assert state["simulation_finished"] is True
    assert state["simulation_playing"] is False


def test_reset_and_run_to_completion_stop_playback(playback_result) -> None:
    state = _playing_state(2)
    state["simulation_playing"] = True

    reset_step = reset_playback(state, playback_result)

    assert reset_step is playback_result.steps[0]
    assert state["current_step_index"] == 0
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False

    start_playback(state, playback_result)
    completed_step = complete_playback(state, playback_result)

    assert completed_step is last_step(playback_result)
    assert state["simulation_finished"] is True
    assert state["simulation_playing"] is False


def test_new_search_starts_paused_at_step_zero_and_preserves_speed() -> None:
    state = _playing_state(4)
    state["simulation_playing"] = True
    state["simulation_finished"] = True
    state["playback_interval_seconds"] = 0.5

    reset_simulation_state(state)

    assert state["current_step_index"] == 0
    assert state["simulation_initialized"] is True
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False
    assert state["playback_interval_seconds"] == 0.5


def test_configuration_change_stops_and_clears_playback(playback_result) -> None:
    state = _playing_state(2)
    state.update(
        latest_result=playback_result,
        latest_configuration=object(),
        latest_scenario_id="normal_conditions",
        latest_configuration_signature=("old",),
        search_error="stale",
        simulation_playing=True,
    )

    assert clear_stale_search_state(state, ("new",)) is True
    assert state["latest_result"] is None
    assert state["search_error"] is None
    assert state["current_step_index"] == 0
    assert state["simulation_playing"] is False


def test_speed_labels_map_to_increasing_intervals() -> None:
    assert PLAYBACK_INTERVALS == {
        "Very Fast": 0.25,
        "Fast": 0.5,
        "Normal": 1.0,
        "Slow": 1.5,
        "Very Slow": 2.0,
    }
    state = {"playback_interval_seconds": 99.0}
    assert normalize_playback_interval(state) == 1.0
    assert state["playback_interval_seconds"] == 1.0


def test_invalid_state_without_result_is_cleared_safely() -> None:
    state = _playing_state(500)
    state["simulation_playing"] = True

    assert normalize_playback_state(state, None) is None
    assert advance_playback(state, None) is None
    assert state["current_step_index"] == 0
    assert state["simulation_initialized"] is False
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False


def test_invalid_index_is_clamped_and_manual_navigation_works_paused(playback_result) -> None:
    state = _playing_state(10_000)

    assert normalize_playback_state(state, playback_result) is last_step(playback_result)
    assert state["simulation_finished"] is True

    reset_playback(state, playback_result)
    selected_step = next_step(playback_result, state["current_step_index"])
    set_simulation_step(state, playback_result, selected_step)

    assert state["simulation_playing"] is False
    assert selected_step is playback_result.steps[1]


def test_playback_does_not_mutate_result_or_steps(playback_result) -> None:
    original_result = deepcopy(playback_result)
    original_steps = playback_result.steps
    original_step_instances = tuple(id(step) for step in playback_result.steps)
    state = _playing_state()

    start_playback(state, playback_result)
    advance_playback(state, playback_result)
    pause_playback(state)
    complete_playback(state, playback_result)
    reset_playback(state, playback_result)

    assert playback_result == original_result
    assert playback_result.steps is original_steps
    assert tuple(id(step) for step in playback_result.steps) == original_step_instances


def test_page_uses_one_step_reruns_and_stored_history_only() -> None:
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

    assert len(run_search_calls) == 1
    assert "if run_clicked:" in source
    assert "result.steps" not in source
    assert "advance_playback(st.session_state, st.session_state.latest_result)" in source
    assert "time.sleep(normalize_playback_interval(st.session_state))" in source
    assert "st.rerun()" in source
    assert "st.session_state.playback_interval_seconds = PLAYBACK_INTERVALS[selected_speed_label]" in source
    assert 'st.caption("Playback controls")' in source
    assert 'label_visibility="collapsed"' in source
    assert ':has([aria-label="Playback Speed"])' in source
    assert "text-align: center !important" in source
    assert "build_search_step_figure(" in source
    assert "render_search_step_state(" in source
