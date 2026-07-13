"""Toolkit validation diagnostics for SafeRouteSL custom searches."""

from __future__ import annotations

from pathlib import Path

import networkx as nx
import streamlit as st

from algorithms.simpleai_adapter import get_simpleai_status, is_simpleai_available
from models.configuration import SearchConfiguration
from services.graph_service import get_available_goal_nodes, load_graph
from services.scenario_service import apply_scenario_by_id, load_scenarios
from services.toolkit_validation_service import validate_against_toolkits
from utils.constants import (
	BALANCED_MODE,
	GOAL_LOCATION_TYPES,
	HEURISTIC_LABELS,
	OPTIMIZATION_MODE_LABELS,
)
from utils.exceptions import SafeRouteError
from utils.formatting import format_node_name
from visualizations.page_style import apply_page_styles, render_page_title, render_section_title
from visualizations.toolkit_validation_renderer import build_validation_dataframe


st.set_page_config(
	page_title="Toolkit Validation | SafeRouteSL",
	page_icon="🌊",
	layout="wide",
	initial_sidebar_state="expanded",
)
apply_page_styles()

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


render_page_title("Toolkit Validation")
st.write(
	"Compare the custom educational searches with NetworkX reference implementations. "
	"The simulator continues to use the custom algorithms for all step recording."
)
st.caption(
	"Different valid toolkits can return alternate equal paths. BFS is compared by edge count, while UCS and A* are compared by weighted cost."
)
st.caption(
	"Haversine A* validation is conditional outside distance mode; safety and balanced totals are educational composite scores, not physical units."
)
st.caption("Educational simulation using synthetic data. Not for real emergency decision-making.")

render_section_title("Toolkit Availability")
st.success(f"NetworkX available ({nx.__version__}) — active reference toolkit")
simpleai_status = get_simpleai_status()
if is_simpleai_available():
	st.success(simpleai_status)
else:
	st.info(f"{simpleai_status}. NetworkX remains the active reference toolkit.")

base_graph = load_base_graph()
scenarios = load_all_scenarios()
scenario_ids = list(scenarios.keys())

scenario_id = st.selectbox(
	"Flood scenario",
	options=scenario_ids,
	format_func=lambda value: scenarios[value].name,
)
scenario_graph = apply_scenario_by_id(base_graph, scenarios, scenario_id)
start_nodes = _sorted_start_nodes(scenario_graph)
goal_nodes = get_available_goal_nodes(scenario_graph)

if not start_nodes or not goal_nodes:
	st.error("This scenario does not provide a valid start and goal selection.")
	st.stop()

start_node = st.selectbox(
	"Start node",
	options=start_nodes,
	format_func=lambda value: format_node_name(scenario_graph, value),
)
goal_node = st.selectbox(
	"Goal node",
	options=goal_nodes,
	format_func=lambda value: format_node_name(scenario_graph, value),
)
optimization_mode = st.selectbox(
	"Optimization mode",
	options=list(OPTIMIZATION_MODE_LABELS.keys()),
	format_func=lambda value: OPTIMIZATION_MODE_LABELS[value],
	index=list(OPTIMIZATION_MODE_LABELS.keys()).index(BALANCED_MODE),
)
risk_weight = st.slider(
	"Flood-risk importance",
	min_value=0.0,
	max_value=10.0,
	value=4.0,
	step=0.5,
)
heuristic_type = st.selectbox(
	"Heuristic type",
	options=list(HEURISTIC_LABELS.keys()),
	format_func=lambda value: HEURISTIC_LABELS[value],
)

run_clicked = st.button("Run Toolkit Validation", type="primary")

if run_clicked:
	try:
		configuration = SearchConfiguration(
			algorithm="Breadth-First Search",
			start_node=start_node,
			goal_node=goal_node,
			optimization_mode=optimization_mode,
			risk_weight=float(risk_weight),
			heuristic_type=heuristic_type,
			scenario_id=scenario_id,
		)
		records = validate_against_toolkits(scenario_graph, configuration)
	except SafeRouteError as error:
		st.error(str(error))
	else:
		render_section_title("Validation Results")
		st.dataframe(
			build_validation_dataframe(records, scenario_graph),
			width="stretch",
			hide_index=True,
		)

		for record in records:
			message = (
				f"{record.algorithm_name}: {record.validation_status} — "
				f"{record.validation_message}"
			)
			if record.validation_status in {"Passed", "Passed with alternate equal path"}:
				st.success(message)
			elif record.validation_status == "Conditional":
				st.warning(message)
			elif record.validation_status == "Failed":
				st.error(message)
			else:
				st.info(message)
else:
	st.info("Choose a configuration, then run toolkit validation.")
