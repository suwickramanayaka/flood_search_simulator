"""Interactive simulation page for SafeRouteSL."""

from __future__ import annotations

from html import escape
from pathlib import Path
import time

import streamlit as st

from models.configuration import SearchConfiguration
from services.graph_service import get_available_goal_nodes, load_graph
from services.playback_service import (
	PLAYBACK_INTERVALS,
	PLAYBACK_LABELS_BY_INTERVAL,
	advance_playback,
	complete_playback,
	normalize_playback_interval,
	normalize_playback_state,
	pause_playback,
	reset_playback,
	start_playback,
)
from services.scenario_service import apply_scenario_by_id, load_scenarios
from services.session_state_service import (
	clear_search_state,
	clear_stale_search_state,
	get_simulation_progress,
	initialize_simulation_state,
	reset_simulation_state,
	reset_control_state,
	set_simulation_step,
)
from services.simulation_service import (
	get_step,
	next_step,
	previous_step,
	simulation_complete,
)
from services.search_service import run_search
from utils.constants import (
	BALANCED_MODE,
	DISTANCE_MODE,
	GOAL_LOCATION_TYPES,
	HEURISTIC_LABELS,
	OPTIMIZATION_MODE_LABELS,
	SEARCH_ALGORITHM_LABELS,
)
from utils.exceptions import SafeRouteError
from utils.formatting import format_node_name, format_optimization_mode_label, humanize_identifier
from visualizations.card_renderer import render_centered_card
from visualizations.graph_renderer import build_graph_figure, build_search_step_figure
from visualizations.state_renderer import render_search_step_state


st.set_page_config(
	page_title="Interactive Simulation | SafeRouteSL",
	page_icon="🌊",
	layout="wide",
	initial_sidebar_state="expanded",
)
st.markdown(
	"""
	<style>
	[data-testid="stMainBlockContainer"] {
		padding-top: 1rem;
	}
	.safe-route-page-title {
		margin: 0 0 1rem;
		font-size: clamp(2.4rem, 4vw, 3.25rem);
		font-weight: 800;
		letter-spacing: -0.035em;
		line-height: 1.08;
		text-align: center;
	}
	.safe-route-page-title::after {
		content: "";
		display: block;
		width: 4.5rem;
		height: 0.25rem;
		margin: 0.7rem auto 0;
		border-radius: 999px;
		background: linear-gradient(90deg, #2d8cff, #22c55e);
	}
	.safe-route-section-title {
		margin: 0.15rem 0 1.25rem !important;
		padding: 0.45rem 0.75rem 0.45rem 1rem !important;
		border-left: 0.25rem solid #2d8cff;
		border-radius: 0.25rem;
		background: linear-gradient(90deg, rgba(45, 140, 255, 0.14), transparent 75%);
		font-size: 1.4rem;
		font-weight: 700;
		letter-spacing: 0.01em;
		line-height: 1.2;
	}
	[data-testid="stSelectbox"]:has([aria-label="Playback Speed"])
	[data-baseweb="select"] > div {
		position: relative;
	}
	[data-testid="stSelectbox"]:has([aria-label="Playback Speed"])
	[data-baseweb="select"] > div > div:first-child {
		position: absolute;
		left: 2.5rem;
		right: 2.5rem;
		width: auto;
		text-align: center !important;
	}
	[data-testid="stSelectbox"]:has([aria-label="Playback Speed"])
	[data-baseweb="select"] > div > div:first-child > div {
		width: 100%;
		text-align: center !important;
	}
	</style>
	""",
	unsafe_allow_html=True,
)

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
	initialize_simulation_state(st.session_state)


def reset_result_state() -> None:
	clear_search_state(st.session_state)


def reset_controls() -> None:
	reset_control_state(st.session_state)


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


def render_section_title(title: str) -> None:
	"""Render a consistent secondary heading for a main page section."""
	st.markdown(
		f'<h2 class="safe-route-section-title">{escape(title)}</h2>',
		unsafe_allow_html=True,
	)


st.markdown(
	'<h1 class="safe-route-page-title">Interactive Simulation</h1>',
	unsafe_allow_html=True,
)

initialize_session_state()

base_graph = load_base_graph()
scenarios = load_all_scenarios()
scenario_ids = list(scenarios.keys())
default_scenario_id = scenario_ids[0]

controls_col, graph_col, results_col = st.columns([1.1, 2.2, 1.2])

_coerce_widget_value("scenario_id", scenario_ids, default_scenario_id)
with controls_col:
	render_section_title("Controls")
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

with controls_col:
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

	run_clicked = st.button("Run Search", type="primary", width="stretch")

	st.button(
		"Reset Controls",
		on_click=reset_controls,
		width="stretch",
	)

	with st.expander("About and educational disclaimer"):
		st.write(
			"Run a custom search once, then explore its recorded search states with manual or automatic playback."
		)
		st.caption("Educational simulation using synthetic data. Not for real emergency decision-making.")

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

if clear_stale_search_state(st.session_state, current_signature):
	st.info("Previous result cleared because the configuration changed.")

