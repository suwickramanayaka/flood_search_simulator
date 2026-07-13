"""Tests for static and step-aware Plotly graph preparation."""

from __future__ import annotations

import ast
import copy
from dataclasses import replace
from pathlib import Path

from algorithms.breadth_first import BreadthFirstSearch
from models.search_models import SearchStep
from tests.support import make_start_goal_config, make_unweighted_choice_graph
from visualizations.graph_renderer import (
    build_graph_figure,
    build_search_step_figure,
    classify_edge_states,
    classify_node_states,
    get_geographic_positions,
)


def _search_fixture():
    graph = make_unweighted_choice_graph()
    graph.nodes["B"]["available"] = False
    graph["A"]["B"]["flood_risk"] = 4
    graph["C"]["D"]["blocked"] = True
    configuration = make_start_goal_config("Breadth-First Search", "A", "G")
    result = BreadthFirstSearch().search(graph, configuration)
    return graph, configuration, result


def _edge_state(states, source: str, target: str) -> str:
    return next(
        state
        for edge, state in states.items()
        if set(edge) == {source, target}
    )


def test_initialization_classifies_start_frontier_goal_unavailable_and_unvisited() -> None:
    graph, _, result = _search_fixture()
    step = result.steps[0]
    states = classify_node_states(graph, step, result)

    assert states["A"] == "start"
    assert states["G"] == "goal"
    assert states["B"] == "unavailable"
    assert states["C"] == "unvisited"


def test_current_node_precedes_path_frontier_and_explored() -> None:
    graph, _, result = _search_fixture()
    step = SearchStep(
        step_number=2,
        event_type="expand",
        current_node="C",
        frontier_nodes=("C", "D"),
        explored_nodes=("A", "C"),
        current_path=("A", "C"),
    )
    states = classify_node_states(graph, step, result)

    assert states["C"] == "current"
    assert states["A"] == "start"
    assert states["D"] == "frontier"


def test_current_path_frontier_and_explored_classification() -> None:
    graph, _, result = _search_fixture()
    step = SearchStep(
        step_number=3,
        event_type="expand",
        current_node="D",
        frontier_nodes=(),
        explored_nodes=("B",),
        current_path=("A", "C", "D"),
    )
    states = classify_node_states(graph, step, result)

    assert states["D"] == "current"
    assert states["C"] == "current_path"
    assert states["B"] == "explored"


def test_goal_completion_adds_final_path_without_hiding_start_or_goal() -> None:
    graph, _, result = _search_fixture()
    goal_step = result.steps[-1]
    node_states = classify_node_states(graph, goal_step, result)
    edge_states = classify_edge_states(graph, goal_step, result)

    assert node_states[result.start_node] == "start"
    assert node_states[result.goal_node] == "current"
    assert any(state == "final_path" for state in node_states.values())
    assert _edge_state(edge_states, "A", "B") == "final_route"
    assert _edge_state(edge_states, "B", "G") == "final_route"


def test_failure_step_never_reveals_final_route() -> None:
    graph, _, result = _search_fixture()
    failure_step = replace(result.steps[-1], event_type="failure", goal_found=False)

    assert "final_path" not in classify_node_states(graph, failure_step, result).values()
    assert "final_route" not in classify_edge_states(graph, failure_step, result).values()


def test_edge_classification_and_precedence() -> None:
    graph, _, result = _search_fixture()
    step = SearchStep(
        step_number=2,
        event_type="expand",
        current_node="B",
        frontier_nodes=(),
        explored_nodes=("A",),
        current_path=("A", "B"),
    )
    states = classify_edge_states(graph, step, result)

    assert _edge_state(states, "A", "B") == "current_path"
    assert _edge_state(states, "C", "D") == "blocked"
    assert _edge_state(states, "B", "G") == "normal"

    graph["A"]["B"]["blocked"] = True
    blocked_states = classify_edge_states(graph, step, result)
    assert _edge_state(blocked_states, "A", "B") == "blocked"


def test_high_risk_edge_remains_distinct_when_not_on_current_path() -> None:
    graph, _, result = _search_fixture()
    step = replace(result.steps[0], current_path=("A",))
    states = classify_edge_states(graph, step, result)

    assert _edge_state(states, "A", "B") == "high_risk"


def test_rendering_does_not_mutate_inputs_and_positions_are_stable() -> None:
    graph, configuration, result = _search_fixture()
    step = result.steps[1]
    graph_snapshot = copy.deepcopy(graph)
    step_snapshot = copy.deepcopy(step)
    result_snapshot = copy.deepcopy(result)
    positions_before = get_geographic_positions(graph)

    build_search_step_figure(graph, step, result, configuration)

    assert list(graph.nodes(data=True)) == list(graph_snapshot.nodes(data=True))
    assert list(graph.edges(data=True)) == list(graph_snapshot.edges(data=True))
    assert step == step_snapshot
    assert result == result_snapshot
    assert get_geographic_positions(graph) == positions_before
    assert positions_before["A"] == (
        graph.nodes["A"]["longitude"],
        graph.nodes["A"]["latitude"],
    )


def test_graph_layout_centers_enlarged_graph_legend_and_dense_node_labels() -> None:
    graph, configuration, result = _search_fixture()
    figure = build_search_step_figure(graph, result.steps[0], result, configuration)
    node_traces = [trace for trace in figure.data if trace.mode == "markers+text"]
    label_positions = {
        position
        for trace in node_traces
        for position in trace.textposition
    }

    assert figure.layout.height == 680
    assert figure.layout.title.text is None
    assert figure.layout.legend.y == -0.06
    assert figure.layout.legend.yanchor == "top"
    assert figure.layout.legend.x == 0.5
    assert figure.layout.legend.xanchor == "center"
    assert figure.layout.legend.entrywidth == 145
    assert max(trace.marker.size for trace in node_traces) >= 22
    assert max(trace.textfont.size for trace in node_traces) == 12
    assert len(label_positions) > 1


def test_existing_final_state_renderer_remains_compatible() -> None:
    graph, _, result = _search_fixture()
    figure = build_graph_figure(
        graph,
        start_node=result.start_node,
        goal_node=result.goal_node,
        final_path=result.final_path,
    )
    trace_names = {trace.name for trace in figure.data}

    assert "Final route" in trace_names
    assert "Start" in trace_names
    assert "Goal" in trace_names


def test_page_uses_step_renderer_without_rerunning_or_direct_history_access() -> None:
    page_path = Path(__file__).resolve().parents[1] / "pages" / "1_Interactive_Simulation.py"
    source = page_path.read_text(encoding="utf-8")
    syntax_tree = ast.parse(source)
    run_search_calls = [
        node
        for node in ast.walk(syntax_tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run_search"
    ]

    assert "build_search_step_figure" in source
    assert "result.steps" not in source
    assert len(run_search_calls) == 1
    for label in ("Previous", "Next", "Reset", "Run to Completion"):
        assert f'"{label}"' in source
