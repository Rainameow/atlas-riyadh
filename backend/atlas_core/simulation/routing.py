"""Movement along the real road network.

The :class:`MovementController` assigns each citizen a shortest-path route over
the OSM road graph and advances them along the route's true polyline geometry
each tick. Position is interpolated by cumulative distance, so agents follow the
actual curve of the road — never a straight line between endpoints.
"""

from __future__ import annotations

import math
from itertools import pairwise

from atlas_core.city.network import RoadNetwork
from atlas_core.city.types import LatLon
from atlas_core.simulation.agents.citizen import Citizen
from atlas_core.simulation.types import Destination

_M_PER_DEG_LAT = 111_320.0


def _distance_m(a: LatLon, b: LatLon) -> float:
    """Planar (equirectangular) distance in metres — accurate at city scale."""
    mean_lat = math.radians((a.lat + b.lat) / 2.0)
    dx = (b.lon - a.lon) * _M_PER_DEG_LAT * math.cos(mean_lat)
    dy = (b.lat - a.lat) * _M_PER_DEG_LAT
    return math.hypot(dx, dy)


def _cumulative(polyline: list[LatLon]) -> list[float]:
    """Cumulative distance (metres) at each polyline vertex; first entry is 0."""
    cumulative = [0.0]
    for a, b in pairwise(polyline):
        cumulative.append(cumulative[-1] + _distance_m(a, b))
    return cumulative


class MovementController:
    """Assigns routes and advances citizens along them."""

    def __init__(self, network: RoadNetwork) -> None:
        self._network = network

    def assign_route(self, citizen: Citizen, destination: Destination) -> None:
        """Plan a route from the citizen's current node to ``destination``.

        Trivial cases (already at the node, or no path exists) snap the citizen
        straight to the destination so no agent gets stuck.
        """
        citizen.destination = destination
        path = self._network.shortest_path(citizen.current_node, destination.node)

        if len(path) <= 1:
            self._arrive(citizen, destination)
            return

        polyline = self._network.path_polyline(path)
        if len(polyline) < 2:
            self._arrive(citizen, destination)
            return

        citizen.route = path
        citizen.route_polyline = polyline
        citizen.route_cumulative_m = _cumulative(polyline)
        citizen.route_cursor_m = 0.0
        citizen.position = polyline[0]

    def advance(self, citizen: Citizen, distance_m: float) -> bool:
        """Advance a traveling citizen by ``distance_m``.

        Returns ``True`` if the citizen arrived at their destination this tick.
        """
        if not citizen.route or citizen.destination is None:
            return False

        citizen.route_cursor_m += max(0.0, distance_m)
        if citizen.route_cursor_m >= citizen.route_length_m:
            self._arrive(citizen, citizen.destination)
            return True

        citizen.position = self._interpolate(citizen)
        return False

    def _interpolate(self, citizen: Citizen) -> LatLon:
        """Interpolate the citizen's position along the route polyline."""
        cursor = citizen.route_cursor_m
        cumulative = citizen.route_cumulative_m
        polyline = citizen.route_polyline

        # Find the segment [i, i+1] containing the cursor distance.
        i = _segment_index(cumulative, cursor)
        seg_start, seg_end = cumulative[i], cumulative[i + 1]
        span = seg_end - seg_start
        t = 0.0 if span <= 0 else (cursor - seg_start) / span
        a, b = polyline[i], polyline[i + 1]
        return LatLon(lat=a.lat + (b.lat - a.lat) * t, lon=a.lon + (b.lon - a.lon) * t)

    def _arrive(self, citizen: Citizen, destination: Destination) -> None:
        citizen.position = destination.location
        citizen.current_node = destination.node
        citizen.clear_route()


def _segment_index(cumulative: list[float], cursor: float) -> int:
    """Return index ``i`` such that ``cumulative[i] <= cursor < cumulative[i+1]``."""
    # Linear scan is fine: route polylines are short relative to tick cost.
    for i in range(len(cumulative) - 1):
        if cursor < cumulative[i + 1]:
            return i
    return max(0, len(cumulative) - 2)
