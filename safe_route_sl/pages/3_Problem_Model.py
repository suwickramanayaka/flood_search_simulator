"""Problem model page for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from visualizations.page_style import apply_page_styles, render_page_title, render_section_title


st.set_page_config(
	page_title="Problem Model | SafeRouteSL",
	page_icon="🌊",
	layout="wide",
	initial_sidebar_state="expanded",
)
apply_page_styles()

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"


@st.cache_data
def load_locations_dataframe() -> pd.DataFrame:
	return pd.read_csv(DATA_DIR / "locations.csv")


@st.cache_data
def load_roads_dataframe() -> pd.DataFrame:
	return pd.read_csv(DATA_DIR / "roads.csv")


@st.cache_data
def load_scenarios_dataframe() -> pd.DataFrame:
	scenarios = pd.read_json(DATA_DIR / "scenarios.json")
	return scenarios[["id", "name", "description"]]


render_page_title("Problem Model")
st.write("SafeRouteSL represents a synthetic Sri Lankan flood-evacuation problem as deterministic graph search.")
st.caption("Educational simulation using synthetic data. Not for real emergency decision-making.")

render_section_title("Problem Statement")
st.write(
	"Select a traversable route from a local starting location to an available evacuation destination while road flooding, "
	"travel conditions, and the selected optimization objective influence the route."
)

render_section_title("State-Space Model")
st.write(
	"A state identifies the current location and the recorded route used to reach it. Graph nodes represent locations; "
	"undirected edges represent local roads with distance, travel-time, flood-risk, condition, and blocked attributes."
)

render_section_title("Initial State")
st.write("The initial state is the available start node selected by the user.")

render_section_title("Goal State")
st.write("The goal state is the selected available shelter, hospital, school, community hall, temple, or relief centre.")

render_section_title("Actions")
st.write("From the current node, an action traverses one open road to an available neighbouring node.")

render_section_title("Transition Model")
st.write("Traversing an edge changes the current node, extends the path, and adds the edge's selected cost.")

render_section_title("Goal Test")
st.write("The goal test succeeds when the current node equals the selected goal node.")

render_section_title("Constraints")
st.markdown(
	"""
- Blocked roads are excluded from traversal.
- Unavailable locations cannot be used as selectable destinations or traversed nodes.
- Start and goal nodes must exist, be available, and be different for an ordinary route search.
- Costs and risk weights must be non-negative and road data must pass validation.
- Scenario overrides are applied to graph copies so the base graph is not mutated.
"""
)

render_section_title("Path-Cost Functions")
st.markdown(
	"""
- **Shortest Distance:** `cost = distance_km`
- **Fastest Travel Time:** `cost = travel_time_min`
- **Safest Route:** `cost = distance_km + risk_weight × flood_risk + road_condition_penalty`
- **Balanced Route:** `cost = distance_km + 0.5 × travel_time_min + risk_weight × flood_risk + road_condition_penalty`

Safety and balanced totals are educational composite scores and do not represent a real-world physical unit.
"""
)

render_section_title("Heuristic")
st.write(
	"Haversine Distance estimates straight-line distance from a node to the goal. It supports normal distance-mode A* "
	"validation, but is only an educational estimate for time, safety, and balanced costs. A Zero Heuristic is also "
	"available and makes A* behave like Uniform-Cost Search."
)

render_section_title("Search Algorithm Properties")
theory_rows = pd.DataFrame(
	[
		{"Algorithm": "Breadth-First Search", "Frontier": "Queue", "Complete": "Yes on finite graphs", "Weighted optimal": "No", "Heuristic": "No"},
		{"Algorithm": "Depth-First Search", "Frontier": "Stack", "Complete": "Yes for this finite graph implementation", "Weighted optimal": "No", "Heuristic": "No"},
		{"Algorithm": "Uniform-Cost Search", "Frontier": "Priority queue", "Complete": "Yes", "Weighted optimal": "Yes", "Heuristic": "No"},
		{"Algorithm": "Greedy Best-First Search", "Frontier": "Priority queue", "Complete": "Yes for this finite graph implementation", "Weighted optimal": "No", "Heuristic": "Yes"},
		{"Algorithm": "A* Search", "Frontier": "Priority queue", "Complete": "Yes under suitable conditions", "Weighted optimal": "Conditional", "Heuristic": "Yes"},
	]
)
st.dataframe(theory_rows, width="stretch", hide_index=True)

render_section_title("Dataset")
st.write(
	"The fictional dataset contains readable location records and road records. It is deliberately small enough for "
	"students to inspect the graph and follow every recorded search step."
)
st.write("Locations")
st.dataframe(load_locations_dataframe(), width="stretch", hide_index=True)

st.write("Roads")
st.dataframe(load_roads_dataframe(), width="stretch", hide_index=True)

render_section_title("Scenarios")
st.write(
	"Scenario definitions apply edge or node overrides for normal conditions, a flooded bridge, severe flooding, an "
	"unavailable shelter, and multiple similar-cost routes."
)
st.dataframe(load_scenarios_dataframe(), width="stretch", hide_index=True)

render_section_title("Toolkit Roles")
st.markdown(
	"""
- Custom Python algorithms remain the simulator's primary implementations and produce the recorded search steps.
- NetworkX provides reference BFS, Dijkstra, and A* results for academic validation.
- SimpleAI support is optional and is not required to run the application.
- Reference toolkits may return different but equally valid paths; matching edge count or weighted cost can matter more than an identical node sequence.
"""
)

render_section_title("Limitations")
st.markdown(
	"""
- Locations, roads, coordinates, capacities, conditions, and flood values are synthetic.
- The graph is small and static apart from predefined scenario overrides.
- Flood risk is an ordinal educational input, not a live forecast or calibrated hazard model.
- Approximate execution times are classroom observations, not scientific performance benchmarks.
- Route output must not be used for emergency response, public safety, or real navigation.
"""
)
