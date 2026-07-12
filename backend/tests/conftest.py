"""Shared pytest fixtures and configuration for the Atlas test suite."""

from __future__ import annotations

import networkx as nx
import pytest
from atlas_core.city.categories import BuildingCategory, PoiCategory
from atlas_core.city.model import CityModel
from atlas_core.city.network import RoadNetwork
from atlas_core.city.types import Building, LatLon, Poi
from atlas_core.config.settings import Settings, get_settings
from atlas_core.simulation.agents.citizen import Citizen
from atlas_core.simulation.types import Destination, Occupation, TransportMode
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


@pytest.fixture
def sample_city(grid_network: RoadNetwork) -> CityModel:
    """A tiny but complete city: the grid network plus buildings and POIs.

    Every POI category the behaviour layer needs is present and pinned to a real
    grid node, so the simulation can run end-to-end without any OSM download.
    """

    def coords(node: int):
        return grid_network.node_coords(node)

    buildings = [
        Building(1, BuildingCategory.RESIDENTIAL, coords(1), 1, 200.0, "Home North"),
        Building(2, BuildingCategory.RESIDENTIAL, coords(4), 4, 180.0, "Home South"),
        Building(3, BuildingCategory.OFFICE, coords(3), 3, 500.0, "Tower"),
    ]
    pois = [
        Poi(10, PoiCategory.MOSQUE, coords(2), 2, "Grand Mosque"),
        Poi(11, PoiCategory.MALL, coords(4), 4, "Riyadh Mall"),
        Poi(12, PoiCategory.PARK, coords(1), 1, "City Park"),
        Poi(13, PoiCategory.GYM, coords(2), 2, "Fit Gym"),
        Poi(14, PoiCategory.RESTAURANT, coords(3), 3, "Najd Kitchen"),
        Poi(15, PoiCategory.CAFE, coords(4), 4, "Corner Cafe"),
        Poi(16, PoiCategory.HOSPITAL, coords(1), 1, "Central Hospital"),
        Poi(17, PoiCategory.UNIVERSITY, coords(3), 3, "KSU"),
        Poi(18, PoiCategory.SCHOOL, coords(2), 2, "Al Noor School"),
    ]
    return CityModel(name="TestCity", network=grid_network, buildings=buildings, pois=pois)


@pytest.fixture
def make_citizen():
    """Return a builder for a single citizen with sensible defaults."""

    def _build(
        *,
        occupation: Occupation = Occupation.OFFICE_WORKER,
        prayer_propensity: float = 0.9,
        has_workplace: bool = True,
        transport: TransportMode = TransportMode.CAR,
    ) -> Citizen:
        home = Destination(LatLon(24.700, 46.600), node=1, label="home")
        workplace = (
            Destination(LatLon(24.710, 46.610), node=3, label="work") if has_workplace else None
        )
        return Citizen(
            id=0,
            age=30,
            occupation=occupation,
            home=home,
            workplace=workplace,
            preferred_transport=transport,
            position=home.location,
            current_node=1,
            prayer_propensity=prayer_propensity,
        )

    return _build
