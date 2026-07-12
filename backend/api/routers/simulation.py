"""Simulation control and state endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import ControlRequest, SimulationState
from api.service import service

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.get("/state", response_model=SimulationState)
def simulation_state() -> SimulationState:
    """Return the current run state and aggregate metrics."""
    return service.state()


@router.post("/control", response_model=SimulationState)
async def simulation_control(request: ControlRequest) -> SimulationState:
    """Play/pause, reset, change speed or weather, or trigger an event."""
    return await service.control(request)
