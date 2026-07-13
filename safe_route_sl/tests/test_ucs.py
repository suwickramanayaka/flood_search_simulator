"""Uniform-cost search tests for SafeRouteSL."""

from __future__ import annotations

import networkx as nx
import pytest

from algorithms.base import calculate_path_cost
from algorithms.uniform_cost import UniformCostSearch
from services.graph_service import create_traversable_graph
from tests.support import make_replacement_graph, make_start_goal_config, make_weighted_choice_graph
from utils.constants import BALANCED_MODE, DISTANCE_MODE
from utils.cost_functions import create_networkx_weight_function


def test_ucs_finds_minimum_cost_route() -> None:
    graph = make_weighted_choice_graph()
    config = make_start_goal_config("Uniform-Cost Search", "A", "G", optimization_mode=DISTANCE_MODE)
    result = UniformCostSearch().search(graph, config)

    assert result.found is True
    assert result.final_path == ("A", "C", "D", "G")
    assert result.total_cost == pytest.approx(6.0)
    assert result.path_length_edges == 3
    assert all(step.nodes_generated >= 1 for step in result.steps)
    assert tuple(step.nodes_generated for step in result.steps) == tuple(
        sorted(step.nodes_generated for step in result.steps)
    )


def test_ucs_replaces_higher_cost_path_and_skips_stale_entries() -> None:
    graph = make_replacement_graph()
    config = make_start_goal_config("Uniform-Cost Search", "A", "G", optimization_mode=DISTANCE_MODE)
    result = UniformCostSearch().search(graph, config)

    assert result.final_path == ("A", "C", "B", "G")
    assert result.total_cost == pytest.approx(5.0)
    assert result.repeated_state_skips >= 1


def test_ucs_equal_cost_ties_are_deterministic_and_matches_networkx() -> None:
    graph = nx.Graph()
    for node_id, coords in (("A", (0.0, 0.0)), ("B", (0.0, 1.0)), ("C", (1.0, 0.0)), ("G", (1.0, 1.0))):
        graph.add_node(
            node_id,
            name=node_id,
            short_name=node_id,
            location_type="junction",
            latitude=coords[0],
            longitude=coords[1],
            capacity=0,
            available=True,
            description=node_id,
        )
    graph.add_edge("A", "B", road_name="AB", distance_km=2.0, travel_time_min=2.0, flood_risk=1, road_condition="good", blocked=False)
    graph.add_edge("B", "G", road_name="BG", distance_km=2.0, travel_time_min=2.0, flood_risk=1, road_condition="good", blocked=False)
    graph.add_edge("A", "C", road_name="AC", distance_km=2.0, travel_time_min=2.0, flood_risk=1, road_condition="good", blocked=False)
    graph.add_edge("C", "G", road_name="CG", distance_km=2.0, travel_time_min=2.0, flood_risk=1, road_condition="good", blocked=False)

    result = UniformCostSearch().search(graph, make_start_goal_config("Uniform-Cost Search", "A", "G", optimization_mode=DISTANCE_MODE))
    assert result.final_path == ("A", "B", "G")

    weight = create_networkx_weight_function(DISTANCE_MODE, 4.0)
    expected_cost = nx.shortest_path_length(graph, "A", "G", weight=weight)
    assert result.total_cost == pytest.approx(expected_cost)


def test_ucs_handles_no_route_and_start_equals_goal() -> None:
    graph = make_weighted_choice_graph()
    graph["A"]["B"]["blocked"] = True
    graph["B"]["G"]["blocked"] = True
    graph["A"]["C"]["blocked"] = True
    graph["C"]["D"]["blocked"] = True
    graph["D"]["G"]["blocked"] = True

    no_route = UniformCostSearch().search(graph, make_start_goal_config("Uniform-Cost Search", "A", "G", optimization_mode=DISTANCE_MODE))
    assert no_route.found is False
    assert no_route.final_path == ()

    same = UniformCostSearch().search(graph, make_start_goal_config("Uniform-Cost Search", "A", "A", optimization_mode=DISTANCE_MODE))
    assert same.found is True
    assert same.final_path == ("A",)
"""Phase 1 placeholder for UCS tests."""
