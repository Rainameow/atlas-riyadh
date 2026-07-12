"""The simulation world — the top-level engine.

:class:`World` owns the city, the population, and the subsystems (clock, weather,
events, movement) and advances them one tick at a time. Each tick it decides
what every citizen intends to do, routes them if their goal changed, moves the
travelers along the road network, and applies the tick's effect on their energy
and happiness. It is pure Python with no I/O, so it can run headless, under
tests, or behind the API unchanged.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from atlas_core.city.model import CityModel
from atlas_core.config import get_logger
from atlas_core.simulation.agents.citizen import Citizen
from atlas_core.simulation.agents.factory import PopulationFactory
from atlas_core.simulation.behavior import resolve_destination
from atlas_core.simulation.clock import SimulationClock
from atlas_core.simulation.events import CityEvent, EventEffects, EventSystem
from atlas_core.simulation.routing import MovementController
from atlas_core.simulation.schedule import scheduled_activity
from atlas_core.simulation.types import TRANSPORT_SPEED_MS, Activity, TransportMode
from atlas_core.simulation.weather import WeatherState, WeatherSystem

log = get_logger(__name__)

# Per-tick change to (energy, happiness) while *performing* an activity.
_ACTIVITY_EFFECTS: dict[Activity, tuple[float, float]] = {
    Activity.SLEEP: (2.0, 0.1),
    Activity.HOME: (1.0, 0.1),
    Activity.WORK: (-0.6, -0.1),
    Activity.EAT: (3.0, 0.5),
    Activity.PRAY: (0.3, 0.6),
    Activity.SHOP: (-0.3, 0.3),
    Activity.SOCIALIZE: (-0.2, 0.6),
    Activity.EXERCISE: (-0.6, 0.8),
}
# Per-tick effect while traveling (commute fatigue).
_TRAVEL_EFFECT = (-0.3, -0.1)


@dataclass(frozen=True, slots=True)
class CitizenSnapshot:
    """A lightweight, serializable view of a citizen for transport/persistence."""

    id: int
    lat: float
    lon: float
    activity: str
    traveling: bool
    energy: float
    happiness: float


class World:
    """The living city.

    Args:
        city: The assembled city model.
        population: Number of citizens to generate.
        seed: RNG seed for a reproducible world.
        minutes_per_tick: Simulated minutes advanced per :meth:`step`.
    """

    def __init__(
        self,
        city: CityModel,
        population: int,
        *,
        seed: int = 42,
        minutes_per_tick: int = 5,
    ) -> None:
        self.city = city
        self._rng = random.Random(seed)
        self.clock = SimulationClock(minutes_per_tick=minutes_per_tick)
        self.weather = WeatherSystem(self._rng)
        self.events = EventSystem()
        self._movement = MovementController(city.network)
        self.citizens: list[Citizen] = PopulationFactory(city, self._rng).create(population)
        log.info("world created", population=population, seed=seed)

    # -- Control -------------------------------------------------------------

    def add_event(self, event: CityEvent) -> None:
        self.events.add(event)

    def step(self) -> None:
        """Advance the world by one tick."""
        self.clock.tick()
        self.weather.update(self.clock.day_index)

        weather_state = self.weather.state_at(self.clock.hour_of_day)
        event_effects = self.events.effects(self.clock.total_minutes)

        for citizen in self.citizens:
            self._update_citizen(citizen, weather_state, event_effects)

    def run(self, ticks: int) -> None:
        """Advance the world by ``ticks`` ticks."""
        for _ in range(ticks):
            self.step()

    # -- Per-citizen update --------------------------------------------------

    def _update_citizen(
        self, citizen: Citizen, weather_state: WeatherState, event_effects: EventEffects
    ) -> None:
        intended = scheduled_activity(self.clock, citizen)

        # Re-plan only when the goal changes (or the citizen is idle with no
        # destination) — this prevents per-tick route thrashing.
        needs_plan = intended != citizen.activity or (
            citizen.destination is None and not citizen.is_traveling
        )
        if needs_plan:
            citizen.activity = intended
            destination = resolve_destination(
                citizen, intended, self.city, weather_state, event_effects, self._rng
            )
            self._movement.assign_route(citizen, destination)

        if citizen.is_traveling:
            distance = self._tick_distance(citizen, weather_state, event_effects)
            self._movement.advance(citizen, distance)
            citizen.adjust_energy(_TRAVEL_EFFECT[0])
            citizen.adjust_happiness(_TRAVEL_EFFECT[1])
        else:
            energy_delta, happiness_delta = _ACTIVITY_EFFECTS.get(citizen.activity, (0.0, 0.0))
            citizen.adjust_energy(energy_delta)
            citizen.adjust_happiness(happiness_delta)

    def _tick_distance(
        self, citizen: Citizen, weather_state: WeatherState, event_effects: EventEffects
    ) -> float:
        """Metres a citizen can travel this tick, given mode, weather, events."""
        mode = citizen.preferred_transport
        if mode == TransportMode.METRO and event_effects.metro_blocked:
            mode = TransportMode.BUS  # metro outage -> fall back to the bus
        base_ms = TRANSPORT_SPEED_MS[mode]
        effective_ms = base_ms * weather_state.speed_factor * event_effects.speed_factor
        return effective_ms * self.clock.minutes_per_tick * 60.0

    # -- Observation ---------------------------------------------------------

    def snapshot(self) -> list[CitizenSnapshot]:
        """Return a serializable snapshot of every citizen's current state."""
        return [
            CitizenSnapshot(
                id=c.id,
                lat=round(c.position.lat, 6),
                lon=round(c.position.lon, 6),
                activity=c.activity.value,
                traveling=c.is_traveling,
                energy=round(c.energy, 1),
                happiness=round(c.happiness, 1),
            )
            for c in self.citizens
        ]

    def metrics(self) -> dict[str, object]:
        """Return aggregate metrics for dashboards and monitoring."""
        traveling = sum(c.is_traveling for c in self.citizens)
        by_activity: dict[str, int] = {}
        total_energy = 0.0
        total_happiness = 0.0
        for c in self.citizens:
            by_activity[c.activity.value] = by_activity.get(c.activity.value, 0) + 1
            total_energy += c.energy
            total_happiness += c.happiness
        n = len(self.citizens)
        weather_state = self.weather.state_at(self.clock.hour_of_day)
        return {
            "day": self.clock.day_index,
            "day_name": self.clock.day_name,
            "time": self.clock.clock_label(),
            "population": n,
            "traveling": traveling,
            "by_activity": by_activity,
            "avg_energy": round(total_energy / n, 1) if n else 0.0,
            "avg_happiness": round(total_happiness / n, 1) if n else 0.0,
            "weather": weather_state.condition.value,
            "temperature_c": weather_state.temperature_c,
            "active_events": [e.name for e in self.events.active(self.clock.total_minutes)],
        }
