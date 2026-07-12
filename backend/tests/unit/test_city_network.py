"""Tests for the road-network routing wrapper."""

from __future__ import annotations

import networkx as nx
import pytest
from atlas_core.city.network import RoadNetwork
from atlas_core.city.types import LatLon


def test_empty_graph_rejected() -> None:
    with pytest.raises(ValueError):
        RoadNetwork(nx.MultiDiGraph())


def test_node_coords(grid_network: RoadNetwork) -> None:
    coords = grid_network.node_coords(1)
    assert coords == LatLon(lat=24.700, lon=46.600)


def test_nearest_node_snaps_to_closest(grid_network: RoadNetwork) -> None:
    # A point just past node 3's corner should snap to node 3.
    assert grid_network.nearest_node(lat=24.7099, lon=46.6099) == 3


def test_nearest_nodes_batch(grid_network: RoadNetwork) -> None:
    nodes = grid_network.nearest_nodes([LatLon(24.7001, 46.6001), LatLon(24.7099, 46.6099)])
    assert nodes == [1, 3]


def test_shortest_path_same_node_is_singleton(grid_network: RoadNetwork) -> None:
    assert grid_network.shortest_path(2, 2) == [2]


def test_shortest_path_picks_lower_weight_route(grid_network: RoadNetwork) -> None:
    # 1 -> 3: via node 2 (1000+1100=2100) vs via node 4 (1000+1000=2000).
    # The node-4 route is shorter, so it must be chosen.
    assert grid_network.shortest_path(1, 3) == [1, 4, 3]


def test_no_path_returns_empty() -> None:
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=46.6, y=24.7)
    graph.add_node(2, x=46.7, y=24.8)
    graph.add_edge(1, 2, length=100.0)  # only 1->2, so 2->1 has no path
    net = RoadNetwork(graph)
    assert net.shortest_path(2, 1) == []


def test_edge_points_follow_real_geometry(grid_network: RoadNetwork) -> None:
    # The 2->3 edge bulges east; its polyline must include the mid vertex.
    points = grid_network.edge_points(2, 3)
    assert len(points) == 3
    assert points[1] == LatLon(lat=24.705, lon=46.615)


def test_edge_points_straight_when_no_geometry(grid_network: RoadNetwork) -> None:
    points = grid_network.edge_points(1, 2)
    assert points == [LatLon(24.700, 46.600), LatLon(24.700, 46.610)]


def test_path_polyline_is_not_a_straight_line(grid_network: RoadNetwork) -> None:
    # Route 1 -> 2 -> 3 should carry the eastward bulge from the 2->3 edge,
    # proving movement follows the road, not a straight line between endpoints.
    polyline = grid_network.path_polyline([1, 2, 3])
    lons = [p.lon for p in polyline]
    assert max(lons) > 46.610  # the bulge pushes east of the node grid
    # Join vertices are de-duplicated.
    assert polyline == sorted(set(polyline), key=polyline.index)


def test_path_length_sums_edges(grid_network: RoadNetwork) -> None:
    assert grid_network.path_length([1, 2, 3]) == pytest.approx(2100.0)
