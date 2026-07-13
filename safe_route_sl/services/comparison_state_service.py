"""Session-state transitions for stored algorithm comparisons."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any

from services.comparison_service import AlgorithmComparisonRecord


COMPARISON_STATE_DEFAULTS: dict[str, object] = {
    "latest_comparison_records": None,
    "latest_comparison_signature": None,
    "comparison_error": None,
}


def initialize_comparison_state(session_state: MutableMapping[str, Any]) -> None:
    """Add missing comparison keys without replacing existing values."""
    for key, value in COMPARISON_STATE_DEFAULTS.items():
        session_state.setdefault(key, value)


def build_comparison_signature(
    scenario_id: str,
    start_node: str,
    goal_node: str,
    optimization_mode: str,
    risk_weight: float,
    heuristic_type: str,
) -> tuple[object, ...]:
    """Return the configuration identity for a comparison run."""
    return (
        scenario_id,
        start_node,
        goal_node,
        optimization_mode,
        float(risk_weight),
        heuristic_type,
    )


def clear_comparison_state(session_state: MutableMapping[str, Any]) -> None:
    """Clear stored comparison results, signature, and errors."""
    session_state["latest_comparison_records"] = None
    session_state["latest_comparison_signature"] = None
    session_state["comparison_error"] = None


def clear_stale_comparison_state(
    session_state: MutableMapping[str, Any],
    current_signature: tuple[object, ...],
) -> bool:
    """Clear comparison output when its generating configuration changed."""
    stored_signature = session_state.get("latest_comparison_signature")
    if stored_signature is None or stored_signature == current_signature:
        return False
    clear_comparison_state(session_state)
    return True


def store_comparison_results(
    session_state: MutableMapping[str, Any],
    records: tuple[AlgorithmComparisonRecord, ...],
    signature: tuple[object, ...],
) -> None:
    """Store one completed comparison and clear its stale error."""
    session_state["latest_comparison_records"] = records
    session_state["latest_comparison_signature"] = signature
    session_state["comparison_error"] = None


def store_comparison_error(
    session_state: MutableMapping[str, Any],
    signature: tuple[object, ...],
    message: str,
) -> None:
    """Store a comparison-level error without retaining stale results."""
    session_state["latest_comparison_records"] = None
    session_state["latest_comparison_signature"] = signature
    session_state["comparison_error"] = message
