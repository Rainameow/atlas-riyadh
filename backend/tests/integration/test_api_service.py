"""Fast tests for the simulation service logic (no network, no event loop task).

These inject a world built on the in-memory ``sample_city`` fixture, so they
exercise the control/read logic without loading real OSM data or starting the
background tick loop.
"""

from __future__ import annotations

import pytest
from api.schemas import ControlAction, ControlRequest, EventPreset
from api.service import SimulationService
from atlas_core.simulation import World
from atlas_core.simulation.weather import WeatherCondition


@pytest.fixture
def service(sample_city) -> SimulationService:
    svc = SimulationService()
    svc._world = World(sample_city, population=30, seed=1, minutes_per_tick=5)
    return svc


async def test_pause_and_play(service: SimulationService) -> None:
    state = await service.control(ControlRequest(action=ControlAction.PAUSE))
    assert state.running is False
    state = await service.control(ControlRequest(action=ControlAction.PLAY))
    assert state.running is True


async def test_set_speed(service: SimulationService) -> None:
    state = await service.control(
        ControlRequest(action=ControlAction.SET_SPEED, tick_interval_seconds=0.5)
    )
    assert state.tick_interval_seconds == 0.5


async def test_set_weather_forces_condition(service: SimulationService) -> None:
    await service.control(
        ControlRequest(action=ControlAction.SET_WEATHER, weather=WeatherCondition.SANDSTORM)
    )
    assert service.world.weather.state.condition is WeatherCondition.SANDSTORM


async def test_reset_changes_population(service: SimulationService) -> None:
    state = await service.control(ControlRequest(action=ControlAction.RESET, population=12))
    assert state.metrics.population == 12
    assert len(service.world.citizens) == 12


async def test_add_event_appears_in_metrics(service: SimulationService) -> None:
    await service.control(
        ControlRequest(action=ControlAction.ADD_EVENT, event=EventPreset.RIYADH_SEASON)
    )
    assert "Riyadh Season" in service.state().metrics.active_events


def test_tick_payload_shape(service: SimulationService) -> None:
    payload = service.tick_payload()
    assert payload["type"] == "tick"
    assert len(payload["citizens"]) == 30
    assert {"id", "lat", "lon", "activity"}.issubset(payload["citizens"][0])


def test_city_summary_and_pois(service: SimulationService) -> None:
    summary = service.city_summary()
    assert summary.name == "TestCity"
    assert summary.pois > 0
    pois = service.map_pois()
    assert any(p.category == "mosque" for p in pois)
