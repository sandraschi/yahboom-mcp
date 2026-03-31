"""
Pytest configuration: default to mock bridge so importing `yahboom_mcp.server` is safe in CI.

- Normal / CI: YAHBOOM_USE_MOCK_BRIDGE=1 (set here unless YAHBOOM_E2E=1).
- Hardware smoke tests: set YAHBOOM_E2E=1 and run only `tests/hardware/` (no mock).
"""

from __future__ import annotations

import os

# Must run before any test module imports `yahboom_mcp.server`.
# Always default to mock so CI and local pytest never open a real roslibpy connection.
os.environ.setdefault("YAHBOOM_USE_MOCK_BRIDGE", "1")

import pytest

from yahboom_mcp.state import _state
from yahboom_mcp.testing.mock_bridge import MockROS2Bridge


@pytest.fixture
def mock_bridge() -> MockROS2Bridge:
    """Inject a connected MockROS2Bridge into global state for tool tests."""
    bridge = MockROS2Bridge(host="127.0.0.1", port=9090)
    bridge.connected = True
    bridge.cmd_vel_topic = object()

    old = _state.get("bridge")
    _state["bridge"] = bridge
    yield bridge
    _state["bridge"] = old


@pytest.fixture
def clear_bridge() -> None:
    """Ensure no bridge for tests that expect disconnected behaviour."""
    old = _state.get("bridge")
    _state["bridge"] = None
    yield
    _state["bridge"] = old


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """
    Split logic:
    - Default/CI: Skip tests marked with 'needs_robot' unless YAHBOOM_E2E=1.
    """
    if os.environ.get("YAHBOOM_E2E") == "1":
        return
        
    skip_robot = pytest.mark.skip(
        reason="Robot Hardware test: Set YAHBOOM_E2E=1 and YAHBOOM_IP=<ip> to run."
    )
    for item in items:
        if "needs_robot" in item.keywords or "real_robot" in item.keywords:
            item.add_marker(skip_robot)
