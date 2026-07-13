"""Shared page-level typography and section-heading styles for SafeRouteSL."""

from __future__ import annotations

from html import escape

import streamlit as st


def apply_page_styles() -> None:
	"""Apply the common page title, spacing, and section-heading visual language."""
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
		</style>
		""",
		unsafe_allow_html=True,
	)


def render_page_title(title: str) -> None:
	"""Render an escaped, centered primary page title."""
	st.markdown(
		f'<h1 class="safe-route-page-title">{escape(title)}</h1>',
		unsafe_allow_html=True,
	)


def render_section_title(title: str) -> None:
	"""Render an escaped secondary heading using the shared section style."""
	st.markdown(
		f'<h2 class="safe-route-section-title">{escape(title)}</h2>',
		unsafe_allow_html=True,
	)
