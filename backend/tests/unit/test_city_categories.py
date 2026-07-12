"""Tests for the OSM tag classification taxonomy."""

from __future__ import annotations

import math

from atlas_core.city.categories import (
    BuildingCategory,
    PoiCategory,
    classify_building,
    classify_poi,
)


def test_mosque_classified_from_place_of_worship() -> None:
    assert classify_poi({"amenity": "place_of_worship", "religion": "muslim"}) is PoiCategory.MOSQUE


def test_airport_takes_priority() -> None:
    assert classify_poi({"aeroway": "aerodrome", "amenity": "cafe"}) is PoiCategory.AIRPORT


def test_metro_station_from_railway() -> None:
    assert classify_poi({"railway": "station", "station": "subway"}) is PoiCategory.METRO_STATION


def test_mall_and_park_and_gym() -> None:
    assert classify_poi({"shop": "mall"}) is PoiCategory.MALL
    assert classify_poi({"leisure": "park"}) is PoiCategory.PARK
    assert classify_poi({"leisure": "fitness_centre"}) is PoiCategory.GYM


def test_unknown_poi_is_other() -> None:
    assert classify_poi({"barrier": "gate"}) is PoiCategory.OTHER


def test_nan_tag_values_are_ignored() -> None:
    # GeoDataFrame cells use NaN (float) for missing tags.
    assert classify_poi({"amenity": math.nan, "shop": "mall"}) is PoiCategory.MALL


def test_building_classification() -> None:
    assert classify_building({"building": "apartments"}) is BuildingCategory.RESIDENTIAL
    assert classify_building({"building": "office"}) is BuildingCategory.OFFICE
    assert classify_building({"building": "hospital"}) is BuildingCategory.HEALTHCARE
    assert classify_building({"building": "mosque"}) is BuildingCategory.RELIGIOUS


def test_untagged_building_defaults_residential() -> None:
    assert classify_building({"building": "yes"}) is BuildingCategory.RESIDENTIAL
