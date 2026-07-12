"""Immutable domain types for the city data layer.

These are plain, framework-free dataclasses. They intentionally do not depend on
GeoPandas or SQLAlchemy so the simulation engine can consume them directly.
Geometry is reduced to what the engine needs: a representative point (centroid)
and the id of the nearest road-graph node.
"""

from __future__ import annotations

from dataclasses import dataclass

from atlas_core.city.categories import BuildingCategory, PoiCategory


@dataclass(frozen=True, slots=True)
class LatLon:
    """A WGS84 coordinate. ``lat`` is Y, ``lon`` is X."""

    lat: float
    lon: float


@dataclass(frozen=True, slots=True)
class Building:
    """A building footprint reduced to its centroid and land use.

    Attributes:
        id: Stable identifier (OSM element id when available).
        category: Land-use classification.
        centroid: Representative point of the footprint.
        nearest_node: Id of the closest node in the road graph; the point where
            an agent enters/exits the road network for this building.
        area_m2: Footprint area in square metres (used as a capacity proxy).
        name: Optional human-readable name.
    """

    id: int
    category: BuildingCategory
    centroid: LatLon
    nearest_node: int
    area_m2: float = 0.0
    name: str | None = None


@dataclass(frozen=True, slots=True)
class Poi:
    """A place of interest reduced to a point and a semantic category."""

    id: int
    category: PoiCategory
    location: LatLon
    nearest_node: int
    name: str | None = None
