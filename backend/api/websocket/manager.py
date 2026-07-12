"""WebSocket connection manager.

Tracks connected clients and fans a single per-tick payload out to all of them,
quietly dropping any that have disconnected.
"""

from __future__ import annotations

import asyncio

from atlas_core.config import get_logger
from fastapi import WebSocket

log = get_logger(__name__)


class ConnectionManager:
    """Manages the set of live WebSocket clients."""

    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._lock = asyncio.Lock()

    @property
    def client_count(self) -> int:
        return len(self._clients)

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._clients.add(websocket)
        log.info("client connected", clients=len(self._clients))

    async def disconnect(self, websocket: WebSocket) -> None:
        async with self._lock:
            self._clients.discard(websocket)
        log.info("client disconnected", clients=len(self._clients))

    async def broadcast_json(self, payload: dict[str, object]) -> None:
        """Send ``payload`` to every client; drop those that error out."""
        async with self._lock:
            clients = list(self._clients)
        dead: list[WebSocket] = []
        for client in clients:
            try:
                await client.send_json(payload)
            except Exception:
                dead.append(client)
        if dead:
            async with self._lock:
                for client in dead:
                    self._clients.discard(client)
