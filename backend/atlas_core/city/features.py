"""Convert OSM feature GeoDataFrames into typed domain objects.

The ingest pipeline hands GeoPandas ``GeoDataFrame``s (buildings, POIs) to these
functions, which classify each row, reduce its geometry to a representative
point, snap it to the nearest road-graph node, and emit the framework-free
:class:`~atlas_core.city.types.Building` / :class:`~atlas_core.city.types.Poi`
dataclasses the simulation consumes.
"""

from __future__ import annotations

from typing import Any

import geopandas as gpd

from atlas_core.city.categories import classify_building, classify_poi
from atlas_core.city.network import RoadNetwork
from atlas_core.city.types import Building, LatLon, Poi

# Metric CRS suitable for the Arabian Peninsula, used for area computation.
_AREA_CRS = "EPSG:32638"  # UTM zone 38N (covers Riyadh)


def _representative_point(geom: Any) -> LatLon | None:
    """Return a point guaranteed to lie on/within the geometry, in lat/lon."""
    if geom is None or geom.is_empty:
        return None
    point = geom.representative_point()
    return LatLon(lat=float(point.y), lon=float(point.x))


def _row_tags(row: Any, columns: list[str]) -> dict[str, Any]:
    """Extract the OSM tag columns from a GeoDataFrame row as a plain dict."""
    return {col: row[col] for col in columns if col in row.index}


def _stable_id(index_value: Any, fallback: int) -> int:
    """Derive an integer id from a GeoDataFrame index entry.

    OSMnx indexes features by ``(element_type, osmid)``; we use the osmid when
    present and fall back to positional order otherwise.
    """
    if isinstance(index_value, tuple):
        for part in reversed(index_value):
            if isinstance(part, int | float) and not isinstance(part, bool):
                return int(part)
    if isinstance(index_value, int | float) and not isinstance(index_value, bool):
        return int(index_value)
    return fallback


def buildings_from_gdf(gdf: gpd.GeoDataFrame, network: RoadNetwork) -> list[Building]:
    """Build :class:`Building` objects from a footprint GeoDataFrame."""
    if gdf.empty:
        return []

    areas = gdf.to_crs(_AREA_CRS).geometry.area
    tag_columns = [c for c in gdf.columns if c != "geometry"]

    centroids: list[LatLon] = []
    kept: list[tuple[int, Any, float]] = []
    for pos, (index_value, row) in enumerate(gdf.iterrows()):
        point = _representative_point(row.geometry)
        if point is None:
            continue
        centroids.append(point)
        kept.append((pos, (index_value, row), float(areas.iloc[pos])))

    nearest = network.nearest_nodes(centroids)

    buildings: list[Building] = []
    for (pos, (index_value, row), area), point, node in zip(kept, centroids, nearest, strict=True):
        tags = _row_tags(row, tag_columns)
        buildings.append(
            Building(
                id=_stable_id(index_value, pos),
                category=classify_building(tags),
                centroid=point,
                nearest_node=node,
                area_m2=round(area, 2),
                name=_clean_name(tags.get("name")),
            )
        )
    return buildings


def pois_from_gdf(gdf: gpd.GeoDataFrame, network: RoadNetwork) -> list[Poi]:
    """Build :class:`Poi` objects from a points-of-interest GeoDataFrame."""
    if gdf.empty:
        return []

    tag_columns = [c for c in gdf.columns if c != "geometry"]
    locations: list[LatLon] = []
    kept: list[tuple[int, Any]] = []
    for pos, (index_value, row) in enumerate(gdf.iterrows()):
        point = _representative_point(row.geometry)
        if point is None:
            continue
        locations.append(point)
        kept.append((pos, (index_value, row)))

    nearest = network.nearest_nodes(locations)

    pois: list[Poi] = []
    for (pos, (index_value, row)), point, node in zip(kept, locations, nearest, strict=True):
        tags = _row_tags(row, tag_columns)
        pois.append(
            Poi(
                id=_stable_id(index_value, pos),
                category=classify_poi(tags),
                location=point,
                nearest_node=node,
                name=_clean_name(tags.get("name")),
            )
        )
    return pois


def _clean_name(value: Any) -> str | None:
    if value is None or isinstance(value, float):  # NaN
        return None
    text = str(value).strip()
    return text or None
