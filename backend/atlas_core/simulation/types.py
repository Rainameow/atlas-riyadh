"""Core enumerations and value objects for the simulation engine.

These are small, framework-free types shared across the agent, scheduling,
routing, weather, and event modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from atlas_core.city.types import LatLon


class Occupation(StrEnum):
    """What a citizen does on a working day; drives workplace and hours."""

    OFFICE_WORKER = "office_worker"
    HEALTHCARE_WORKER = "healthcare_worker"
    RETAIL_WORKER = "retail_worker"
    STUDENT = "student"
    RETIRED = "retired"
    CHILD = "child"


class TransportMode(StrEnum):
    """A citizen's preferred way of getting around."""

    WALK = "walk"
    CAR = "car"
    BUS = "bus"
    METRO = "metro"


class Activity(StrEnum):
    """The activity a citizen is currently doing or heading toward.

    Movement is implicit: when the target location differs from the citizen's
    position they are *en route* to it; once arrived they are *performing* it.
    """

    SLEEP = "sleep"
    PRAY = "pray"
    WORK = "work"
    EAT = "eat"
    SHOP = "shop"
    EXERCISE = "exercise"
    SOCIALIZE = "socialize"
    HOME = "home"


# Free-flow travel speeds in metres per second by transport mode. These are
# base speeds; weather and congestion scale them down at runtime.
TRANSPORT_SPEED_MS: dict[TransportMode, float] = {
    TransportMode.WALK: 1.35,
    TransportMode.CAR: 11.0,  # ~40 km/h effective urban speed
    TransportMode.BUS: 7.5,
    TransportMode.METRO: 15.0,
}

# Activities that take place outdoors and are therefore weather-sensitive.
OUTDOOR_ACTIVITIES: frozenset[Activity] = frozenset({Activity.EXERCISE})


@dataclass(frozen=True, slots=True)
class Destination:
    """A resolved place a citizen can travel to.

    Decouples the movement layer from :class:`~atlas_core.city.types.Building`
    and :class:`~atlas_core.city.types.Poi`: both reduce to a coordinate, the
    nearest road-graph node, and a human-readable label.
    """

    location: LatLon
    node: int
    label: str
