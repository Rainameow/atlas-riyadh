"""Behaviour: turning an activity intent into a concrete destination.

The scheduler decides *what* a citizen wants to do; this module decides *where*
they do it, consulting the city (nearest mosque, mall, park…), the weather
(outdoor exercise in a park becomes indoor gym in a sandstorm), and active
events (a concert pulls evening crowds to its venue).
"""

from __future__ import annotations

import random
from typing import assert_never

from atlas_core.city.categories import PoiCategory
from atlas_core.city.model import CityModel
from atlas_core.city.types import LatLon, Poi
from atlas_core.simulation.agents.citizen import Citizen
from atlas_core.simulation.events import EventEffects
from atlas_core.simulation.types import Activity, Destination
from atlas_core.simulation.weather import WeatherState

# Activities eligible to be diverted to an active event venue.
_EVENT_ELIGIBLE: frozenset[Activity] = frozenset(
    {Activity.SHOP, Activity.SOCIALIZE, Activity.EAT, Activity.EXERCISE}
)
# Below this weather outdoor factor, exercise moves indoors (park -> gym).
_INDOOR_THRESHOLD = 0.5


def resolve_destination(
    citizen: Citizen,
    activity: Activity,
    city: CityModel,
    weather: WeatherState,
    events: EventEffects,
    rng: random.Random,
) -> Destination:
    """Resolve the destination for a citizen's intended activity."""
    # Event attraction can divert eligible leisure activities to a venue.
    if activity in _EVENT_ELIGIBLE:
        for venue, pull in events.attractions:
            if rng.random() < pull:
                return venue

    if activity in (Activity.SLEEP, Activity.HOME):
        return citizen.home
    if activity == Activity.WORK:
        return citizen.workplace or citizen.home
    if activity == Activity.PRAY:
        return _nearest(city, PoiCategory.MOSQUE, citizen.position, citizen.home)
    if activity == Activity.EAT:
        return _nearest(city, PoiCategory.RESTAURANT, citizen.position, citizen.home)
    if activity == Activity.SHOP:
        return _nearest(city, PoiCategory.MALL, citizen.position, citizen.home)
    if activity == Activity.SOCIALIZE:
        return _nearest(city, PoiCategory.CAFE, citizen.position, citizen.home)
    if activity == Activity.EXERCISE:
        # Outdoor park in fair weather; indoor gym otherwise.
        if weather.outdoor_factor >= _INDOOR_THRESHOLD:
            return _nearest(city, PoiCategory.PARK, citizen.position, citizen.home)
        return _nearest(city, PoiCategory.GYM, citizen.position, citizen.home)

    assert_never(activity)


def _nearest(
    city: CityModel, category: PoiCategory, origin: LatLon, fallback: Destination
) -> Destination:
    """Nearest POI of ``category`` to ``origin`` as a Destination, else fallback."""
    poi = city.nearest_poi(category, origin)
    if poi is None:
        return fallback
    return _poi_destination(poi)


def _poi_destination(poi: Poi) -> Destination:
    return Destination(
        location=poi.location,
        node=poi.nearest_node,
        label=poi.name or f"{poi.category.value}#{poi.id}",
    )
