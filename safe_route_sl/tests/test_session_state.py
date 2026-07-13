"""Tests for simulation-related session-state transitions."""

from __future__ import annotations

from services.session_state_service import (
    clear_search_state,
    clear_simulation_state,
    clear_stale_search_state,
    initialize_simulation_state,
    reset_simulation_state,
    reset_control_state,
)


def test_simulation_state_initialization_preserves_existing_values() -> None:
    state = {"current_step_index": 3}

    initialize_simulation_state(state)

    assert state["current_step_index"] == 3
    assert state["simulation_initialized"] is False
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False
    assert state["playback_interval_seconds"] == 1.0


def test_reset_initializes_simulation_at_first_step() -> None:
    state = {
        "current_step_index": 5,
        "simulation_initialized": False,
        "simulation_finished": True,
        "simulation_playing": True,
        "playback_interval_seconds": 0.5,
    }

    reset_simulation_state(state)

    assert state["current_step_index"] == 0
    assert state["simulation_initialized"] is True
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False
    assert state["playback_interval_seconds"] == 0.5


def test_clear_simulation_state_resets_all_playback_flags() -> None:
    state = {
        "current_step_index": 4,
        "simulation_initialized": True,
        "simulation_finished": True,
        "simulation_playing": True,
        "playback_interval_seconds": 0.25,
    }

    clear_simulation_state(state)

    assert state["current_step_index"] == 0
    assert state["simulation_initialized"] is False
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False
    assert state["playback_interval_seconds"] == 1.0


def test_clear_search_state_removes_results_errors_and_playback() -> None:
    state = {
        "latest_result": object(),
        "latest_configuration": object(),
        "latest_scenario_id": "normal_conditions",
        "latest_configuration_signature": ("old",),
        "search_error": "stale error",
        "current_step_index": 4,
        "simulation_initialized": True,
        "simulation_finished": True,
        "simulation_playing": True,
    }

    clear_search_state(state)

    assert state["latest_result"] is None
    assert state["latest_configuration"] is None
    assert state["latest_scenario_id"] is None
    assert state["latest_configuration_signature"] is None
    assert state["search_error"] is None
    assert state["current_step_index"] == 0
    assert state["simulation_initialized"] is False
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False


def test_configuration_change_clears_stale_search_and_simulation_state() -> None:
    state = {
        "latest_result": object(),
        "latest_configuration": object(),
        "latest_scenario_id": "normal_conditions",
        "latest_configuration_signature": ("old",),
        "search_error": "stale error",
        "current_step_index": 2,
        "simulation_initialized": True,
        "simulation_finished": True,
        "simulation_playing": True,
    }

    changed = clear_stale_search_state(state, ("new",))

    assert changed is True
    assert state["latest_result"] is None
    assert state["search_error"] is None
    assert state["current_step_index"] == 0
    assert state["simulation_initialized"] is False
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False


def test_unchanged_or_untracked_configuration_preserves_state() -> None:
    result = object()
    state = {
        "latest_result": result,
        "latest_configuration_signature": ("same",),
    }

    assert clear_stale_search_state(state, ("same",)) is False
    assert state["latest_result"] is result

    state["latest_configuration_signature"] = None
    assert clear_stale_search_state(state, ("new",)) is False
    assert state["latest_result"] is result


def test_reset_control_state_clears_widgets_result_error_and_playback() -> None:
    state = {
        "scenario_id": "severe_flooding",
        "algorithm": "A* Search",
        "start_node": "A",
        "goal_node": "H",
        "optimization_mode": "distance",
        "risk_weight": 8.0,
        "heuristic_type": "haversine",
        "latest_result": object(),
        "latest_configuration": object(),
        "latest_scenario_id": "severe_flooding",
        "latest_configuration_signature": ("stale",),
        "search_error": "stale error",
        "current_step_index": 7,
        "simulation_initialized": True,
        "simulation_finished": True,
        "simulation_playing": True,
    }

    reset_control_state(state)

    for key in (
        "scenario_id",
        "algorithm",
        "start_node",
        "goal_node",
        "optimization_mode",
        "risk_weight",
        "heuristic_type",
    ):
        assert key not in state
    assert state["latest_result"] is None
    assert state["latest_configuration"] is None
    assert state["search_error"] is None
    assert state["current_step_index"] == 0
    assert state["simulation_initialized"] is False
    assert state["simulation_finished"] is False
    assert state["simulation_playing"] is False
