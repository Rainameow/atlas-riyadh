"""Tests for the weather subsystem."""

from __future__ import annotations

import random

from atlas_core.simulation.weather import WeatherCondition, WeatherSystem


def test_adverse_weather_reduces_speed_and_outdoor_activity() -> None:
    clear = WeatherSystem(random.Random(0), WeatherCondition.CLEAR).state
    sandstorm = WeatherSystem(random.Random(0), WeatherCondition.SANDSTORM).state
    assert sandstorm.speed_factor < clear.speed_factor
    assert sandstorm.outdoor_factor < clear.outdoor_factor


def test_force_pins_condition_until_cleared() -> None:
    system = WeatherSystem(random.Random(1))
    system.force(WeatherCondition.HEATWAVE)
    for day in range(1, 30):
        system.update(day)
    assert system.state.condition is WeatherCondition.HEATWAVE
    system.clear_override()
    for day in range(30, 60):
        system.update(day)
    # After clearing, evolution is free to (eventually) change it.
    assert isinstance(system.state.condition, WeatherCondition)


def test_weather_evolution_is_deterministic_for_a_seed() -> None:
    a = WeatherSystem(random.Random(7))
    b = WeatherSystem(random.Random(7))
    seq_a, seq_b = [], []
    for day in range(1, 20):
        a.update(day)
        b.update(day)
        seq_a.append(a.state.condition)
        seq_b.append(b.state.condition)
    assert seq_a == seq_b


def test_diurnal_temperature_varies_by_hour() -> None:
    system = WeatherSystem(random.Random(0), WeatherCondition.CLEAR)
    dawn = system.state_at(5.0).temperature_c
    afternoon = system.state_at(15.0).temperature_c
    assert afternoon > dawn
