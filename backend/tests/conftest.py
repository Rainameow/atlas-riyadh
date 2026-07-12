"""Shared pytest fixtures and configuration for the Atlas test suite."""

from __future__ import annotations

import networkx as nx
import pytest
from atlas_core.city.network import RoadNetwork
from atlas_core.config.settings import Settings, get_settings
from shapely.geometry import LineString


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="Run tests marked 'slow' (e.g. live OSM downloads).",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="needs --run-slow (network / heavy download)")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def settings() -> Settings:
    """Return the process settings singleton (fresh cache per session)."""
    get_settings.cache_clear()
    return get_settings()


@pytest.fixture
def grid_graph() -> nx.MultiDiGraph:
    """A tiny 4-node square road graph near central Riyadh.

    Node ids 1..4 form a unit square. Edges are bidirectional. The 2<->3 edge
    carries a curved ``geometry`` (an eastward bulge) so tests can assert that
    movement follows real road shape rather than a straight segment.
    """
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = "EPSG:4326"
    coords = {
        1: (46.600, 24.700),
        2: (46.610, 24.700),
        3: (46.610, 24.710),
        4: (46.600, 24.710),
    }
    for node, (x, y) in coords.items():
        graph.add_node(node, x=x, y=y)

    bulge = LineString([(46.610, 24.700), (46.615, 24.705), (46.610, 24.710)])
    edges = [
        (1, 2, 1000.0, None),
        (2, 3, 1100.0, bulge),
        (3, 4, 1000.0, None),
        (4, 1, 1000.0, None),
    ]
    for u, v, length, geom in edges:
        attrs = {"length": length, "travel_time": length / 13.9}
        if geom is not None:
            attrs["geometry"] = geom
        graph.add_edge(u, v, **attrs)
        graph.add_edge(v, u, **attrs)
    return graph


@pytest.fixture
def grid_network(grid_graph: nx.MultiDiGraph) -> RoadNetwork:
    """A :class:`RoadNetwork` over the synthetic grid graph."""
    return RoadNetwork(grid_graph)
