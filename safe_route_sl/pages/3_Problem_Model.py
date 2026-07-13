"""Problem model page for SafeRouteSL."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from utils.constants import BALANCED_MODE, DISTANCE_MODE, OPTIMIZATION_MODE_LABELS, SAFETY_MODE, TIME_MODE


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


st.title("Problem Model")
st.write("SafeRouteSL models flood-safe evacuation routing as a weighted graph search problem.")

st.subheader("Local Problem")
st.write("The project demonstrates how routes across Sri Lankan local roads change when flooding increases risk or blocks roads.")

st.subheader("Graph Representation")
st.markdown(
	"""
- Nodes represent locations.
- Edges represent roads.
- Edge attributes represent distance, time, risk, and road condition.
"""
)

st.subheader("Search Problem")
st.markdown(
	"""
- Initial state: the selected start location.
- Goal state: the selected evacuation destination.
- Actions: traverse a traversable road to a neighbouring node.
- Transition model: moving across an edge updates the current location and accumulated cost.
- Goal test: the current node matches the selected goal.
- Path cost: the sum of selected edge costs.
- Heuristic: straight-line Haversine distance or zero.
"""
)

st.subheader("Cost Modes")
st.markdown(
	"""
- Distance: `cost = distance_km`
- Time: `cost = travel_time_min`
- Safety: `cost = distance_km + risk_weight × flood_risk + road_condition_penalty`
- Balanced: `cost = distance_km + 0.5 × travel_time_min + risk_weight × flood_risk + road_condition_penalty`
"""
)

st.subheader("Algorithm Theory")
theory_rows = pd.DataFrame(
	[
		{"Algorithm": "Breadth-First Search", "Frontier": "Queue", "Complete": "Yes on finite graphs", "Weighted optimal": "No", "Heuristic": "No"},
		{"Algorithm": "Depth-First Search", "Frontier": "Stack", "Complete": "Yes for this finite graph implementation", "Weighted optimal": "No", "Heuristic": "No"},
		{"Algorithm": "Uniform-Cost Search", "Frontier": "Priority queue", "Complete": "Yes", "Weighted optimal": "Yes", "Heuristic": "No"},
		{"Algorithm": "Greedy Best-First Search", "Frontier": "Priority queue", "Complete": "Yes for this finite graph implementation", "Weighted optimal": "No", "Heuristic": "Yes"},
		{"Algorithm": "A* Search", "Frontier": "Priority queue", "Complete": "Yes under suitable conditions", "Weighted optimal": "Conditional", "Heuristic": "Yes"},
	]
)
st.dataframe(theory_rows, use_container_width=True, hide_index=True)

st.subheader("Dataset Tables")
st.write("Location data")
st.dataframe(load_locations_dataframe(), use_container_width=True, hide_index=True)

st.write("Road data")
st.dataframe(load_roads_dataframe(), use_container_width=True, hide_index=True)

st.write("Scenario descriptions")
st.dataframe(load_scenarios_dataframe(), use_container_width=True, hide_index=True)

st.info("Educational simulation using synthetic data. Not for real emergency decision-making.")
