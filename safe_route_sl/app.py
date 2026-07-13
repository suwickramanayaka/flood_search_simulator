"""SafeRouteSL application entry point."""

from __future__ import annotations

import streamlit as st

from visualizations.page_style import apply_page_styles, render_page_title, render_section_title


st.set_page_config(
	page_title="SafeRouteSL",
	page_icon="🌊",
	layout="wide",
	initial_sidebar_state="expanded",
)
apply_page_styles()

render_page_title("SafeRouteSL")
st.subheader("Interactive flood-evacuation search for education")
st.write(
	"SafeRouteSL models a synthetic Sri Lankan local-road network where flooding can increase risk, "
	"change travel conditions, block roads, or make an evacuation destination unavailable."
)
render_section_title("What you can explore")
st.markdown(
	"""
- **Interactive Simulation:** run a custom search once, then inspect or automatically replay its recorded steps.
- **Algorithm Comparison:** compare routes, search effort, and approximate educational execution times across five algorithms.
- **Problem Model:** review the state space, constraints, costs, heuristics, scenarios, and synthetic dataset.
- **Toolkit Validation:** compare selected custom results with NetworkX reference implementations.

Use the sidebar to open any page.
"""
)

st.info("Educational simulation using synthetic data. Not for real emergency decision-making.")
