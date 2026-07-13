"""Algorithm comparison page for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from services.comparison_service import compare_algorithms
from services.graph_service import get_available_goal_nodes, load_graph
from services.scenario_service import apply_scenario_by_id, load_scenarios
from utils.constants import BALANCED_MODE, GOAL_LOCATION_TYPES, HEURISTIC_LABELS, OPTIMIZATION_MODE_LABELS, SEARCH_ALGORITHM_LABELS
from utils.formatting import format_node_name
from visualizations.comparison_renderer import build_comparison_dataframe


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

if run_clicked:
	from models.configuration import SearchConfiguration

	configuration = SearchConfiguration(
		algorithm=SEARCH_ALGORITHM_LABELS[0],
		start_node=start_node,
		goal_node=goal_node,
		optimization_mode=optimization_mode,
		risk_weight=float(risk_weight),
		heuristic_type=heuristic_type,
	)
	records = compare_algorithms(scenario_graph, configuration)
	dataframe = build_comparison_dataframe(records)
	st.dataframe(dataframe, use_container_width=True, hide_index=True)
else:
	st.info("Select a scenario and settings, then run the comparison.")
