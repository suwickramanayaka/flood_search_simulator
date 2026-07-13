"""Optional SimpleAI compatibility helpers for SafeRouteSL."""

from __future__ import annotations

try:
	import simpleai  # type: ignore
except Exception:  # pragma: no cover - optional dependency
	simpleai = None


def is_simpleai_available() -> bool:
	return simpleai is not None


def get_simpleai_status() -> str:
	if simpleai is None:
		return "SimpleAI unavailable (optional)"

	version = getattr(simpleai, "__version__", "unknown")
	return f"SimpleAI available ({version})"
