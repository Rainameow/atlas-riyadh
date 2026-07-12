"""Integration tests for the World orchestrator over the sample city."""

from __future__ import annotations

from atlas_core.city.types import LatLon
from atlas_core.simulation.events import CityEvent, EventType
from atlas_core.simulation.types import Destination
from atlas_core.simulation.world import World

_TICKS_PER_DAY = (24 * 60) // 5  # minutes_per_tick == 5


def test_world_creates_requested_population(sample_city) -> None:
    world = World(sample_city, population=25, seed=1)
    assert len(world.citizens) == 25


def test_step_advances_clock(sample_city) -> None:
    world = World(sample_city, population=10, seed=1, minutes_per_tick=5)
    world.step()
    assert world.clock.total_minutes == 5


def test_full_day_runs_without_error_and_reports_metrics(sample_city) -> None:
    world = World(sample_city, population=40, seed=2)
    world.run(_TICKS_PER_DAY)
    metrics = world.metrics()
    for key in ("day", "time", "population", "traveling", "by_activity", "weather"):
        assert key in metrics
    assert metrics["population"] == 40


def test_snapshot_shape(sample_city) -> None:
    world = World(sample_city, population=15, seed=3)
    world.run(10)
    snap = world.snapshot()
    assert len(snap) == 15
    first = snap[0]
    assert isinstance(first.lat, float)
    assert isinstance(first.activity, str)


def test_world_is_deterministic_for_a_seed(sample_city) -> None:
    a = World(sample_city, population=20, seed=5)
    b = World(sample_city, population=20, seed=5)
    a.run(50)
    b.run(50)
    assert [(c.id, c.position) for c in a.citizens] == [(c.id, c.position) for c in b.citizens]


def test_citizens_exhibit_varied_activities_over_a_day(sample_city) -> None:
    world = World(sample_city, population=60, seed=7)
    seen: set[str] = set()
    for _ in range(_TICKS_PER_DAY):
        world.step()
        seen.update(c.activity.value for c in world.citizens)
    # A realistic day should include sleeping, working, and at least one more.
    assert {"sleep", "work"}.issubset(seen)
    assert len(seen) >= 4


def test_active_event_appears_in_metrics(sample_city) -> None:
    world = World(sample_city, population=10, seed=1, minutes_per_tick=5)
    # An event active across the whole first day.
    venue = Destination(LatLon(24.71, 46.61), node=3, label="Boulevard")
    world.add_event(
        CityEvent(EventType.RIYADH_SEASON, "Riyadh Season", 0, 24 * 60, venue=venue, attraction=0.5)
    )
    world.step()
    assert "Riyadh Season" in world.metrics()["active_events"]
