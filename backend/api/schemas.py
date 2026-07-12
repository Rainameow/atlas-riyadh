"""Pydantic request/response models for the Atlas API.

These DTOs form the contract between the backend and the React frontend. They
live in the API layer (not the engine) so the simulation core stays free of any
transport concerns.
"""

from __future__ import annotations

from enum import StrEnum

from atlas_core.simulation.weather import WeatherCondition
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "ok"
    city: str


class CategoryCount(BaseModel):
    category: str
    count: int


class CitySummary(BaseModel):
    name: str
    nodes: int
    edges: int
    buildings: int
    pois: int
    pois_by_category: list[CategoryCount]


class PoiFeature(BaseModel):
    """A single POI for the map's static layers."""

    id: int
    category: str
    name: str | None
    lat: float
    lon: float


class CitizenState(BaseModel):
    """One citizen's live position and status (streamed over WebSocket)."""

    id: int
    lat: float
    lon: float
    activity: str
    traveling: bool
    energy: float
    happiness: float


class SimulationMetrics(BaseModel):
    day: int
    day_name: str
    time: str
    population: int
    traveling: int
    by_activity: dict[str, int]
    avg_energy: float
    avg_happiness: float
    weather: str
    temperature_c: float
    active_events: list[str]


class SimulationState(BaseModel):
    running: bool
    tick_interval_seconds: float
    metrics: SimulationMetrics


class TickMessage(BaseModel):
    """The per-tick payload broadcast to every connected client."""

    type: str = "tick"
    metrics: SimulationMetrics
    citizens: list[CitizenState]


class ControlAction(StrEnum):
    PLAY = "play"
    PAUSE = "pause"
    RESET = "reset"
    SET_WEATHER = "set_weather"
    SET_SPEED = "set_speed"
    ADD_EVENT = "add_event"


class EventPreset(StrEnum):
    RIYADH_SEASON = "riyadh_season"
    FOOTBALL_MATCH = "football_match"
    CONCERT = "concert"
    ROAD_CLOSURE = "road_closure"
    METRO_OUTAGE = "metro_outage"


class ControlRequest(BaseModel):
    action: ControlAction
    weather: WeatherCondition | None = None
    tick_interval_seconds: float | None = Field(default=None, gt=0.05, le=10.0)
    population: int | None = Field(default=None, ge=1, le=20_000)
    event: EventPreset | None = None
