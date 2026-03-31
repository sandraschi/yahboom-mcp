"""
FastAPI routes with a mocked ROS bridge (YAHBOOM_USE_MOCK_BRIDGE set in tests/conftest.py).

Imports the app after env is configured; lifespan runs once per TestClient session.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from yahboom_mcp.server import app


@pytest.mark.integration
@pytest.mark.mock
@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def test_health_reports_connected(client: TestClient) -> None:
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["connected"] is True


def test_telemetry_live_source(client: TestClient) -> None:
    r = client.get("/api/v1/telemetry")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "live"
    assert body["battery"] == 88.0


def test_control_move_publishes(client: TestClient) -> None:
    r = client.post(
        "/api/v1/control/move",
        params={"linear": 0.1, "angular": 0.0, "linear_y": 0.0},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("status") == "success"


def test_sensors_endpoint_live(client: TestClient) -> None:
    r = client.get("/api/v1/sensors")
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "live"
