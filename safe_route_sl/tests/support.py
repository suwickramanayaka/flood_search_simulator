"""Shared test helpers for SafeRouteSL phase 3."""

from __future__ import annotations

from pathlib import Path

import networkx as nx

from models.configuration import SearchConfiguration
from services.graph_service import load_graph
from services.scenario_service import apply_scenario_by_id, load_scenarios
from utils.constants import BALANCED_MODE, DISTANCE_MODE, SAFETY_MODE, TIME_MODE


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def add_node(graph: nx.Graph, node_id: str, latitude: float, longitude: float) -> None:
    graph.add_node(
        node_id,
        name=node_id,
        short_name=node_id,
        location_type="junction",
        latitude=latitude,
        longitude=longitude,
        capacity=0,
        available=True,
        description=f"Node {node_id}",
    )


def add_edge(
    graph: nx.Graph,
    source: str,
    target: str,
    *,
    distance_km: float,
    travel_time_min: float | None = None,
    flood_risk: int = 1,
    road_condition: str = "good",
    blocked: bool = False,
) -> None:
    graph.add_edge(
        source,
        target,
        road_name=f"{source}-{target}",
        distance_km=distance_km,
        travel_time_min=travel_time_min if travel_time_min is not None else distance_km,
        flood_risk=flood_risk,
        road_condition=road_condition,
        blocked=blocked,
    )


def make_unweighted_choice_graph() -> nx.Graph:
    graph = nx.Graph()
    for node_id, lat, lon in (("A", 0.0, 0.0), ("B", 0.0, 1.0), ("C", 1.0, 0.0), ("D", 1.0, 1.0), ("G", 2.0, 0.0)):
        add_node(graph, node_id, lat, lon)
    graph.nodes["G"].update(name="Goal Shelter", short_name="Goal", location_type="shelter", capacity=100, available=True)
    add_edge(graph, "A", "B", distance_km=1.0)
    add_edge(graph, "B", "G", distance_km=1.0)
    add_edge(graph, "A", "C", distance_km=1.0)
    add_edge(graph, "C", "D", distance_km=1.0)
    add_edge(graph, "D", "G", distance_km=1.0)
    return graph


def make_weighted_choice_graph() -> nx.Graph:
    graph = nx.Graph()
    for node_id, lat, lon in (("A", 0.0, 0.0), ("B", 0.0, 1.0), ("C", 1.0, 0.0), ("D", 1.0, 1.0), ("G", 2.0, 0.0)):
        add_node(graph, node_id, lat, lon)
    graph.nodes["G"].update(name="Goal Shelter", short_name="Goal", location_type="shelter", capacity=100, available=True)
    add_edge(graph, "A", "B", distance_km=10.0, travel_time_min=10.0, flood_risk=1, road_condition="good")
    add_edge(graph, "B", "G", distance_km=10.0, travel_time_min=10.0, flood_risk=1, road_condition="good")
    add_edge(graph, "A", "C", distance_km=2.0, travel_time_min=2.0, flood_risk=1, road_condition="good")
    add_edge(graph, "C", "D", distance_km=2.0, travel_time_min=2.0, flood_risk=1, road_condition="good")
    add_edge(graph, "D", "G", distance_km=2.0, travel_time_min=2.0, flood_risk=1, road_condition="good")
    return graph


def make_greedy_trap_graph() -> nx.Graph:
    graph = nx.Graph()
    for node_id, lat, lon in (("A", 0.0, 0.0), ("B", 0.0, 3.0), ("C", 3.0, 0.0), ("D", 4.0, 0.0), ("G", 0.0, 4.0)):
        add_node(graph, node_id, lat, lon)
    graph.nodes["G"].update(name="Goal Shelter", short_name="Goal", location_type="shelter", capacity=100, available=True)
    add_edge(graph, "A", "B", distance_km=1.0, travel_time_min=1.0)
    add_edge(graph, "B", "G", distance_km=50.0, travel_time_min=50.0)
    add_edge(graph, "A", "C", distance_km=2.0, travel_time_min=2.0)
    add_edge(graph, "C", "D", distance_km=2.0, travel_time_min=2.0)
    add_edge(graph, "D", "G", distance_km=2.0, travel_time_min=2.0)
    return graph


def make_replacement_graph() -> nx.Graph:
    graph = nx.Graph()
    for node_id, lat, lon in (("A", 0.0, 0.0), ("B", 0.0, 1.0), ("C", 1.0, 0.0), ("G", 2.0, 0.0)):
        add_node(graph, node_id, lat, lon)
    graph.nodes["G"].update(name="Goal Shelter", short_name="Goal", location_type="shelter", capacity=100, available=True)
    add_edge(graph, "A", "B", distance_km=8.0, travel_time_min=8.0)
    add_edge(graph, "A", "C", distance_km=2.0, travel_time_min=2.0)
    add_edge(graph, "C", "B", distance_km=1.0, travel_time_min=1.0)
    add_edge(graph, "B", "G", distance_km=2.0, travel_time_min=2.0)
    return graph


def make_start_goal_config(
    algorithm: str,
    start_node: str,
    goal_node: str,
    *,
    optimization_mode: str = BALANCED_MODE,
    heuristic_type: str = "haversine",
    risk_weight: float = 4.0,
    tie_breaking: str = "alphabetical",
) -> SearchConfiguration:
    return SearchConfiguration(
        algorithm=algorithm,
        start_node=start_node,
        goal_node=goal_node,
        optimization_mode=optimization_mode,
        risk_weight=risk_weight,
        heuristic_type=heuristic_type,
        tie_breaking=tie_breaking,
    )


def load_project_dataset_graph() -> nx.Graph:
    return load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")


def load_project_dataset_scenario_graph(scenario_id: str) -> nx.Graph:
    graph = load_project_dataset_graph()
    scenarios = load_scenarios(DATA_DIR / "scenarios.json")
    return apply_scenario_by_id(graph, scenarios, scenario_id)