if run_clicked:
	try:
		result = run_search(scenario_graph, configuration)
		st.session_state.latest_result = result
		st.session_state.latest_configuration = configuration
		st.session_state.latest_scenario_id = scenario_id
		st.session_state.latest_configuration_signature = current_signature
		st.session_state.search_error = None
		reset_simulation_state(st.session_state)
	except SafeRouteError as error:
		reset_result_state()
		st.session_state.latest_configuration_signature = current_signature
		st.session_state.search_error = str(error)

current_step = None
normalize_playback_interval(st.session_state)
normalize_playback_state(st.session_state, st.session_state.latest_result)

with graph_col:
	render_section_title("Scenario View")
	scenario_summary_columns = st.columns(2)
	with scenario_summary_columns[0]:
		render_centered_card("Scenario", scenario.name)
	with scenario_summary_columns[1]:
		render_centered_card("Optimization mode", format_optimization_mode_label(optimization_mode))
	st.caption(_cost_formula_summary(optimization_mode))

	if st.session_state.latest_result is None:
		st.info("Configure the scenario and search settings, then select Run Search.")
		graph_figure = build_graph_figure(
			scenario_graph,
			start_node=start_node,
			goal_node=goal_node,
			optimization_mode=configuration.optimization_mode,
			risk_weight=configuration.risk_weight,
		)
		st.plotly_chart(graph_figure, width="stretch")
	else:
		result = st.session_state.latest_result
		current_index = int(st.session_state.current_step_index)
		at_first_step = current_index <= 0
		at_last_step = simulation_complete(result, current_index)
		is_playing = bool(st.session_state.simulation_playing)

		navigation_columns = st.columns(4)
		previous_clicked = navigation_columns[0].button(
			"Previous",
			disabled=at_first_step or is_playing,
			width="stretch",
			key="simulation_previous",
		)
		next_clicked = navigation_columns[1].button(
			"Next",
			disabled=at_last_step or is_playing,
			width="stretch",
			key="simulation_next",
		)
		reset_clicked = navigation_columns[2].button(
			"Reset",
			width="stretch",
			key="simulation_reset",
		)
		complete_clicked = navigation_columns[3].button(
			"Run to Completion",
			disabled=at_last_step,
			width="stretch",
			key="simulation_complete",
		)

		st.caption("Playback controls")
		playback_columns = st.columns([1, 1, 1.5])
		autoplay_clicked = playback_columns[0].button(
			"Auto Play",
			disabled=is_playing or at_last_step,
			width="stretch",
			key="simulation_autoplay",
		)
		pause_clicked = playback_columns[1].button(
			"Pause",
			disabled=not is_playing,
			width="stretch",
			key="simulation_pause",
		)
		playback_labels = tuple(PLAYBACK_INTERVALS)
		current_interval = normalize_playback_interval(st.session_state)
		current_speed_label = PLAYBACK_LABELS_BY_INTERVAL[current_interval]
		if st.session_state.get("playback_speed_label") not in playback_labels:
			st.session_state.pop("playback_speed_label", None)
		selected_speed_label = playback_columns[2].selectbox(
			"Playback Speed",
			options=playback_labels,
			index=playback_labels.index(current_speed_label),
			key="playback_speed_label",
			label_visibility="collapsed",
		)
		st.session_state.playback_interval_seconds = PLAYBACK_INTERVALS[selected_speed_label]

		navigation_changed = False
		if autoplay_clicked:
			start_playback(st.session_state, result)
			navigation_changed = True
		elif pause_clicked:
			pause_playback(st.session_state)
			navigation_changed = True
		elif previous_clicked:
			set_simulation_step(st.session_state, result, previous_step(result, current_index))
			navigation_changed = True
		elif next_clicked:
			set_simulation_step(st.session_state, result, next_step(result, current_index))
			navigation_changed = True
		elif reset_clicked:
			reset_playback(st.session_state, result)
			navigation_changed = True
		elif complete_clicked:
			complete_playback(st.session_state, result)
			navigation_changed = True

		if navigation_changed:
			st.rerun()

		current_index = int(st.session_state.current_step_index)
		current_step = get_step(result, current_index)
		current_number, step_count, progress_fraction = get_simulation_progress(result, current_index)
		st.write(f"Step {current_number} of {step_count}")
		st.progress(progress_fraction, text=f"Progress: {current_number} / {step_count}")
		current_node_name = (
			format_node_name(scenario_graph, current_step.current_node)
			if current_step.current_node is not None
			else "None"
		)
		st.caption(
			f"Algorithm: {result.algorithm_name} | "
			f"Event: {humanize_identifier(current_step.event_type)} | "
			f"Current node: {current_node_name}"
		)

		graph_figure = build_search_step_figure(
			scenario_graph,
			current_step,
			result,
			configuration,
		)
		st.plotly_chart(graph_figure, width="stretch")

with results_col:
	render_section_title("Results")
	if st.session_state.search_error:
		st.error(st.session_state.search_error)
	elif st.session_state.latest_result is None:
		st.info("No search has been run yet.")
	else:
		result = st.session_state.latest_result
		render_search_step_state(
			scenario_graph,
			current_step,
			result,
			st.session_state.latest_configuration,
		)

if st.session_state.simulation_playing and st.session_state.latest_result is not None:
	time.sleep(normalize_playback_interval(st.session_state))
	advance_playback(st.session_state, st.session_state.latest_result)
	st.rerun()
