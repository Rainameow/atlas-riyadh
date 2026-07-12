"""Tests for the city events subsystem."""

from __future__ import annotations

from atlas_core.city.types import LatLon
from atlas_core.simulation.events import CityEvent, EventSystem, EventType
from atlas_core.simulation.types import Destination


def _venue() -> Destination:
    return Destination(LatLon(24.71, 46.61), node=3, label="Boulevard")


def test_event_active_window() -> None:
    event = CityEvent(EventType.CONCERT, "Concert", start_minute=100, end_minute=200)
    assert not event.is_active(99)
    assert event.is_active(100)
    assert event.is_active(199)
    assert not event.is_active(200)


def test_effects_combine_speed_and_metro_and_attractions() -> None:
    system = EventSystem(
        [
            CityEvent(EventType.ROAD_CLOSURE, "Closure", 0, 500, speed_penalty=0.5),
            CityEvent(EventType.METRO_OUTAGE, "Outage", 0, 500, blocks_metro=True),
            CityEvent(
                EventType.RIYADH_SEASON,
                "Season",
                0,
                500,
                venue=_venue(),
                attraction=0.4,
            ),
        ]
    )
    effects = system.effects(100)
    assert effects.speed_factor == 0.5
    assert effects.metro_blocked is True
    assert len(effects.attractions) == 1
    assert effects.attractions[0][1] == 0.4


def test_inactive_events_have_no_effect() -> None:
    system = EventSystem([CityEvent(EventType.CONCERT, "C", 0, 50, speed_penalty=0.2)])
    effects = system.effects(100)
    assert effects.speed_factor == 1.0
    assert effects.metro_blocked is False
    assert effects.attractions == []
