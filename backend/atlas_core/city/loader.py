"""Load a :class:`CityModel` from the on-disk OSM cache.

This is the public entry point the simulation uses to obtain a ready-to-run
city. It reads the cached artifacts (downloading them first if absent) and
assembles the road network, buildings, and POIs into a single model.
"""

from __future__ import annotations

import geopandas as gpd
import networkx as nx
import osmnx as ox

from atlas_core.city.features import buildings_from_gdf, pois_from_gdf
from atlas_core.city.ingest import CachePaths, cache_paths, ingest_city
from atlas_core.city.model import CityModel
from atlas_core.city.network import RoadNetwork
from atlas_core.config import get_logger, get_settings
from atlas_core.config.settings import Settings

log = get_logger(__name__)


def load_city(settings: Settings | None = None, *, auto_ingest: bool = True) -> CityModel:
    """Load the configured city from cache, ingesting first if needed.

    Args:
        settings: Configuration; defaults to the process settings singleton.
        auto_ingest: When ``True`` and the cache is missing, download it first.
            When ``False`` and the cache is missing, raise ``FileNotFoundError``.

    Returns:
        A fully assembled :class:`CityModel`.
    """
    settings = settings or get_settings()
    paths = cache_paths(settings)

    if not paths.all_exist():
        if not auto_ingest:
            raise FileNotFoundError(
                f"city cache missing at {settings.cache_dir}; run "
                "`python -m atlas_core.city.ingest` first"
            )
        ingest_city(settings)

    return build_city_from_cache(settings.city.name, paths)


def build_city_from_cache(name: str, paths: CachePaths) -> CityModel:
    """Assemble a :class:`CityModel` from resolved cache paths."""
    log.info("loading city from cache", city=name)
    graph: nx.MultiDiGraph = ox.load_graphml(paths.graph)
    network = RoadNetwork(graph)

    buildings_gdf = gpd.read_parquet(paths.buildings)
    pois_gdf = gpd.read_parquet(paths.pois)

    buildings = buildings_from_gdf(buildings_gdf, network)
    pois = pois_from_gdf(pois_gdf, network)

    city = CityModel(name=name, network=network, buildings=buildings, pois=pois)
    log.info("city loaded", **{k: v for k, v in city.summary().items() if isinstance(v, int)})
    return city
