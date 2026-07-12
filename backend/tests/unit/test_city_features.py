"""Tests for feature extraction, cache sanitization, and the load pipeline."""

from __future__ import annotations

import geopandas as gpd
import osmnx as ox
import pytest
from atlas_core.city.categories import BuildingCategory, PoiCategory
from atlas_core.city.features import buildings_from_gdf, pois_from_gdf
from atlas_core.city.ingest import CachePaths, _sanitize_features
from atlas_core.city.loader import build_city_from_cache
from atlas_core.city.network import RoadNetwork
from atlas_core.city.types import LatLon
from shapely.geometry import Point, Polygon


def _buildings_gdf() -> gpd.GeoDataFrame:
    rows = [
        {"building": "apartments", "name": "Tower A", "geometry": _square(46.6005, 24.7005)},
        {"building": "office", "name": "KAFD-ish", "geometry": _square(46.6095, 24.7005)},
    ]
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


def _pois_gdf() -> gpd.GeoDataFrame:
    rows = [
        {"amenity": "place_of_worship", "religion": "muslim", "geometry": Point(46.601, 24.701)},
        {"shop": "mall", "name": "Riyadh Mall", "geometry": Point(46.609, 24.709)},
    ]
    return gpd.GeoDataFrame(rows, crs="EPSG:4326")


def _square(lon: float, lat: float, d: float = 0.0005) -> Polygon:
    return Polygon([(lon - d, lat - d), (lon + d, lat - d), (lon + d, lat + d), (lon - d, lat + d)])


def test_buildings_from_gdf(grid_network: RoadNetwork) -> None:
    buildings = buildings_from_gdf(_buildings_gdf(), grid_network)
    assert len(buildings) == 2
    categories = {b.category for b in buildings}
    assert categories == {BuildingCategory.RESIDENTIAL, BuildingCategory.OFFICE}
    # Each building is snapped to a real graph node and has a positive area.
    assert all(b.nearest_node in grid_network.node_ids for b in buildings)
    assert all(b.area_m2 > 0 for b in buildings)


def test_pois_from_gdf(grid_network: RoadNetwork) -> None:
    pois = pois_from_gdf(_pois_gdf(), grid_network)
    by_cat = {p.category: p for p in pois}
    assert PoiCategory.MOSQUE in by_cat
    assert PoiCategory.MALL in by_cat
    assert by_cat[PoiCategory.MALL].name == "Riyadh Mall"


def test_empty_gdf_yields_no_features(grid_network: RoadNetwork) -> None:
    empty = gpd.GeoDataFrame({"geometry": []}, crs="EPSG:4326")
    assert buildings_from_gdf(empty, grid_network) == []
    assert pois_from_gdf(empty, grid_network) == []


def test_sanitize_features_is_parquet_safe_and_id_stable(tmp_path) -> None:
    gdf = _pois_gdf()
    sanitized = _sanitize_features(gdf)
    path = tmp_path / "pois.parquet"
    sanitized.to_parquet(path)
    reloaded = gpd.read_parquet(path)
    assert len(reloaded) == 2
    assert "geometry" in reloaded.columns
    assert reloaded.index.name == "atlas_id"


def test_full_load_pipeline_round_trip(grid_graph, tmp_path) -> None:
    """Save a graph + feature tables to a cache and reload into a CityModel."""
    paths = CachePaths(
        graph=tmp_path / "city_graph.graphml",
        buildings=tmp_path / "city_buildings.parquet",
        pois=tmp_path / "city_pois.parquet",
    )
    ox.save_graphml(grid_graph, filepath=paths.graph)
    _sanitize_features(_buildings_gdf()).to_parquet(paths.buildings)
    _sanitize_features(_pois_gdf()).to_parquet(paths.pois)

    city = build_city_from_cache("TestCity", paths)

    summary = city.summary()
    assert summary["buildings"] == 2
    assert summary["pois"] == 2
    assert summary["nodes"] == 4

    mosque = city.nearest_poi(PoiCategory.MOSQUE, LatLon(24.701, 46.601))
    assert mosque is not None
    assert mosque.category is PoiCategory.MOSQUE


@pytest.mark.integration
@pytest.mark.slow
def test_real_riyadh_ingest_and_load() -> None:
    """End-to-end ingest of the configured city from the live Overpass API.

    Skipped by default (requires network). Enable with:
        pytest -m slow --run-slow
    """
    from atlas_core.city.loader import load_city

    city = load_city()
    assert len(city.network) > 100
    assert len(city.buildings) > 0
