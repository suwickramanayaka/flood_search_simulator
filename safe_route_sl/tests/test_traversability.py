"""Traversability tests for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

from services.graph_service import create_traversable_graph, get_traversable_neighbors, load_graph
from services.validation_service import has_available_route


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


def test_blocked_edge_is_excluded_from_neighbors_and_traversable_graph() -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")
    graph["A"]["B"]["blocked"] = True

    assert "B" not in get_traversable_neighbors(graph, "A")

    traversable = create_traversable_graph(graph)
    assert traversable.has_edge("A", "B") is False
    assert graph.has_edge("A", "B") is True


def test_route_availability_detects_paths_and_disconnection() -> None:
    graph = load_graph(DATA_DIR / "locations.csv", DATA_DIR / "roads.csv")

    assert has_available_route(graph, "A", "H") is True
    assert has_available_route(graph, "A", "Z") is False

    graph["A"]["B"]["blocked"] = True
    graph["A"]["C"]["blocked"] = True
    graph["A"]["D"]["blocked"] = True
    assert has_available_route(graph, "A", "H") is False