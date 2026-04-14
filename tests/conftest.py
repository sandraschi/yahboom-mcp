"""
Pytest configuration.

Modes:
  Default / CI   : YAHBOOM_USE_MOCK_BRIDGE=1 (auto-set). Skips tests marked
                   needs_robot or e2e.
  Hardware E2E   : YAHBOOM_E2E=1  YAHBOOM_IP=<ip>  pytest tests/e2e/
"""
from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock

import pytest

os.environ.setdefault("YAHBOOM_USE_MOCK_BRIDGE", "1")

from yahboom_mcp.state import _state
from yahboom_mcp.testing.mock_bridge import MockROS2Bridge

# ── Core fixtures ────────────────────────────────────────────────────────────

@pytest.fixture
def mock_bridge() -> MockROS2Bridge:
    """Connected MockROS2Bridge in global state."""
    bridge = MockROS2Bridge(host="127.0.0.1", port=9090)
    bridge.connected = True
    bridge.cmd_vel_topic = object()
    old = _state.get("bridge")
    _state["bridge"] = bridge
    yield bridge
    _state["bridge"] = old


@pytest.fixture
def mock_ssh() -> MagicMock:
    """Mock SSH bridge. execute() returns (stdout, stderr, 0) by default."""
    m = MagicMock()
    m.connected = True
    m.execute = AsyncMock(return_value=("OK", "", 0))
    old = _state.get("ssh")
    _state["ssh"] = m
    yield m
    _state["ssh"] = old


@pytest.fixture
def disconnected_bridge() -> None:
    """No bridge — tests that expect offline behaviour."""
    old = _state.get("bridge")
    _state["bridge"] = None
    yield
    _state["bridge"] = old


@pytest.fixture
def mock_bridge_with_servo(mock_bridge) -> MockROS2Bridge:
    """MockROS2Bridge with servo history tracking (built-in to MockROS2Bridge)."""
    mock_bridge.servo_history.clear()
    return mock_bridge


# ── Marker handling ──────────────────────────────────────────────────────────

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if os.environ.get("YAHBOOM_E2E") == "1":
        return
    skip = pytest.mark.skip(reason="E2E/hardware test: set YAHBOOM_E2E=1 YAHBOOM_IP=<ip>")
    for item in items:
        if any(kw in item.keywords for kw in ("needs_robot", "e2e", "real_robot")):
            item.add_marker(skip)
