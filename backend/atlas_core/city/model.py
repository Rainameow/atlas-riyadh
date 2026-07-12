"""The assembled city model.

:class:`CityModel` binds the road network, building footprints, and points of
interest into one queryable object. It is the single input the simulation
engine needs to place a population, plan routes, and choose destinations.
"""

from __future__ import annotations

from collections import defaultdict
from functools import cached_property

from atlas_core.city.categories import BuildingCategory, PoiCategory
from atlas_core.city.network import RoadNetwork
from atlas_core.city.spatial import SpatialIndex
from atlas_core.city.types import Building, LatLon, Poi


class CityModel:
    """A fully assembled, queryable city.

    Args:
        name: City name (e.g. ``"Riyadh"``).
        network: The road network the population moves over.
        buildings: All building footprints.
        pois: All points of interest.
    """

    def __init__(
        self,
        name: str,
        network: RoadNetwork,
        buildings: list[Building],
        pois: list[Poi],
    ) -> None:
        self.name = name
        self.network = network
        self.buildings = buildings
        self.pois = pois

    # -- Category groupings --------------------------------------------------

    @cached_property
    def buildings_by_category(self) -> dict[BuildingCategory, list[Building]]:
        grouped: dict[BuildingCategory, list[Building]] = defaultdict(list)
        for building in self.buildings:
            grouped[building.category].append(building)
        return dict(grouped)

    @cached_property
    def pois_by_category(self) -> dict[PoiCategory, list[Poi]]:
        grouped: dict[PoiCategory, list[Poi]] = defaultdict(list)
        for poi in self.pois:
            grouped[poi.category].append(poi)
        return dict(grouped)

    def buildings_of(self, category: BuildingCategory) -> list[Building]:
        return self.buildings_by_category.get(category, [])

    def pois_of(self, category: PoiCategory) -> list[Poi]:
        return self.pois_by_category.get(category, [])

    # -- Spatial queries -----------------------------------------------------

    @cached_property
    def _poi_indexes(self) -> dict[PoiCategory, SpatialIndex[Poi]]:
        return {
            category: SpatialIndex(items, lambda p: p.location)
            for category, items in self.pois_by_category.items()
        }

    def nearest_poi(self, category: PoiCategory, location: LatLon) -> Poi | None:
        """Return the nearest POI of ``category`` to ``location``."""
        index = self._poi_indexes.get(category)
        return index.nearest(location) if index else None

    # -- Summary -------------------------------------------------------------

    def summary(self) -> dict[str, object]:
        """Return a compact, serializable summary of the city's contents."""
        return {
            "name": self.name,
            "nodes": len(self.network),
            "edges": self.network.graph.number_of_edges(),
            "buildings": len(self.buildings),
            "pois": len(self.pois),
            "buildings_by_category": {
                c.value: len(v) for c, v in sorted(self.buildings_by_category.items())
            },
            "pois_by_category": {c.value: len(v) for c, v in sorted(self.pois_by_category.items())},
        }
