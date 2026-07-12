"""The Citizen agent.

A :class:`Citizen` is an autonomous agent with a home, a workplace, a daily
routine, and mutable state (position, energy, happiness) that evolves each tick.
The agent holds data and small self-contained state helpers; decision-making
(where to go) lives in the behaviour module and movement in the routing module,
keeping each responsibility in one place.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from atlas_core.city.types import LatLon
from atlas_core.simulation.types import (
    Activity,
    Destination,
    Occupation,
    TransportMode,
)

# Bounds for the two homeostatic drives.
_MIN = 0.0
_MAX = 100.0


@dataclass
class Citizen:
    """An autonomous city inhabitant.

    Identity & profile (fixed at creation):
        id, age, occupation, home, workplace, preferred_transport.

    Live state (evolves each tick):
        position, current_node, activity, destination, route, route_polyline,
        route_cursor_m (metres travelled along the current route),
        route_length_m, energy, happiness.
    """

    id: int
    age: int
    occupation: Occupation
    home: Destination
    workplace: Destination | None
    preferred_transport: TransportMode

    position: LatLon
    current_node: int
    # Propensity (0..1) to attend prayers; fixed per citizen for stable routines.
    prayer_propensity: float = 0.5
    activity: Activity = Activity.SLEEP

    destination: Destination | None = None
    route: list[int] = field(default_factory=list)
    route_polyline: list[LatLon] = field(default_factory=list)
    route_cumulative_m: list[float] = field(default_factory=list)
    route_cursor_m: float = 0.0

    energy: float = 100.0
    happiness: float = 70.0

    @property
    def is_traveling(self) -> bool:
        """True when the agent has an active route it has not yet completed."""
        return bool(self.route) and self.route_cursor_m < self.route_length_m

    @property
    def route_length_m(self) -> float:
        return self.route_cumulative_m[-1] if self.route_cumulative_m else 0.0

    def clear_route(self) -> None:
        """Drop any active route (used on arrival or destination change)."""
        self.route = []
        self.route_polyline = []
        self.route_cumulative_m = []
        self.route_cursor_m = 0.0

    def adjust_energy(self, delta: float) -> None:
        self.energy = _clamp(self.energy + delta)

    def adjust_happiness(self, delta: float) -> None:
        self.happiness = _clamp(self.happiness + delta)


def _clamp(value: float) -> float:
    return max(_MIN, min(_MAX, value))
