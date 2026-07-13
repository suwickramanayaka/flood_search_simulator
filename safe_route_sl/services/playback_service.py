"""Pure state transitions for automatic playback of stored search steps."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from models.search_models import SearchResult, SearchStep
from services.session_state_service import clear_simulation_state, set_simulation_step
from services.simulation_service import first_step, get_step, last_step, next_step, total_steps


DEFAULT_PLAYBACK_INTERVAL_SECONDS = 1.0
PLAYBACK_INTERVALS: dict[str, float] = {
    "Very Fast": 0.25,
    "Fast": 0.5,
    "Normal": 1.0,
    "Slow": 1.5,
    "Very Slow": 2.0,
}
PLAYBACK_LABELS_BY_INTERVAL = {
    interval: label for label, interval in PLAYBACK_INTERVALS.items()
}


def normalize_playback_interval(session_state: MutableMapping[str, Any]) -> float:
    """Store and return a supported playback interval."""
    interval = session_state.get(
        "playback_interval_seconds",
        DEFAULT_PLAYBACK_INTERVAL_SECONDS,
    )
    if interval not in PLAYBACK_LABELS_BY_INTERVAL:
        interval = DEFAULT_PLAYBACK_INTERVAL_SECONDS
        session_state["playback_interval_seconds"] = interval
    return float(interval)


def normalize_playback_state(
    session_state: MutableMapping[str, Any],
    result: SearchResult | None,
) -> SearchStep | None:
    """Clamp playback state to a valid stored step or clear invalid state."""
    if not isinstance(result, SearchResult) or total_steps(result) == 0:
        clear_simulation_state(session_state)
        return None

    current_index = session_state.get("current_step_index", 0)
    if isinstance(current_index, bool) or not isinstance(current_index, int):
        current_index = 0

    current_step = get_step(result, current_index)
    set_simulation_step(session_state, result, current_step)
    if session_state["simulation_finished"]:
        session_state["simulation_playing"] = False
    return current_step


def start_playback(
    session_state: MutableMapping[str, Any],
    result: SearchResult | None,
) -> bool:
    """Start playback when a non-final stored step is available."""
    current_step = normalize_playback_state(session_state, result)
    if current_step is None or session_state["simulation_finished"]:
        session_state["simulation_playing"] = False
        return False

    session_state["simulation_playing"] = True
    return True


def pause_playback(session_state: MutableMapping[str, Any]) -> None:
    """Pause playback without changing the selected step or result."""
    session_state["simulation_playing"] = False


def advance_playback(
    session_state: MutableMapping[str, Any],
    result: SearchResult | None,
) -> SearchStep | None:
    """Advance active playback by exactly one existing search step."""
    current_step = normalize_playback_state(session_state, result)
    if current_step is None or not session_state.get("simulation_playing", False):
        return current_step

    selected_step = next_step(result, current_step.step_number)
    set_simulation_step(session_state, result, selected_step)
    if session_state["simulation_finished"]:
        session_state["simulation_playing"] = False
    return selected_step


def reset_playback(
    session_state: MutableMapping[str, Any],
    result: SearchResult,
) -> SearchStep:
    """Stop playback and return to the first stored search step."""
    session_state["simulation_playing"] = False
    selected_step = first_step(result)
    set_simulation_step(session_state, result, selected_step)
    return selected_step


def complete_playback(
    session_state: MutableMapping[str, Any],
    result: SearchResult,
) -> SearchStep:
    """Stop playback and select the final stored search step."""
    session_state["simulation_playing"] = False
    selected_step = last_step(result)
    set_simulation_step(session_state, result, selected_step)
    return selected_step
