"""City data endpoints: summary and map reference layers."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import CitySummary, PoiFeature
from api.service import service

router = APIRouter(prefix="/api/city", tags=["city"])


@router.get("/summary", response_model=CitySummary)
def city_summary() -> CitySummary:
    """Return counts and category breakdown for the loaded city."""
    return service.city_summary()


@router.get("/pois", response_model=list[PoiFeature])
def city_pois() -> list[PoiFeature]:
    """Return points of interest for the map's static reference layers."""
    return service.map_pois()
