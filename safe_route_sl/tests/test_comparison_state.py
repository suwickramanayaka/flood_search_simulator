"""Tests for stored comparison session-state transitions."""

from __future__ import annotations

from services.comparison_service import AlgorithmComparisonRecord
from services.comparison_state_service import (
    build_comparison_signature,
    clear_stale_comparison_state,
    initialize_comparison_state,
    store_comparison_error,
    store_comparison_results,
)


def _record() -> AlgorithmComparisonRecord:
    return AlgorithmComparisonRecord(
        algorithm_name="Breadth-First Search",
        found=True,
        path=("A", "B"),
        total_cost=1.0,
        nodes_expanded=1,
        nodes_generated=2,
        maximum_frontier_size=2,
        execution_time_ms=0.5,
        path_length_edges=1,
        optimality_expected=False,
        completeness_expected=True,
    )


def test_comparison_state_initialization_and_signature() -> None:
    state: dict[str, object] = {}

    initialize_comparison_state(state)
    signature = build_comparison_signature("normal", "A", "G", "balanced", 4, "haversine")

    assert state["latest_comparison_records"] is None
    assert state["latest_comparison_signature"] is None
    assert state["comparison_error"] is None
    assert signature == ("normal", "A", "G", "balanced", 4.0, "haversine")


def test_comparison_results_are_stored_by_original_tuple_identity() -> None:
    state: dict[str, object] = {"comparison_error": "stale"}
    records = (_record(),)
    signature = ("configuration",)

    store_comparison_results(state, records, signature)

    assert state["latest_comparison_records"] is records
    assert state["latest_comparison_signature"] is signature
    assert state["comparison_error"] is None


def test_configuration_change_clears_stale_results_and_errors() -> None:
    records = (_record(),)
    state: dict[str, object] = {
        "latest_comparison_records": records,
        "latest_comparison_signature": ("old",),
        "comparison_error": "stale error",
    }

    assert clear_stale_comparison_state(state, ("new",)) is True
    assert state["latest_comparison_records"] is None
    assert state["latest_comparison_signature"] is None
    assert state["comparison_error"] is None


def test_unchanged_configuration_preserves_stored_comparison() -> None:
    records = (_record(),)
    signature = ("same",)
    state: dict[str, object] = {
        "latest_comparison_records": records,
        "latest_comparison_signature": signature,
        "comparison_error": None,
    }

    assert clear_stale_comparison_state(state, signature) is False
    assert state["latest_comparison_records"] is records


def test_comparison_error_replaces_stale_records_and_tracks_signature() -> None:
    state: dict[str, object] = {"latest_comparison_records": (_record(),)}
    signature = ("failed",)

    store_comparison_error(state, signature, "comparison failed")

    assert state["latest_comparison_records"] is None
    assert state["latest_comparison_signature"] is signature
    assert state["comparison_error"] == "comparison failed"
