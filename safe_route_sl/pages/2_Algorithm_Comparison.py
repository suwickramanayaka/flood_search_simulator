"""Algorithm comparison page for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from models.configuration import SearchConfiguration
from services.comparison_service import compare_algorithms
from services.comparison_state_service import (
	build_comparison_signature,
	clear_stale_comparison_state,
	initialize_comparison_state,
	store_comparison_error,
	store_comparison_results,
)
from services.graph_service import get_available_goal_nodes, load_graph
from services.scenario_service import apply_scenario_by_id, load_scenarios
from utils.constants import BALANCED_MODE, GOAL_LOCATION_TYPES, HEURISTIC_LABELS, OPTIMIZATION_MODE_LABELS, SEARCH_ALGORITHM_LABELS
from utils.exceptions import SafeRouteError
from utils.formatting import format_node_name
from visualizations.comparison_renderer import (
	build_comparison_dataframe,
	build_frontier_chart,
	build_nodes_expanded_chart,
	build_path_edge_chart,
	build_runtime_chart,
	build_total_cost_chart,
	excluded_cost_algorithm_names,
	failed_algorithm_names,
	format_summary_insight,
	prepare_summary_insights,
)


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
LOCATIONS_PATH = DATA_DIR / "locations.csv"
ROADS_PATH = DATA_DIR / "roads.csv"
SCENARIOS_PATH = DATA_DIR / "scenarios.json"


@st.cache_resource
def load_base_graph() -> object:
	return load_graph(LOCATIONS_PATH, ROADS_PATH)


@st.cache_data
def load_all_scenarios() -> dict[str, object]:
	return load_scenarios(SCENARIOS_PATH)


def _sorted_start_nodes(graph) -> list[str]:
	start_nodes = [
		node_id
		for node_id, node_data in graph.nodes(data=True)
		if node_data.get("available", False) and node_data.get("location_type") not in GOAL_LOCATION_TYPES
	]
	return sorted(start_nodes, key=lambda node_id: format_node_name(graph, node_id).lower())


initialize_comparison_state(st.session_state)

base_graph = load_base_graph()
scenarios = load_all_scenarios()
scenario_ids = list(scenarios.keys())

st.title("Algorithm Comparison")
st.write("Compare the five core algorithms using the same scenario and configuration family.")

scenario_id = st.selectbox("Flood scenario", options=scenario_ids, format_func=lambda value: scenarios[value].name)
scenario_graph = apply_scenario_by_id(base_graph, scenarios, scenario_id)
start_nodes = _sorted_start_nodes(scenario_graph)
goal_nodes = get_available_goal_nodes(scenario_graph)

start_node = st.selectbox("Start node", options=start_nodes, format_func=lambda value: format_node_name(scenario_graph, value))
goal_node = st.selectbox("Goal node", options=goal_nodes, format_func=lambda value: format_node_name(scenario_graph, value))
optimization_mode = st.selectbox(
	"Optimization mode",
	options=list(OPTIMIZATION_MODE_LABELS.keys()),
	format_func=lambda value: OPTIMIZATION_MODE_LABELS[value],
	index=list(OPTIMIZATION_MODE_LABELS.keys()).index(BALANCED_MODE),
)
risk_weight = st.slider("Flood-risk importance", min_value=0.0, max_value=10.0, value=4.0, step=0.5)
heuristic_type = st.selectbox("Heuristic type", options=list(HEURISTIC_LABELS.keys()), format_func=lambda value: HEURISTIC_LABELS[value])

run_clicked = st.button("Run Comparison", type="primary")

current_signature = build_comparison_signature(
	scenario_id,
	start_node,
	goal_node,
	optimization_mode,
	float(risk_weight),
	heuristic_type,
)

if clear_stale_comparison_state(st.session_state, current_signature):
	st.info("Previous comparison cleared because the configuration changed.")

if run_clicked:
	try:
		configuration = SearchConfiguration(
			algorithm=SEARCH_ALGORITHM_LABELS[0],
			start_node=start_node,
			goal_node=goal_node,
			optimization_mode=optimization_mode,
			risk_weight=float(risk_weight),
			heuristic_type=heuristic_type,
			scenario_id=scenario_id,
		)
		records = compare_algorithms(scenario_graph, configuration)
		store_comparison_results(st.session_state, records, current_signature)
	except SafeRouteError as error:
		store_comparison_error(st.session_state, current_signature, str(error))

if st.session_state.comparison_error:
	st.error(st.session_state.comparison_error)
elif st.session_state.latest_comparison_records is None:
	st.info("Select a scenario and settings, then run the comparison.")
else:
	records = st.session_state.latest_comparison_records
	failed_names = failed_algorithm_names(records)

	st.subheader("Summary Insights")
	insights = prepare_summary_insights(records)
	if insights:
		for insight in insights:
			st.write(f"- {format_summary_insight(insight)}")
		st.caption(
			"Algorithms optimize and explore differently; these values describe only this configuration."
		)
	else:
		st.warning("No successful routes are available for summary insights.")

	if failed_names:
		st.warning(f"No route was produced by: {', '.join(failed_names)}.")

	table_tab, cost_tab, effort_tab, runtime_tab = st.tabs(
		["Results Table", "Cost and Path", "Search Effort", "Approximate Runtime"]
	)

	with table_tab:
		dataframe = build_comparison_dataframe(records, scenario_graph)
		st.dataframe(dataframe, width="stretch", hide_index=True)

	with cost_tab:
		cost_chart = build_total_cost_chart(records)
		if cost_chart is None:
			st.warning("No finite successful route costs are available to chart.")
		else:
			st.plotly_chart(cost_chart, width="stretch")
		excluded_names = excluded_cost_algorithm_names(records)
		if excluded_names:
			st.caption(
				"Excluded from the route-cost chart because no finite route was produced: "
				+ ", ".join(excluded_names)
			)

		path_chart = build_path_edge_chart(records)
		if path_chart is None:
			st.warning("No successful path edge counts are available to chart.")
		else:
			st.plotly_chart(path_chart, width="stretch")

	with effort_tab:
		nodes_chart = build_nodes_expanded_chart(records)
		frontier_chart = build_frontier_chart(records)
		if nodes_chart is not None:
			st.plotly_chart(nodes_chart, width="stretch")
		if frontier_chart is not None:
			st.plotly_chart(frontier_chart, width="stretch")

	with runtime_tab:
		st.caption(
			"Execution times are approximate educational measurements, not scientific benchmarks."
		)
		runtime_chart = build_runtime_chart(records)
		if runtime_chart is None:
			st.warning("No finite approximate execution times are available to chart.")
		else:
			st.plotly_chart(runtime_chart, width="stretch")
