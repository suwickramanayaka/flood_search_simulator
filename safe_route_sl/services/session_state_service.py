"""Session-state transitions for search-result playback."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from models.search_models import SearchResult, SearchStep
from services.simulation_service import get_step, simulation_complete, total_steps


SIMULATION_STATE_DEFAULTS: dict[str, object] = {
    "current_step_index": 0,
    "simulation_initialized": False,
    "simulation_finished": False,
    "simulation_playing": False,
    "playback_interval_seconds": 1.0,
}

CONTROL_WIDGET_KEYS = (
    "scenario_id",
    "algorithm",
    "start_node",
    "goal_node",
    "optimization_mode",
    "risk_weight",
    "heuristic_type",
    "playback_speed_label",
)


def initialize_simulation_state(session_state: MutableMapping[str, Any]) -> None:
    """Add missing simulation keys without replacing existing state."""
    for key, value in SIMULATION_STATE_DEFAULTS.items():
        session_state.setdefault(key, value)


def reset_simulation_state(session_state: MutableMapping[str, Any]) -> None:
    """Initialize playback at the first step of a newly stored result."""
    session_state["current_step_index"] = 0
    session_state["simulation_initialized"] = True
    session_state["simulation_finished"] = False
    session_state["simulation_playing"] = False


def clear_simulation_state(session_state: MutableMapping[str, Any]) -> None:
    """Clear playback progress when no current result is available."""
    session_state["current_step_index"] = 0
    session_state["simulation_initialized"] = False
    session_state["simulation_finished"] = False
    session_state["simulation_playing"] = False
    session_state["playback_interval_seconds"] = 1.0


def clear_search_state(session_state: MutableMapping[str, Any]) -> None:
    """Clear stored search output, errors, and all playback state."""
    session_state["latest_result"] = None
    session_state["latest_configuration"] = None
    session_state["latest_scenario_id"] = None
    session_state["latest_configuration_signature"] = None
    session_state["search_error"] = None
    clear_simulation_state(session_state)


def reset_control_state(session_state: MutableMapping[str, Any]) -> None:
    """Clear widget values before Streamlit reconstructs the control widgets."""
    for key in CONTROL_WIDGET_KEYS:
        session_state.pop(key, None)
    clear_search_state(session_state)


def clear_stale_search_state(
    session_state: MutableMapping[str, Any],
    current_signature: tuple[object, ...],
) -> bool:
    """Clear stored search state when the current configuration has changed."""
    stored_signature = session_state.get("latest_configuration_signature")
    if stored_signature is None or stored_signature == current_signature:
        return False

    clear_search_state(session_state)
    return True


def set_simulation_step(
    session_state: MutableMapping[str, Any],
    result: SearchResult,
    step: SearchStep,
) -> None:
    """Store a selected existing step and update playback completion state."""
    session_state["current_step_index"] = step.step_number
    session_state["simulation_initialized"] = True
    session_state["simulation_finished"] = simulation_complete(result, step.step_number)


def get_simulation_progress(result: SearchResult, current_index: int) -> tuple[int, int, float]:
    """Return the one-based step number, total count, and progress fraction."""
    current_step = get_step(result, current_index)
    step_count = total_steps(result)
    current_number = current_step.step_number + 1
    return current_number, step_count, current_number / step_count
