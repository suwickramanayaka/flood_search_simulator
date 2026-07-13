"""SafeRouteSL application entry point."""

from __future__ import annotations

import streamlit as st


st.set_page_config(
	page_title="SafeRouteSL",
	page_icon="🌊",
	layout="wide",
	initial_sidebar_state="expanded",
)

st.title("SafeRouteSL")
st.subheader("Interactive flood-evacuation search for education")
st.write(
	"SafeRouteSL models a synthetic Sri Lankan local-road network where flooding can increase risk, "
	"change travel conditions, block roads, or make an evacuation destination unavailable."
)
st.markdown(
	"""
### What you can explore

- **Interactive Simulation:** run a custom search once, then inspect or automatically replay its recorded steps.
- **Algorithm Comparison:** compare routes, search effort, and approximate educational execution times across five algorithms.
- **Problem Model:** review the state space, constraints, costs, heuristics, scenarios, and synthetic dataset.
- **Toolkit Validation:** compare selected custom results with NetworkX reference implementations.

Use the sidebar to open any page.
"""
)

st.info("Educational simulation using synthetic data. Not for real emergency decision-making.")
