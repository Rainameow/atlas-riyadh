"""Spatial index for fast nearest-place queries.

The simulation constantly asks "where is the nearest mosque / mall / park to
this agent?". :class:`SpatialIndex` answers those queries in log time using a
KD-tree over a local equirectangular projection, which is accurate at city
scale and far cheaper than repeated great-circle scans.
"""

from __future__ import annotations

import math
from collections.abc import Callable

import numpy as np
from scipy.spatial import cKDTree

from atlas_core.city.types import LatLon

_M_PER_DEG_LAT = 111_320.0


class SpatialIndex[T]:
    """A KD-tree index mapping points to arbitrary payload items.

    Args:
        items: The payload objects to index.
        locate: Callable extracting a :class:`LatLon` from a payload item.
    """

    def __init__(self, items: list[T], locate: Callable[[T], LatLon]) -> None:
        self._items = items
        if not items:
            self._kdtree: cKDTree | None = None
            self._cos_lat0 = 1.0
            return
        coords = [locate(item) for item in items]
        self._lat0 = float(np.mean([c.lat for c in coords]))
        self._cos_lat0 = math.cos(math.radians(self._lat0))
        xy = np.array([[self._project_x(c.lon), self._project_y(c.lat)] for c in coords])
        self._kdtree = cKDTree(xy)

    def _project_x(self, lon: float) -> float:
        return lon * _M_PER_DEG_LAT * self._cos_lat0

    def _project_y(self, lat: float) -> float:
        return lat * _M_PER_DEG_LAT

    def __len__(self) -> int:
        return len(self._items)

    def nearest(self, location: LatLon) -> T | None:
        """Return the single closest item, or ``None`` if the index is empty."""
        if self._kdtree is None:
            return None
        _, idx = self._kdtree.query([self._project_x(location.lon), self._project_y(location.lat)])
        return self._items[int(idx)]

    def k_nearest(self, location: LatLon, k: int) -> list[T]:
        """Return up to ``k`` closest items, nearest first."""
        if self._kdtree is None or k <= 0:
            return []
        k = min(k, len(self._items))
        _, idxs = self._kdtree.query(
            [self._project_x(location.lon), self._project_y(location.lat)], k=k
        )
        return [self._items[int(i)] for i in np.atleast_1d(idxs)]

    def within_radius(self, location: LatLon, radius_m: float) -> list[T]:
        """Return all items within ``radius_m`` metres of ``location``."""
        if self._kdtree is None:
            return []
        idxs = self._kdtree.query_ball_point(
            [self._project_x(location.lon), self._project_y(location.lat)], r=radius_m
        )
        return [self._items[int(i)] for i in idxs]
