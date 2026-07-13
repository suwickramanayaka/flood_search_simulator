"""Graph loading and validation tests for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import pytest

from services.graph_service import (
    build_graph,
    get_available_goal_nodes,
    get_edge_data,
    get_traversable_neighbors,
    load_graph,
    load_locations,
    load_roads,
)
from services.validation_service import (
    has_available_route,
    validate_goal_available,
    validate_graph,
    validate_start_goal,
)
from utils.exceptions import DataValidationError, GraphValidationError


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def test_load_locations_and_roads() -> None:
    locations = load_locations(DATA_DIR / "locations.csv")
    roads = load_roads(DATA_DIR / "roads.csv")

    assert len(locations) == 14
    assert len(roads) == 22
    assert locations["A"].available is True
    assert locations["G"].location_type == "hospital"
    assert roads[0].blocked is False


def test_build_graph_preserves_attributes() -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")

    assert graph.number_of_nodes() == 14
    assert graph.number_of_edges() == 22
    assert graph.nodes["A"]["name"] == "Millaniya Village"
    assert graph.nodes["A"]["available"] is True
    assert graph["A"]["B"]["road_name"] == "Village Bridge Road"
    assert graph["A"]["B"]["blocked"] is False


def test_available_goals_and_validation_helpers() -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")

    assert get_available_goal_nodes(graph) == ["D", "F", "G", "H", "N"]
    validate_graph(graph)
    validate_start_goal(graph, "A", "H")
    validate_goal_available(graph, "H")
    assert has_available_route(graph, "A", "H") is True


def test_traversable_neighbors_exclude_blocked_edges() -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")
    graph["A"]["B"]["blocked"] = True

    assert "B" not in get_traversable_neighbors(graph, "A")
    assert "C" in get_traversable_neighbors(graph, "A")


def test_validate_graph_rejects_empty_graph() -> None:
    with pytest.raises(GraphValidationError):
        validate_graph(nx.Graph())


def test_load_locations_rejects_duplicate_ids(tmp_path: Path) -> None:
    source = (DATA_DIR / "locations.csv").read_text(encoding="utf-8")
    duplicate = source + "A,Duplicate,Duplicate,village,6.0,80.0,0,true,Duplicate row\n"
    path = tmp_path / "locations.csv"
    path.write_text(duplicate, encoding="utf-8")

    with pytest.raises(DataValidationError):
        load_locations(path)


def test_load_roads_rejects_unknown_nodes(tmp_path: Path) -> None:
    source = (DATA_DIR / "roads.csv").read_text(encoding="utf-8")
    path = tmp_path / "roads.csv"
    path.write_text(source + "X,Y,Bad Road,1.0,1,1,good,false\n", encoding="utf-8")

    locations = load_locations(DATA_DIR / "locations.csv")
    with pytest.raises(DataValidationError):
        build_graph(locations, load_roads(path))


def test_load_roads_rejects_invalid_data(tmp_path: Path) -> None:
    invalid_risk = tmp_path / "invalid_risk.csv"
    invalid_risk.write_text(
        "source,target,road_name,distance_km,travel_time_min,flood_risk,road_condition,blocked\n"
        "A,B,Bad Road,1.0,2,6,good,false\n",
        encoding="utf-8",
    )
    with pytest.raises(DataValidationError):
        load_roads(invalid_risk)

    invalid_distance = tmp_path / "invalid_distance.csv"
    invalid_distance.write_text(
        "source,target,road_name,distance_km,travel_time_min,flood_risk,road_condition,blocked\n"
        "A,B,Bad Road,-1.0,2,3,good,false\n",
        encoding="utf-8",
    )
    with pytest.raises(DataValidationError):
        load_roads(invalid_distance)

    invalid_self_loop = tmp_path / "invalid_self_loop.csv"
    invalid_self_loop.write_text(
        "source,target,road_name,distance_km,travel_time_min,flood_risk,road_condition,blocked\n"
        "A,A,Loop Road,1.0,2,3,good,false\n",
        encoding="utf-8",
    )
    with pytest.raises(DataValidationError):
        load_roads(invalid_self_loop)

    invalid_coords = tmp_path / "invalid_coords.csv"
    invalid_coords.write_text(
        "id,name,short_name,type,latitude,longitude,capacity,available,description\n"
        "A,Node,A,village,100,80,0,true,Invalid\n",
        encoding="utf-8",
    )
    with pytest.raises(DataValidationError):
        load_locations(invalid_coords)

