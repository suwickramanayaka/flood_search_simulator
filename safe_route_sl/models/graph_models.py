"""Graph and scenario data models used by SafeRouteSL."""

from __future__ import annotations

from dataclasses import dataclass

from utils.constants import FLOOD_RISK_LABELS, ROAD_CONDITION_PENALTIES, SUPPORTED_LOCATION_TYPES
from utils.exceptions import DataValidationError


@dataclass(frozen=True, slots=True)
class Location:
    id: str
    name: str
    short_name: str
    location_type: str
    latitude: float
    longitude: float
    capacity: int
    available: bool
    description: str

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise DataValidationError("Location id cannot be empty")
        if not self.name.strip():
            raise DataValidationError(f"Location {self.id!r} must have a name")
        if not self.short_name.strip():
            raise DataValidationError(f"Location {self.id!r} must have a short_name")
        if self.location_type not in SUPPORTED_LOCATION_TYPES:
            raise DataValidationError(
                f"Unsupported location type for {self.id!r}: {self.location_type!r}"
            )
        if not -90.0 <= self.latitude <= 90.0:
            raise DataValidationError(f"Invalid latitude for location {self.id!r}: {self.latitude!r}")
        if not -180.0 <= self.longitude <= 180.0:
            raise DataValidationError(f"Invalid longitude for location {self.id!r}: {self.longitude!r}")
        if self.capacity < 0:
            raise DataValidationError(f"Location {self.id!r} capacity cannot be negative")


@dataclass(frozen=True, slots=True)
class Road:
    source: str
    target: str
    road_name: str
    distance_km: float
    travel_time_min: float
    flood_risk: int
    road_condition: str
    blocked: bool

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.target.strip():
            raise DataValidationError("Road endpoints cannot be empty")
        if self.source == self.target:
            raise DataValidationError(f"Road {self.source!r} -> {self.target!r} cannot be a self-loop")
        if self.distance_km <= 0:
            raise DataValidationError(
                f"Road {self.source!r} -> {self.target!r} must have positive distance"
            )
        if self.travel_time_min <= 0:
            raise DataValidationError(
                f"Road {self.source!r} -> {self.target!r} must have positive travel time"
            )
        if self.flood_risk not in FLOOD_RISK_LABELS:
            raise DataValidationError(
                f"Road {self.source!r} -> {self.target!r} has invalid flood risk {self.flood_risk!r}"
            )
        if self.road_condition not in ROAD_CONDITION_PENALTIES:
            raise DataValidationError(
                f"Road {self.source!r} -> {self.target!r} has unsupported road condition {self.road_condition!r}"
            )


@dataclass(frozen=True, slots=True)
class EdgeOverride:
    source: str
    target: str
    blocked: bool | None = None
    flood_risk: int | None = None
    distance_km: float | None = None
    travel_time_min: float | None = None
    road_condition: str | None = None

    def __post_init__(self) -> None:
        if not self.source.strip() or not self.target.strip():
            raise DataValidationError("Scenario edge override endpoints cannot be empty")
        if self.source == self.target:
            raise DataValidationError("Scenario edge override cannot be a self-loop")


@dataclass(frozen=True, slots=True)
class NodeOverride:
    node_id: str
    available: bool | None = None
    capacity: int | None = None

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise DataValidationError("Scenario node override node_id cannot be empty")


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    name: str
    description: str
    edge_overrides: tuple[EdgeOverride, ...]
    node_overrides: tuple[NodeOverride, ...]

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise DataValidationError("Scenario id cannot be empty")
        if not self.name.strip():
            raise DataValidationError(f"Scenario {self.id!r} must have a name")
