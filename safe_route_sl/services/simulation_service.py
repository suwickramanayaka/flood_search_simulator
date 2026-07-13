"""Deterministic navigation helpers for recorded search histories."""

from __future__ import annotations

from models.search_models import SearchResult, SearchStep
from utils.exceptions import SimulationNavigationError


def _validate_result(result: SearchResult) -> None:
    """Raise a domain error when ``result`` is not a search result."""
    if not isinstance(result, SearchResult):
        raise SimulationNavigationError("Simulation navigation requires a SearchResult instance")


def _validate_index(step_index: int) -> None:
    """Raise a domain error when a step index is not an integer."""
    if isinstance(step_index, bool) or not isinstance(step_index, int):
        raise SimulationNavigationError(
            f"Simulation step index must be an integer, got {step_index!r}"
        )


def _clamp_index(result: SearchResult, step_index: int) -> int:
    """Return ``step_index`` clamped to the available history bounds."""
    _validate_result(result)
    _validate_index(step_index)
    if not result.steps:
        raise SimulationNavigationError("Cannot navigate a search result with an empty step history")
    return max(0, min(step_index, len(result.steps) - 1))


def get_step(result: SearchResult, step_index: int) -> SearchStep:
    """Return the existing step at ``step_index``, clamped to valid bounds."""
    return result.steps[_clamp_index(result, step_index)]


def first_step(result: SearchResult) -> SearchStep:
    """Return the first existing step in ``result``."""
    return get_step(result, 0)


def last_step(result: SearchResult) -> SearchStep:
    """Return the last existing step in ``result``."""
    _validate_result(result)
    if not result.steps:
        raise SimulationNavigationError("Cannot navigate a search result with an empty step history")
    return result.steps[-1]


def next_step(result: SearchResult, current_index: int) -> SearchStep:
    """Return the next existing step, remaining at the end when complete."""
    _validate_index(current_index)
    return get_step(result, current_index + 1)


def previous_step(result: SearchResult, current_index: int) -> SearchStep:
    """Return the previous existing step, remaining at the start at the lower bound."""
    _validate_index(current_index)
    return get_step(result, current_index - 1)


def total_steps(result: SearchResult) -> int:
    """Return the number of recorded steps in ``result``."""
    _validate_result(result)
    return len(result.steps)


def simulation_complete(result: SearchResult, current_index: int) -> bool:
    """Return whether navigation is at or beyond the final recorded step."""
    _validate_result(result)
    _validate_index(current_index)
    if not result.steps:
        return True
    return _clamp_index(result, current_index) == len(result.steps) - 1
