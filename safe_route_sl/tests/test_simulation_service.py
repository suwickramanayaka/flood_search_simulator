"""Tests for deterministic search-history navigation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from algorithms.breadth_first import BreadthFirstSearch
from services.simulation_service import (
    first_step,
    get_step,
    last_step,
    next_step,
    previous_step,
    simulation_complete,
    total_steps,
)
from tests.support import make_start_goal_config, make_unweighted_choice_graph
from utils.exceptions import SimulationNavigationError


@pytest.fixture
def search_result():
    """Return a real result with several recorded search steps."""
    graph = make_unweighted_choice_graph()
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    return BreadthFirstSearch().search(graph, configuration)


def test_total_steps_and_endpoints(search_result) -> None:
    assert total_steps(search_result) == len(search_result.steps)
    assert first_step(search_result) is search_result.steps[0]
    assert last_step(search_result) is search_result.steps[-1]


def test_next_and_previous_steps_return_original_instances(search_result) -> None:
    assert next_step(search_result, 0) is search_result.steps[1]
    assert previous_step(search_result, 1) is search_result.steps[0]
    assert get_step(search_result, 1) is search_result.steps[1]


def test_navigation_clamps_lower_and_upper_bounds(search_result) -> None:
    assert get_step(search_result, -100) is search_result.steps[0]
    assert previous_step(search_result, 0) is search_result.steps[0]
    assert get_step(search_result, 100) is search_result.steps[-1]
    assert next_step(search_result, len(search_result.steps) - 1) is search_result.steps[-1]


def test_simulation_complete(search_result) -> None:
    final_index = len(search_result.steps) - 1

    assert simulation_complete(search_result, -10) is False
    assert simulation_complete(search_result, 0) is False
    assert simulation_complete(search_result, final_index) is True
    assert simulation_complete(search_result, final_index + 10) is True


def test_empty_history_reports_zero_and_rejects_navigation(search_result) -> None:
    empty_result = replace(search_result, steps=())

    assert total_steps(empty_result) == 0
    assert simulation_complete(empty_result, 0) is True
    with pytest.raises(SimulationNavigationError, match="empty step history"):
        first_step(empty_result)
    with pytest.raises(SimulationNavigationError, match="empty step history"):
        last_step(empty_result)
    with pytest.raises(SimulationNavigationError, match="empty step history"):
        get_step(empty_result, 0)


@pytest.mark.parametrize("invalid_index", [1.5, "1", None, True])
def test_invalid_indexes_raise_domain_error(search_result, invalid_index) -> None:
    with pytest.raises(SimulationNavigationError, match="must be an integer"):
        get_step(search_result, invalid_index)
    with pytest.raises(SimulationNavigationError, match="must be an integer"):
        next_step(search_result, invalid_index)
    with pytest.raises(SimulationNavigationError, match="must be an integer"):
        previous_step(search_result, invalid_index)
    with pytest.raises(SimulationNavigationError, match="must be an integer"):
        simulation_complete(search_result, invalid_index)


def test_invalid_result_raises_domain_error() -> None:
    with pytest.raises(SimulationNavigationError, match="requires a SearchResult"):
        total_steps(None)
