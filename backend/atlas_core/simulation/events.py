"""City events subsystem.

Events are time-boxed occurrences that perturb citizen behaviour and the road
network: a Riyadh Season concert or football match pulls crowds toward a venue;
a road closure or metro outage degrades part of the transport system. The
:class:`EventSystem` tracks which events are active at the current time and
exposes their aggregate effect to the behaviour and routing layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from atlas_core.simulation.types import Destination


class EventType(StrEnum):
    RIYADH_SEASON = "riyadh_season"
    FOOTBALL_MATCH = "football_match"
    CONCERT = "concert"
    ROAD_CLOSURE = "road_closure"
    METRO_OUTAGE = "metro_outage"


@dataclass(frozen=True, slots=True)
class CityEvent:
    """A scheduled city event.

    Attributes:
        event_type: The kind of event.
        name: Human-readable label.
        start_minute: Absolute simulation minute the event begins.
        end_minute: Absolute simulation minute the event ends.
        venue: Where crowds are drawn (for attraction events); ``None`` for
            disruptions like road closures.
        attraction: Probability (0..1) that an eligible citizen is pulled to the
            venue for evening leisure while the event is active.
        speed_penalty: Multiplier applied to travel speed while active
            (1.0 == no effect); models congestion or closures.
        blocks_metro: Whether the event disables metro travel.
    """

    event_type: EventType
    name: str
    start_minute: int
    end_minute: int
    venue: Destination | None = None
    attraction: float = 0.0
    speed_penalty: float = 1.0
    blocks_metro: bool = False

    def is_active(self, total_minutes: int) -> bool:
        return self.start_minute <= total_minutes < self.end_minute


@dataclass
class EventEffects:
    """Aggregate effect of all active events at a moment in time."""

    speed_factor: float = 1.0
    metro_blocked: bool = False
    attractions: list[tuple[Destination, float]] = field(default_factory=list)


class EventSystem:
    """Registry of city events with time-aware effect resolution."""

    def __init__(self, events: list[CityEvent] | None = None) -> None:
        self._events: list[CityEvent] = list(events or [])

    def add(self, event: CityEvent) -> None:
        self._events.append(event)

    def clear(self) -> None:
        self._events.clear()

    @property
    def events(self) -> list[CityEvent]:
        return list(self._events)

    def active(self, total_minutes: int) -> list[CityEvent]:
        return [e for e in self._events if e.is_active(total_minutes)]

    def effects(self, total_minutes: int) -> EventEffects:
        """Combine all active events into a single :class:`EventEffects`."""
        result = EventEffects()
        for event in self.active(total_minutes):
            result.speed_factor *= event.speed_penalty
            result.metro_blocked = result.metro_blocked or event.blocks_metro
            if event.venue is not None and event.attraction > 0:
                result.attractions.append((event.venue, event.attraction))
        return result
