"""Road-network wrapper around an OSM-derived NetworkX graph.

:class:`RoadNetwork` is the routing substrate for the whole simulation. It wraps
a ``networkx`` graph whose nodes carry ``x`` (longitude) and ``y`` (latitude)
attributes and whose edges carry a ``length`` (metres) and an optional
``geometry`` (a Shapely ``LineString`` capturing the road's real curvature).

It deliberately depends only on ``networkx`` + ``scipy`` — not on OSMnx — so it
can be unit-tested against a hand-built synthetic grid without any network
access, while still consuming the real graph produced by the ingest pipeline.
"""

from __future__ import annotations

import math
from itertools import pairwise
from typing import TYPE_CHECKING, Any

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree

from atlas_core.city.types import LatLon

if TYPE_CHECKING:
    from shapely.geometry import LineString

# Metres per degree of latitude (mean). Longitude is scaled by cos(latitude).
_M_PER_DEG_LAT = 111_320.0


class RoadNetwork:
    """A queryable view over the city road graph.

    Args:
        graph: A ``networkx`` (Multi)DiGraph with ``x``/``y`` node attributes and
            ``length`` edge attributes. OSMnx produces exactly this shape.
    """

    def __init__(self, graph: nx.MultiDiGraph) -> None:
        if graph.number_of_nodes() == 0:
            raise ValueError("road graph has no nodes")
        self._graph = graph
        self._nodes: list[int] = list(graph.nodes)
        self._node_index: dict[int, int] = {n: i for i, n in enumerate(self._nodes)}

        lats = np.fromiter((graph.nodes[n]["y"] for n in self._nodes), dtype=float)
        lons = np.fromiter((graph.nodes[n]["x"] for n in self._nodes), dtype=float)
        self._lats = lats
        self._lons = lons

        # Build a KD-tree in a local equirectangular projection (metres) so
        # nearest-node queries are accurate within a city footprint.
        self._lat0 = float(lats.mean())
        self._cos_lat0 = math.cos(math.radians(self._lat0))
        xy = np.column_stack(
            (
                lons * _M_PER_DEG_LAT * self._cos_lat0,
                lats * _M_PER_DEG_LAT,
            )
        )
        self._kdtree = cKDTree(xy)

    # -- Basic accessors -----------------------------------------------------

    @property
    def graph(self) -> nx.MultiDiGraph:
        return self._graph

    def __len__(self) -> int:
        return len(self._nodes)

    @property
    def node_ids(self) -> list[int]:
        return self._nodes

    def node_coords(self, node: int) -> LatLon:
        """Return the ``LatLon`` of a graph node."""
        data = self._graph.nodes[node]
        return LatLon(lat=float(data["y"]), lon=float(data["x"]))

    # -- Spatial queries -----------------------------------------------------

    def nearest_node(self, lat: float, lon: float) -> int:
        """Return the id of the graph node closest to ``(lat, lon)``."""
        x = lon * _M_PER_DEG_LAT * self._cos_lat0
        y = lat * _M_PER_DEG_LAT
        _, idx = self._kdtree.query([x, y])
        return self._nodes[int(idx)]

    def nearest_nodes(self, coords: list[LatLon]) -> list[int]:
        """Vectorized nearest-node lookup for many coordinates at once."""
        if not coords:
            return []
        pts = np.array(
            [[c.lon * _M_PER_DEG_LAT * self._cos_lat0, c.lat * _M_PER_DEG_LAT] for c in coords]
        )
        _, idxs = self._kdtree.query(pts)
        return [self._nodes[int(i)] for i in np.atleast_1d(idxs)]

    # -- Routing -------------------------------------------------------------

    def shortest_path(self, origin: int, destination: int, weight: str = "length") -> list[int]:
        """Return the node sequence of the shortest path, or ``[]`` if none.

        Uses Dijkstra over the requested edge weight (``length`` in metres by
        default; ``travel_time`` once edge speeds are attached). Returns a
        single-node list when origin and destination coincide.
        """
        if origin == destination:
            return [origin]
        try:
            path: list[int] = nx.shortest_path(self._graph, origin, destination, weight=weight)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []
        return path

    def _best_edge_data(self, u: int, v: int, weight: str) -> dict[str, Any]:
        """Return the data dict of the lowest-``weight`` parallel edge u->v."""
        edges = self._graph.get_edge_data(u, v)
        if not edges:
            raise KeyError(f"no edge {u} -> {v}")
        return min(edges.values(), key=lambda d: d.get(weight, d.get("length", 1.0)))

    def edge_points(self, u: int, v: int, weight: str = "length") -> list[LatLon]:
        """Return the polyline of the edge ``u -> v`` as ordered coordinates.

        If the edge carries a real ``geometry`` (curved road), its vertices are
        returned so movement follows the true road shape. Otherwise the straight
        segment between the two node coordinates is returned.
        """
        data = self._best_edge_data(u, v, weight)
        geom: LineString | None = data.get("geometry")
        if geom is not None:
            # LineString coords are (x=lon, y=lat) pairs.
            return [LatLon(lat=y, lon=x) for x, y in geom.coords]
        return [self.node_coords(u), self.node_coords(v)]

    def edge_length(self, u: int, v: int) -> float:
        """Return the length in metres of the shortest parallel edge u->v."""
        return float(self._best_edge_data(u, v, "length").get("length", 0.0))

    def path_polyline(self, nodes: list[int], weight: str = "length") -> list[LatLon]:
        """Concatenate edge geometries along ``nodes`` into one polyline.

        Duplicate join vertices between consecutive edges are removed so the
        result is a clean, ordered coordinate list suitable for interpolation.
        """
        if len(nodes) == 1:
            return [self.node_coords(nodes[0])]
        polyline: list[LatLon] = []
        for u, v in pairwise(nodes):
            pts = self.edge_points(u, v, weight)
            if polyline and pts and polyline[-1] == pts[0]:
                pts = pts[1:]
            polyline.extend(pts)
        return polyline

    def path_length(self, nodes: list[int]) -> float:
        """Return the total length in metres of a node path."""
        return sum(self.edge_length(u, v) for u, v in pairwise(nodes))
