"""Tests for the behaviour (activity -> destination) resolver."""

from __future__ import annotations

import random

from atlas_core.city.categories import PoiCategory
from atlas_core.city.model import CityModel
from atlas_core.simulation.behavior import resolve_destination
from atlas_core.simulation.events import EventEffects
from atlas_core.simulation.types import Activity, Destination
from atlas_core.simulation.weather import WeatherCondition, WeatherSystem


def _weather(condition: WeatherCondition):
    return WeatherSystem(random.Random(0), condition).state


def _no_events() -> EventEffects:
    return EventEffects()


def test_work_resolves_to_workplace(sample_city, make_citizen) -> None:
    citizen = make_citizen()
    dest = resolve_destination(
        citizen,
        Activity.WORK,
        sample_city,
        _weather(WeatherCondition.CLEAR),
        _no_events(),
        random.Random(0),
    )
    assert dest == citizen.workplace


def test_pray_resolves_to_a_mosque(sample_city, make_citizen) -> None:
    citizen = make_citizen()
    dest = resolve_destination(
        citizen,
        Activity.PRAY,
        sample_city,
        _weather(WeatherCondition.CLEAR),
        _no_events(),
        random.Random(0),
    )
    assert dest.node == 2  # the mosque node in sample_city


def test_exercise_is_outdoors_in_clear_weather(sample_city, make_citizen) -> None:
    citizen = make_citizen()
    dest = resolve_destination(
        citizen,
        Activity.EXERCISE,
        sample_city,
        _weather(WeatherCondition.CLEAR),
        _no_events(),
        random.Random(0),
    )
    park = sample_city.pois_of(PoiCategory.PARK)[0]
    assert dest.node == park.nearest_node


def test_exercise_moves_indoors_in_sandstorm(sample_city, make_citizen) -> None:
    citizen = make_citizen()
    dest = resolve_destination(
        citizen,
        Activity.EXERCISE,
        sample_city,
        _weather(WeatherCondition.SANDSTORM),
        _no_events(),
        random.Random(0),
    )
    gym = sample_city.pois_of(PoiCategory.GYM)[0]
    assert dest.node == gym.nearest_node


def test_event_attraction_diverts_leisure(sample_city, make_citizen) -> None:
    citizen = make_citizen()
    venue = Destination(sample_city.network.node_coords(3), node=3, label="Boulevard")
    effects = EventEffects(attractions=[(venue, 1.0)])  # certain pull
    dest = resolve_destination(
        citizen,
        Activity.SHOP,
        sample_city,
        _weather(WeatherCondition.CLEAR),
        effects,
        random.Random(0),
    )
    assert dest == venue


def test_missing_category_falls_back_home(grid_network, make_citizen) -> None:
    # A city with no POIs at all -> resolver returns the citizen's home.
    empty_city = CityModel(name="Empty", network=grid_network, buildings=[], pois=[])
    citizen = make_citizen()
    dest = resolve_destination(
        citizen,
        Activity.PRAY,
        empty_city,
        _weather(WeatherCondition.CLEAR),
        _no_events(),
        random.Random(0),
    )
    assert dest == citizen.home
