"""Reusable centered summary cards for SafeRouteSL pages."""

from __future__ import annotations

from html import escape

import streamlit as st


def build_centered_card_html(label: str, value: object, *, prominent: bool = False) -> str:
	"""Return escaped, theme-neutral HTML with centered label and value text."""
	label_html = escape(str(label))
	value_html = escape(str(value)).replace("\n", "<br>")
	value_size = "1.85rem" if prominent else "1rem"
	minimum_height = "4.5rem" if prominent else "3.25rem"
	return (
		f'<div style="width:100%; min-height:{minimum_height}; box-sizing:border-box; '
		'margin-bottom:0.75rem; padding:0.85rem 1rem; '
		'border:1px solid rgba(128, 128, 128, 0.45); '
		'border-radius:0.5rem; text-align:center; overflow-wrap:anywhere; display:flex; '
		'flex-direction:column; align-items:center; justify-content:center;">'
		f'<div style="opacity:0.72; font-size:0.875rem; line-height:1.3; margin-bottom:0.45rem;">{label_html}</div>'
		f'<div style="font-size:{value_size}; font-weight:600; line-height:1.25;">{value_html}</div>'
		'</div>'
	)


def render_centered_card(label: str, value: object, *, prominent: bool = False) -> None:
	"""Render one bordered card whose label and value are centered."""
	st.markdown(
		build_centered_card_html(label, value, prominent=prominent),
		unsafe_allow_html=True,
	)
