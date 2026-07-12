"""The live simulation service.

Owns the single :class:`~atlas_core.simulation.world.World` instance, advances it
on a background asyncio task, and broadcasts each tick to connected WebSocket
clients. All world mutation (stepping, control actions, resets) is serialized
under one lock so the tick loop and HTTP control requests never race.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass

from atlas_core.city.categories import PoiCategory
from atlas_core.city.loader import load_city
from atlas_core.config import get_logger, get_settings
from atlas_core.simulation import CityEvent, EventType, World
from atlas_core.simulation.types import Destination
from atlas_core.simulation.weather import WeatherCondition

from api.schemas import (
    CategoryCount,
    CitizenState,
    CitySummary,
    ControlRequest,
    EventPreset,
    PoiFeature,
    SimulationMetrics,
    SimulationState,
    TickMessage,
)
from api.websocket.manager import ConnectionManager

log = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class _EventSpec:
    """Venue category and disruption profile for an event preset."""

    type: EventType
    name: str
    venue_category: PoiCategory | None
    attraction: float
    speed_penalty: float
    blocks_metro: bool = False


_EVENT_PRESETS: dict[EventPreset, _EventSpec] = {
    EventPreset.RIYADH_SEASON: _EventSpec(
        EventType.RIYADH_SEASON, "Riyadh Season", PoiCategory.MALL, 0.5, 0.85
    ),
    EventPreset.FOOTBALL_MATCH: _EventSpec(
        EventType.FOOTBALL_MATCH, "Football Match", PoiCategory.PARK, 0.4, 0.8
    ),
    EventPreset.CONCERT: _EventSpec(EventType.CONCERT, "Concert", PoiCategory.MALL, 0.45, 0.85),
    EventPreset.ROAD_CLOSURE: _EventSpec(EventType.ROAD_CLOSURE, "Road Closure", None, 0.0, 0.6),
    EventPreset.METRO_OUTAGE: _EventSpec(
        EventType.METRO_OUTAGE, "Metro Outage", None, 0.0, 1.0, blocks_metro=True
    ),
}

# POI categories exposed to the map as static reference layers.
_MAP_POI_CATEGORIES = (
    PoiCategory.MOSQUE,
    PoiCategory.MALL,
    PoiCategory.PARK,
    PoiCategory.HOSPITAL,
    PoiCategory.METRO_STATION,
    PoiCategory.UNIVERSITY,
)


class SimulationService:
    """Singleton coordinating the world, its tick loop, and broadcasts."""

    def __init__(self) -> None:
        settings = get_settings()
        self._settings = settings
        self._population = min(settings.simulation.default_population, 1500)
        self._minutes_per_tick = settings.simulation.minutes_per_tick
        self._interval = settings.simulation.tick_interval_seconds
        self._seed = settings.simulation.random_seed

        self._manager = ConnectionManager()
        self._lock = asyncio.Lock()
        self._running = True
        self._stop = asyncio.Event()
        self._task: asyncio.Task[None] | None = None
        self._world: World | None = None

    @property
    def manager(self) -> ConnectionManager:
        return self._manager

    @property
    def world(self) -> World:
        if self._world is None:
            raise RuntimeError("simulation not started")
        return self._world

    # -- Lifecycle -----------------------------------------------------------

    async def startup(self) -> None:
        """Load the city (off the event loop) and start the tick loop."""
        log.info("loading city", population=self._population)
        city = await asyncio.to_thread(load_city)
        self._world = World(
            city,
            population=self._population,
            seed=self._seed,
            minutes_per_tick=self._minutes_per_tick,
        )
        self._task = asyncio.create_task(self._run_loop())
        log.info("simulation started")

    async def shutdown(self) -> None:
        self._stop.set()
        if self._task is not None:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task

    async def _run_loop(self) -> None:
        while not self._stop.is_set():
            if self._running and self._world is not None:
                async with self._lock:
                    self._world.step()
                    payload = self.tick_payload()
                await self._manager.broadcast_json(payload)
            await asyncio.sleep(self._interval)

    # -- Control -------------------------------------------------------------

    async def control(self, request: ControlRequest) -> SimulationState:
        async with self._lock:
            match request.action:
                case request.action.PLAY:
                    self._running = True
                case request.action.PAUSE:
                    self._running = False
                case request.action.SET_SPEED:
                    if request.tick_interval_seconds is not None:
                        self._interval = request.tick_interval_seconds
                case request.action.SET_WEATHER:
                    if request.weather is not None:
                        self.world.weather.force(WeatherCondition(request.weather))
                case request.action.ADD_EVENT:
                    if request.event is not None:
                        self._add_event(request.event)
                case request.action.RESET:
                    self._reset(request.population)
        return self.state()

    def _reset(self, population: int | None) -> None:
        if population is not None:
            self._population = population
        self._world = World(
            self.world.city,
            population=self._population,
            seed=self._seed,
            minutes_per_tick=self._minutes_per_tick,
        )

    def _add_event(self, preset: EventPreset) -> None:
        spec = _EVENT_PRESETS[preset]
        world = self.world
        now = world.clock.total_minutes
        venue: Destination | None = None
        if spec.venue_category is not None:
            pois = world.city.pois_of(spec.venue_category)
            if pois:
                poi = pois[len(pois) // 2]  # a central-ish representative venue
                venue = Destination(poi.location, poi.nearest_node, poi.name or spec.name)
        world.add_event(
            CityEvent(
                event_type=spec.type,
                name=spec.name,
                start_minute=now,
                end_minute=now + 6 * 60,  # active for six simulated hours
                venue=venue,
                attraction=spec.attraction,
                speed_penalty=spec.speed_penalty,
                blocks_metro=spec.blocks_metro,
            )
        )

    # -- Read models ---------------------------------------------------------

    def state(self) -> SimulationState:
        return SimulationState(
            running=self._running,
            tick_interval_seconds=self._interval,
            metrics=self._metrics(),
        )

    def _metrics(self) -> SimulationMetrics:
        return SimulationMetrics(**self.world.metrics())

    def tick_payload(self) -> dict[str, object]:
        citizens = [
            CitizenState(
                id=s.id,
                lat=s.lat,
                lon=s.lon,
                activity=s.activity,
                traveling=s.traveling,
                energy=s.energy,
                happiness=s.happiness,
            )
            for s in self.world.snapshot()
        ]
        return TickMessage(metrics=self._metrics(), citizens=citizens).model_dump()

    def city_summary(self) -> CitySummary:
        city = self.world.city
        return CitySummary(
            name=city.name,
            nodes=len(city.network),
            edges=city.network.graph.number_of_edges(),
            buildings=len(city.buildings),
            pois=len(city.pois),
            pois_by_category=[
                CategoryCount(category=category.value, count=len(items))
                for category, items in sorted(city.pois_by_category.items())
            ],
        )

    def map_pois(self) -> list[PoiFeature]:
        features: list[PoiFeature] = []
        for category in _MAP_POI_CATEGORIES:
            for poi in self.world.city.pois_of(category):
                features.append(
                    PoiFeature(
                        id=poi.id,
                        category=poi.category.value,
                        name=poi.name,
                        lat=poi.location.lat,
                        lon=poi.location.lon,
                    )
                )
        return features


# Module-level singleton, wired up in the app lifespan.
service = SimulationService()
