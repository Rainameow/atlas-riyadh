"""Tests for daily routine scheduling."""

from __future__ import annotations

from atlas_core.simulation.clock import SimulationClock
from atlas_core.simulation.schedule import in_prayer_window, scheduled_activity
from atlas_core.simulation.types import Activity, Occupation


def _clock_at(hour: int, minute: int = 0, *, day: int = 0) -> SimulationClock:
    """A clock positioned at a specific time on a chosen day (day 0 = Sunday)."""
    return SimulationClock(minutes_per_tick=1, total_minutes=day * 24 * 60 + hour * 60 + minute)


def test_sleeps_overnight(make_citizen) -> None:
    citizen = make_citizen()
    assert scheduled_activity(_clock_at(2), citizen) is Activity.SLEEP


def test_office_worker_works_on_weekday(make_citizen) -> None:
    citizen = make_citizen(occupation=Occupation.OFFICE_WORKER)
    assert scheduled_activity(_clock_at(9), citizen) is Activity.WORK


def test_no_work_on_weekend(make_citizen) -> None:
    citizen = make_citizen(occupation=Occupation.OFFICE_WORKER)
    # Day 5 from a Sunday start is Friday (weekend).
    assert scheduled_activity(_clock_at(9, day=5), citizen) is not Activity.WORK


def test_retired_does_not_work(make_citizen) -> None:
    citizen = make_citizen(occupation=Occupation.RETIRED, has_workplace=False)
    assert scheduled_activity(_clock_at(9), citizen) is not Activity.WORK


def test_observant_citizen_prays_in_window(make_citizen) -> None:
    citizen = make_citizen(prayer_propensity=0.95)
    assert in_prayer_window(5 * 60 + 10)
    assert scheduled_activity(_clock_at(5, 10), citizen) is Activity.PRAY


def test_non_observant_citizen_skips_prayer(make_citizen) -> None:
    citizen = make_citizen(prayer_propensity=0.0)
    assert scheduled_activity(_clock_at(5, 10), citizen) is not Activity.PRAY


def test_leisure_choice_is_stable_within_a_day(make_citizen) -> None:
    citizen = make_citizen()
    a = scheduled_activity(_clock_at(21, 0), citizen)
    b = scheduled_activity(_clock_at(21, 30), citizen)
    assert a == b
    assert a in {Activity.SHOP, Activity.SOCIALIZE, Activity.EXERCISE, Activity.EAT}
