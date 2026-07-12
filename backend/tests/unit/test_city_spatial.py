"""Tests for the KD-tree spatial index."""

from __future__ import annotations

from dataclasses import dataclass

from atlas_core.city.spatial import SpatialIndex
from atlas_core.city.types import LatLon


@dataclass
class Place:
    name: str
    loc: LatLon


def _places() -> list[Place]:
    return [
        Place("center", LatLon(24.7136, 46.6753)),
        Place("north", LatLon(24.7500, 46.6753)),
        Place("east", LatLon(24.7136, 46.7200)),
    ]


def test_empty_index_returns_none() -> None:
    index: SpatialIndex[Place] = SpatialIndex([], lambda p: p.loc)
    assert index.nearest(LatLon(24.7, 46.6)) is None
    assert index.k_nearest(LatLon(24.7, 46.6), 3) == []
    assert index.within_radius(LatLon(24.7, 46.6), 1000) == []


def test_nearest_returns_closest_place() -> None:
    index = SpatialIndex(_places(), lambda p: p.loc)
    nearest = index.nearest(LatLon(24.7140, 46.6760))
    assert nearest is not None
    assert nearest.name == "center"


def test_k_nearest_is_ordered() -> None:
    index = SpatialIndex(_places(), lambda p: p.loc)
    result = index.k_nearest(LatLon(24.7136, 46.6753), k=2)
    assert [p.name for p in result] == ["center", "north"]


def test_k_nearest_caps_at_size() -> None:
    index = SpatialIndex(_places(), lambda p: p.loc)
    assert len(index.k_nearest(LatLon(24.7, 46.6), k=99)) == 3


def test_within_radius_filters_by_distance() -> None:
    index = SpatialIndex(_places(), lambda p: p.loc)
    # ~1km radius around the center should include only the center place.
    close = index.within_radius(LatLon(24.7136, 46.6753), radius_m=1000)
    assert {p.name for p in close} == {"center"}
