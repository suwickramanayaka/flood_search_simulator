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
st.subheader("Flood-safe evacuation routing for educational use")
st.write(
	"Use the interactive simulation page to choose a scenario, configure a search, and inspect the final route and metrics."
)
st.info("Educational simulation using synthetic data. Not for real emergency decision-making.")

st.markdown(
	"""
### Navigation
Use the Streamlit pages in the sidebar to open the interactive simulation, compare algorithms, or review the problem model.
"""
)
