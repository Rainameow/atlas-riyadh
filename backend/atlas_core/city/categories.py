"""OSM tag taxonomy for Atlas.

OpenStreetMap describes features with free-form ``key=value`` tags. Atlas
collapses the relevant subset into two small, stable enumerations — one for
point-like places of interest (:class:`PoiCategory`) and one for building land
use (:class:`BuildingCategory`) — so the simulation reasons about a handful of
semantic categories rather than hundreds of raw tags.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any


class PoiCategory(StrEnum):
    """Semantic category for a place of interest.

    Covers the destinations the brief calls out (mosques, schools, hospitals,
    malls, parks, metro stations, the airport) plus the everyday places
    citizens visit in their routines.
    """

    MOSQUE = "mosque"
    SCHOOL = "school"
    UNIVERSITY = "university"
    HOSPITAL = "hospital"
    CLINIC = "clinic"
    MALL = "mall"
    SHOP = "shop"
    RESTAURANT = "restaurant"
    CAFE = "cafe"
    PARK = "park"
    GYM = "gym"
    METRO_STATION = "metro_station"
    BUS_STATION = "bus_station"
    AIRPORT = "airport"
    GOVERNMENT = "government"
    OTHER = "other"


class BuildingCategory(StrEnum):
    """Land-use category for a building footprint."""

    RESIDENTIAL = "residential"
    OFFICE = "office"
    RETAIL = "retail"
    INDUSTRIAL = "industrial"
    EDUCATION = "education"
    HEALTHCARE = "healthcare"
    RELIGIOUS = "religious"
    CIVIC = "civic"
    OTHER = "other"


# OSM tag sets requested from Overpass for POIs. Kept as a mapping of
# ``key -> list of accepted values`` (``True`` means "any value").
POI_OSM_TAGS: dict[str, Any] = {
    "amenity": [
        "place_of_worship",
        "school",
        "university",
        "college",
        "hospital",
        "clinic",
        "doctors",
        "restaurant",
        "fast_food",
        "cafe",
        "bus_station",
        "townhall",
    ],
    "shop": ["mall", "supermarket", "department_store"],
    "leisure": ["park", "fitness_centre", "sports_centre", "stadium"],
    "railway": ["station", "subway_entrance"],
    "station": ["subway"],
    "aeroway": ["aerodrome", "terminal"],
    "office": ["government"],
}

# OSM tags requested for building footprints.
BUILDING_OSM_TAGS: dict[str, Any] = {"building": True}


def classify_poi(tags: dict[str, Any]) -> PoiCategory:
    """Map a feature's OSM tags to a :class:`PoiCategory`.

    Classification is order-sensitive: more specific / higher-signal tags are
    checked first so, e.g., a mosque (``amenity=place_of_worship`` +
    ``religion=muslim``) is not mislabeled as generic government or shop.
    """
    amenity = _clean(tags.get("amenity"))
    shop = _clean(tags.get("shop"))
    leisure = _clean(tags.get("leisure"))
    railway = _clean(tags.get("railway"))
    aeroway = _clean(tags.get("aeroway"))
    office = _clean(tags.get("office"))
    religion = _clean(tags.get("religion"))
    station = _clean(tags.get("station"))

    if aeroway in {"aerodrome", "terminal"}:
        return PoiCategory.AIRPORT
    if railway in {"station", "subway_entrance"} or station == "subway":
        return PoiCategory.METRO_STATION
    if amenity == "place_of_worship":
        # Riyadh's places of worship are overwhelmingly mosques; treat the
        # muslim tag (or an untagged religion) as a mosque.
        return PoiCategory.MOSQUE if religion in {"muslim", None, ""} else PoiCategory.OTHER
    if amenity == "hospital":
        return PoiCategory.HOSPITAL
    if amenity in {"clinic", "doctors"}:
        return PoiCategory.CLINIC
    if amenity == "university" or amenity == "college":
        return PoiCategory.UNIVERSITY
    if amenity == "school":
        return PoiCategory.SCHOOL
    if amenity in {"restaurant", "fast_food"}:
        return PoiCategory.RESTAURANT
    if amenity == "cafe":
        return PoiCategory.CAFE
    if amenity == "bus_station":
        return PoiCategory.BUS_STATION
    if amenity == "townhall" or office == "government":
        return PoiCategory.GOVERNMENT
    if shop == "mall" or shop == "department_store":
        return PoiCategory.MALL
    if shop in {"supermarket"}:
        return PoiCategory.SHOP
    if leisure == "park":
        return PoiCategory.PARK
    if leisure in {"fitness_centre", "sports_centre"}:
        return PoiCategory.GYM
    if leisure == "stadium":
        return PoiCategory.PARK
    return PoiCategory.OTHER


def classify_building(tags: dict[str, Any]) -> BuildingCategory:
    """Map a building footprint's OSM tags to a :class:`BuildingCategory`."""
    building = _clean(tags.get("building"))
    amenity = _clean(tags.get("amenity"))
    shop = _clean(tags.get("shop"))
    office = _clean(tags.get("office"))

    if building in {"house", "apartments", "residential", "detached", "dormitory", "villa"}:
        return BuildingCategory.RESIDENTIAL
    if building in {"office", "commercial"} or office:
        return BuildingCategory.OFFICE
    if building in {"retail", "supermarket", "mall"} or shop:
        return BuildingCategory.RETAIL
    if building in {"industrial", "warehouse", "factory"}:
        return BuildingCategory.INDUSTRIAL
    if building in {"school", "university", "college", "kindergarten"} or amenity in {
        "school",
        "university",
        "college",
    }:
        return BuildingCategory.EDUCATION
    if building in {"hospital"} or amenity in {"hospital", "clinic"}:
        return BuildingCategory.HEALTHCARE
    if building in {"mosque", "church", "cathedral"} or amenity == "place_of_worship":
        return BuildingCategory.RELIGIOUS
    if building in {"government", "civic", "public"} or amenity == "townhall":
        return BuildingCategory.CIVIC
    if building in {"yes", "", None}:
        # Untagged footprints dominate OSM; default to residential, which is the
        # most common land use in a city and keeps the population housed.
        return BuildingCategory.RESIDENTIAL
    return BuildingCategory.OTHER


def _clean(value: Any) -> str | None:
    """Normalize an OSM tag value to a lowercase string or ``None``.

    GeoDataFrame cells are often ``NaN`` (a float) for absent tags; treat those
    and empty strings as missing.
    """
    if value is None:
        return None
    if isinstance(value, float):  # NaN
        return None
    text = str(value).strip().lower()
    return text or None
