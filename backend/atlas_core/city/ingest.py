"""OpenStreetMap ingestion and on-disk caching.

Downloading a city from the Overpass API is slow and rate-limited, so Atlas
downloads once and caches to disk: the road graph as GraphML and the building /
POI feature tables as GeoParquet. Every later run loads from that cache.

Run as a module to (re)build the cache for the configured city::

    python -m atlas_core.city.ingest          # build if missing
    python -m atlas_core.city.ingest --force  # force re-download
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import osmnx as ox

from atlas_core.city.categories import BUILDING_OSM_TAGS, POI_OSM_TAGS
from atlas_core.config import get_logger, get_settings
from atlas_core.config.settings import DATA_DIR, CitySettings, Settings

log = get_logger(__name__)

# Keep OSMnx's raw Overpass response cache inside the (gitignored) data dir
# rather than the current working directory.
ox.settings.use_cache = True
ox.settings.cache_folder = str(DATA_DIR / "osmnx_cache")

# Tag columns retained when caching feature tables. Anything outside this set is
# dropped so GeoParquet never chokes on OSM's occasional list-valued tags.
_KEPT_TAG_COLUMNS = [
    "name",
    "amenity",
    "shop",
    "leisure",
    "railway",
    "station",
    "aeroway",
    "office",
    "religion",
    "building",
]
_ID_COLUMN = "atlas_id"


@dataclass(frozen=True)
class CachePaths:
    """Resolved on-disk locations for a city's cached artifacts."""

    graph: Path
    buildings: Path
    pois: Path

    def all_exist(self) -> bool:
        return self.graph.exists() and self.buildings.exists() and self.pois.exists()


def cache_paths(settings: Settings) -> CachePaths:
    """Return the cache file paths for the configured city."""
    slug = settings.city.name.lower().replace(" ", "_")
    root = settings.cache_dir
    return CachePaths(
        graph=root / f"{slug}_graph.graphml",
        buildings=root / f"{slug}_buildings.parquet",
        pois=root / f"{slug}_pois.parquet",
    )


def download_graph(city: CitySettings) -> nx.MultiDiGraph:
    """Download the drivable road graph for the city bounding box.

    Edge speeds and travel times are attached so routing can weight by either
    distance (``length``) or estimated travel time (``travel_time``).
    """
    log.info("downloading road graph", bbox=city.bbox, network_type=city.network_type)
    graph = ox.graph_from_bbox(bbox=city.bbox, network_type=city.network_type)
    try:
        graph = ox.routing.add_edge_speeds(graph)
        graph = ox.routing.add_edge_travel_times(graph)
    except Exception as exc:
        log.warning("could not attach edge speeds/travel times", error=str(exc))
    log.info("road graph downloaded", nodes=graph.number_of_nodes(), edges=graph.number_of_edges())
    return graph


def download_features(city: CitySettings, tags: dict[str, Any]) -> gpd.GeoDataFrame:
    """Download OSM features matching ``tags`` within the city bounding box."""
    gdf = ox.features_from_bbox(bbox=city.bbox, tags=tags)
    return _sanitize_features(gdf)


def _sanitize_features(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Reduce an OSM feature table to a GeoParquet-safe, id-stable frame.

    Keeps the geometry and the whitelisted tag columns (as strings), and lifts a
    stable integer id (the OSM id when available) into an explicit column so it
    survives the parquet round-trip.
    """
    if gdf.empty:
        return gdf

    ids = [_osm_id(idx, pos) for pos, idx in enumerate(gdf.index)]
    keep = [c for c in _KEPT_TAG_COLUMNS if c in gdf.columns]
    out = gdf[[*keep, "geometry"]].copy()
    for col in keep:
        out[col] = out[col].astype("string")
    out = out.reset_index(drop=True)
    out[_ID_COLUMN] = ids
    return out.set_index(_ID_COLUMN)


def _osm_id(index_value: object, fallback: int) -> int:
    if isinstance(index_value, tuple):
        for part in reversed(index_value):
            if isinstance(part, int | float) and not isinstance(part, bool):
                return int(part)
    if isinstance(index_value, int | float) and not isinstance(index_value, bool):
        return int(index_value)
    return fallback


def ingest_city(settings: Settings | None = None, *, force: bool = False) -> CachePaths:
    """Download and cache the configured city, returning the cache paths.

    If the cache already exists and ``force`` is false, this is a no-op.
    """
    settings = settings or get_settings()
    paths = cache_paths(settings)

    if paths.all_exist() and not force:
        log.info("city cache present; skipping download", city=settings.city.name)
        return paths

    settings.cache_dir.mkdir(parents=True, exist_ok=True)

    graph = download_graph(settings.city)
    ox.save_graphml(graph, filepath=paths.graph)

    buildings = download_features(settings.city, BUILDING_OSM_TAGS)
    buildings.to_parquet(paths.buildings)
    log.info("cached buildings", count=len(buildings), path=str(paths.buildings))

    pois = download_features(settings.city, POI_OSM_TAGS)
    pois.to_parquet(paths.pois)
    log.info("cached pois", count=len(pois), path=str(paths.pois))

    return paths


def _main() -> None:
    parser = argparse.ArgumentParser(description="Build the Atlas OSM cache.")
    parser.add_argument("--force", action="store_true", help="Force re-download.")
    args = parser.parse_args()
    paths = ingest_city(force=args.force)
    log.info("ingest complete", graph=str(paths.graph))


if __name__ == "__main__":
    _main()
