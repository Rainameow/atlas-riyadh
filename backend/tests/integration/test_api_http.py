"""End-to-end HTTP/WebSocket tests booting the full app (loads real OSM cache).

Marked ``slow`` because the app lifespan loads the real Riyadh city. Enable with
``pytest --run-slow``.
"""

from __future__ import annotations

import pytest
from api.main import app
from fastapi.testclient import TestClient


@pytest.mark.slow
@pytest.mark.integration
def test_health_and_summary_and_stream() -> None:
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        summary = client.get("/api/city/summary")
        assert summary.status_code == 200
        assert summary.json()["nodes"] > 100

        # The WebSocket should deliver an initial tick payload on connect.
        with client.websocket_connect("/ws/stream") as ws:
            message = ws.receive_json()
            assert message["type"] == "tick"
            assert len(message["citizens"]) > 0
