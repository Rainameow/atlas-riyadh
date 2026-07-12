"""Tests for movement along the real road network."""

from __future__ import annotations

import networkx as nx
from atlas_core.city.network import RoadNetwork
from atlas_core.simulation.routing import MovementController
from atlas_core.simulation.types import Destination


def test_assign_route_builds_polyline(grid_network, make_citizen) -> None:
    controller = MovementController(grid_network)
    citizen = make_citizen()  # starts at node 1
    dest = Destination(grid_network.node_coords(3), node=3, label="work")

    controller.assign_route(citizen, dest)

    assert citizen.route == [1, 4, 3]  # shortest path avoids the longer 1-2-3
    assert len(citizen.route_polyline) >= 3
    assert citizen.route_length_m > 0
    assert citizen.is_traveling


def test_advance_moves_along_route_then_arrives(grid_network, make_citizen) -> None:
    controller = MovementController(grid_network)
    citizen = make_citizen()
    dest = Destination(grid_network.node_coords(3), node=3, label="work")
    controller.assign_route(citizen, dest)

    start = citizen.position
    arrived = controller.advance(citizen, 50.0)  # small step
    assert not arrived
    assert citizen.position != start  # moved along the road

    arrived = controller.advance(citizen, 10_000.0)  # overshoot -> arrive
    assert arrived
    assert citizen.current_node == 3
    assert citizen.position == dest.location
    assert not citizen.is_traveling


def test_same_node_destination_snaps_without_route(grid_network, make_citizen) -> None:
    controller = MovementController(grid_network)
    citizen = make_citizen()  # at node 1
    dest = Destination(grid_network.node_coords(1), node=1, label="home")
    controller.assign_route(citizen, dest)
    assert citizen.route == []
    assert not citizen.is_traveling
    assert citizen.current_node == 1


def test_unreachable_destination_snaps(make_citizen) -> None:
    graph = nx.MultiDiGraph()
    graph.add_node(1, x=46.60, y=24.70)
    graph.add_node(2, x=46.70, y=24.80)
    graph.add_edge(1, 2, length=100.0)  # only 1->2; 2 is a sink
    network = RoadNetwork(graph)
    controller = MovementController(network)

    citizen = make_citizen()
    citizen.current_node = 2  # no path from 2 to 1
    dest = Destination(network.node_coords(1), node=1, label="home")
    controller.assign_route(citizen, dest)

    assert not citizen.is_traveling
    assert citizen.current_node == 1  # snapped to destination
