"""Domain-specific exceptions for SafeRouteSL."""


class SafeRouteError(Exception):
    """Base exception for the SafeRouteSL project."""


class DataValidationError(SafeRouteError):
    """Raised when CSV or JSON data is invalid."""


class GraphValidationError(SafeRouteError):
    """Raised when graph construction or validation fails."""


class ScenarioNotFoundError(SafeRouteError):
    """Raised when a requested scenario does not exist."""


class InvalidScenarioError(SafeRouteError):
    """Raised when scenario overrides are invalid."""


class InvalidOptimizationModeError(SafeRouteError):
    """Raised when an unsupported cost mode is requested."""


class UnavailableGoalError(SafeRouteError):
    """Raised when the selected goal is unavailable."""


class SimulationNavigationError(SafeRouteError):
    """Raised when search-history navigation cannot be completed."""
