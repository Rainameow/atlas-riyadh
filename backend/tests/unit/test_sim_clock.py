"""Tests for the simulation world clock."""

from __future__ import annotations

from atlas_core.simulation.clock import SimulationClock


def test_tick_advances_total_minutes() -> None:
    clock = SimulationClock(minutes_per_tick=5)
    clock.tick()
    clock.tick()
    assert clock.total_minutes == 10
    assert clock.tick_count == 2


def test_hour_and_minute_of_day() -> None:
    clock = SimulationClock(minutes_per_tick=15)
    for _ in range(4 * 9):  # 9 hours
        clock.tick()
    assert clock.minute_of_day == 9 * 60
    assert clock.hour == 9
    assert clock.minute == 0
    assert clock.hour_of_day == 9.0
    assert clock.clock_label() == "09:00"


def test_day_rollover_and_weekday_names() -> None:
    clock = SimulationClock(minutes_per_tick=60)
    for _ in range(24):  # one full day
        clock.tick()
    assert clock.day_index == 1
    assert clock.day_name == "Monday"  # starts on Sunday


def test_riyadh_weekend_is_friday_saturday() -> None:
    clock = SimulationClock(minutes_per_tick=24 * 60)  # one tick == one day
    days = []
    for _ in range(7):
        days.append((clock.day_name, clock.is_weekend))
        clock.tick()
    weekend_days = {name for name, weekend in days if weekend}
    assert weekend_days == {"Friday", "Saturday"}
