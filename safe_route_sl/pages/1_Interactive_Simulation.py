"""Interactive simulation page for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from models.configuration import SearchConfiguration
from services.graph_service import get_available_goal_nodes, load_graph
from services.scenario_service import apply_scenario_by_id, load_scenarios
from services.search_service import run_search
from utils.constants import (
	BALANCED_MODE,
	DISTANCE_MODE,
	GOAL_LOCATION_TYPES,
	HEURISTIC_LABELS,
	HEURISTIC_LABEL_TO_TYPE,
	OPTIMIZATION_MODE_LABELS,
	OPTIMIZATION_LABEL_TO_MODE,
	SEARCH_ALGORITHM_LABELS,
)
from utils.exceptions import SafeRouteError
from utils.formatting import format_node_name, format_optimization_mode_label, format_path, humanize_identifier
from visualizations.graph_renderer import build_graph_figure
from visualizations.metrics_renderer import render_search_metrics
from visualizations.state_renderer import render_final_search_state


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOCATIONS_PATH = DATA_DIR / "locations.csv"
ROADS_PATH = DATA_DIR / "roads.csv"
SCENARIOS_PATH = DATA_DIR / "scenarios.json"

SESSION_DEFAULTS = {
	"latest_result": None,
	"latest_configuration": None,
	"latest_scenario_id": None,
	"search_error": None,
	"latest_configuration_signature": None,
}


@st.cache_resource
def load_base_graph() -> object:
	return load_graph(LOCATIONS_PATH, ROADS_PATH)


@st.cache_data
def load_all_scenarios() -> dict[str, object]:
	return load_scenarios(SCENARIOS_PATH)


def initialize_session_state() -> None:
	for key, value in SESSION_DEFAULTS.items():
		st.session_state.setdefault(key, value)


def reset_result_state() -> None:
	st.session_state.latest_result = None
	st.session_state.latest_configuration = None
	st.session_state.latest_scenario_id = None
	st.session_state.latest_configuration_signature = None
	st.session_state.search_error = None


def configuration_signature(configuration: SearchConfiguration) -> tuple[object, ...]:
	return (
		configuration.algorithm,
		configuration.start_node,
		configuration.goal_node,
		configuration.optimization_mode,
		configuration.risk_weight,
		configuration.heuristic_type,
		configuration.scenario_id,
	)


def _sorted_start_nodes(graph) -> list[str]:
	start_nodes = [
		node_id
		for node_id, node_data in graph.nodes(data=True)
		if node_data.get("available", False) and node_data.get("location_type") not in GOAL_LOCATION_TYPES
	]
	return sorted(start_nodes, key=lambda node_id: format_node_name(graph, node_id).lower())


def _coerce_widget_value(key: str, options: list[object], default_value: object) -> object:
	current_value = st.session_state.get(key)
	if current_value not in options:
		st.session_state[key] = default_value
	return st.session_state[key]


def _cost_formula_summary(optimization_mode: str) -> str:
	if optimization_mode == DISTANCE_MODE:
		return "cost = distance_km"
	if optimization_mode == "time":
		return "cost = travel_time_min"
	if optimization_mode == "safety":
		return "cost = distance_km + risk_weight × flood_risk + road_condition_penalty"
	return "cost = distance_km + 0.5 × travel_time_min + risk_weight × flood_risk + road_condition_penalty"


initialize_session_state()

base_graph = load_base_graph()
scenarios = load_all_scenarios()
scenario_ids = list(scenarios.keys())
default_scenario_id = scenario_ids[0]

_coerce_widget_value("scenario_id", scenario_ids, default_scenario_id)
scenario_id = st.selectbox(
	"Flood scenario",
	options=scenario_ids,
	format_func=lambda value: scenarios[value].name,
	key="scenario_id",
)

scenario = scenarios[scenario_id]
scenario_graph = apply_scenario_by_id(base_graph, scenarios, scenario_id)
start_nodes = _sorted_start_nodes(scenario_graph)
goal_nodes = get_available_goal_nodes(scenario_graph)

if not start_nodes:
	st.error("No suitable start locations are available for the selected scenario.")
	st.stop()
if not goal_nodes:
	st.error("No available evacuation goals exist for the selected scenario.")
	st.stop()

_coerce_widget_value("start_node", start_nodes, start_nodes[0])
_coerce_widget_value("goal_node", goal_nodes, goal_nodes[0])
_coerce_widget_value("algorithm", list(SEARCH_ALGORITHM_LABELS), SEARCH_ALGORITHM_LABELS[0])
_coerce_widget_value("optimization_mode", list(OPTIMIZATION_MODE_LABELS.keys()), BALANCED_MODE)
_coerce_widget_value("risk_weight", [st.session_state.get("risk_weight", 4.0)], 4.0)

controls_col, graph_col, results_col = st.columns([1.1, 2.2, 1.2])

with controls_col:
	st.subheader("Controls")
	st.caption(scenario.description)

	algorithm = st.selectbox(
		"Search algorithm",
		options=list(SEARCH_ALGORITHM_LABELS),
		key="algorithm",
	)

	start_node = st.selectbox(
		"Start node",
		options=start_nodes,
		format_func=lambda value: format_node_name(scenario_graph, value),
		key="start_node",
	)

	goal_node = st.selectbox(
		"Goal node",
		options=goal_nodes,
		format_func=lambda value: format_node_name(scenario_graph, value),
		key="goal_node",
	)

	optimization_mode = st.selectbox(
		"Optimization mode",
		options=list(OPTIMIZATION_MODE_LABELS.keys()),
		format_func=lambda value: OPTIMIZATION_MODE_LABELS[value],
		key="optimization_mode",
	)

	risk_weight = st.slider(
		"Flood-risk importance",
		min_value=0.0,
		max_value=10.0,
		value=float(st.session_state.get("risk_weight", 4.0)),
		step=0.5,
		help="This value mainly affects the safety and balanced cost modes.",
		key="risk_weight",
	)

	if algorithm in {"Greedy Best-First Search", "A* Search"}:
		heuristic_type = st.selectbox(
			"Heuristic type",
			options=list(HEURISTIC_LABELS.keys()),
			format_func=lambda value: HEURISTIC_LABELS[value],
			key="heuristic_type",
		)
	else:
		st.session_state.heuristic_type = "zero"
		heuristic_type = "zero"
		st.caption("Heuristic settings are ignored for this algorithm.")

	run_clicked = st.button("Run Search", type="primary", use_container_width=True)

	if st.button("Reset", use_container_width=True):
		st.session_state.scenario_id = default_scenario_id
		st.session_state.algorithm = SEARCH_ALGORITHM_LABELS[0]
		st.session_state.start_node = start_nodes[0]
		st.session_state.goal_node = goal_nodes[0]
		st.session_state.optimization_mode = BALANCED_MODE
		st.session_state.heuristic_type = "zero"
		st.session_state.risk_weight = 4.0
		reset_result_state()
		st.rerun()

configuration = SearchConfiguration(
	algorithm=algorithm,
	start_node=start_node,
	goal_node=goal_node,
	optimization_mode=optimization_mode,
	risk_weight=float(risk_weight),
	heuristic_type=heuristic_type if algorithm in {"Greedy Best-First Search", "A* Search"} else "zero",
	scenario_id=scenario_id,
)
current_signature = configuration_signature(configuration)

if st.session_state.latest_result is not None and st.session_state.latest_configuration_signature != current_signature:
	reset_result_state()
	st.info("Previous result cleared because the configuration changed.")

if run_clicked:
	try:
		result = run_search(scenario_graph, configuration)
		st.session_state.latest_result = result
		st.session_state.latest_configuration = configuration
		st.session_state.latest_scenario_id = scenario_id
		st.session_state.latest_configuration_signature = current_signature
		st.session_state.search_error = None
	except SafeRouteError as error:
		reset_result_state()
		st.session_state.search_error = str(error)

with graph_col:
	st.subheader("Scenario View")
	st.write(f"Scenario: {scenario.name}")
	st.write(f"Optimization mode: {format_optimization_mode_label(optimization_mode)}")
	st.caption(_cost_formula_summary(optimization_mode))

	if st.session_state.latest_result is None:
		st.info("Configure the scenario and search settings, then select Run Search.")
	else:
		result = st.session_state.latest_result
		graph_figure = build_graph_figure(
			scenario_graph,
			start_node=result.start_node,
			goal_node=result.goal_node,
			final_path=result.final_path,
			optimization_mode=configuration.optimization_mode,
			risk_weight=configuration.risk_weight,
		)
		st.plotly_chart(graph_figure, use_container_width=True)

with results_col:
	st.subheader("Results")
	if st.session_state.search_error:
		st.error(st.session_state.search_error)
	elif st.session_state.latest_result is None:
		st.info("No search has been run yet.")
	else:
		result = st.session_state.latest_result
		if result.found:
			st.success("A route was found.")
		else:
			st.warning("No traversable route was found.")
		render_final_search_state(result, scenario_graph)
		render_search_metrics(result, optimization_mode)

