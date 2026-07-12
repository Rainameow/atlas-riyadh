"""Atlas FastAPI application.

Wires the simulation service into an HTTP + WebSocket API:
  * REST under ``/api`` for city data and simulation control.
  * A WebSocket at ``/ws/stream`` that pushes every simulated tick to clients.

Run with::

    uvicorn api.main:app --reload
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from atlas_core.config import configure_logging, get_logger
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from api.routers import city, simulation
from api.schemas import HealthResponse
from api.service import service

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    await service.startup()
    try:
        yield
    finally:
        await service.shutdown()


app = FastAPI(
    title="Atlas API",
    version="0.1.0",
    description="Live digital-twin simulation of Riyadh.",
    lifespan=lifespan,
)

# Permissive CORS for local development (Vite dev server on :5173).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(city.router)
app.include_router(simulation.router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
def health() -> HealthResponse:
    return HealthResponse(city=service.world.city.name)


@app.websocket("/ws/stream")
async def stream(websocket: WebSocket) -> None:
    """Stream per-tick simulation state to a connected client."""
    await service.manager.connect(websocket)
    try:
        # Send the current state immediately so a new client isn't blank until
        # the next tick.
        await websocket.send_json(service.tick_payload())
        while True:
            # We don't expect inbound messages; this keeps the socket open and
            # detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        await service.manager.disconnect(websocket)
    except Exception:
        await service.manager.disconnect(websocket)
