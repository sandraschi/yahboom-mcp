import pytest
import asyncio
from yahboom_mcp.state import _state

# Markers are handled by conftest.py (default to skip unless YAHBOOM_E2E=1)
pytestmark = pytest.mark.needs_robot


@pytest.mark.asyncio
async def test_bridge_connectivity():
    """Verify that we have a real ROS 2 bridge and it identifies as connected."""
    bridge = _state.get("bridge")
    assert bridge is not None, "ROS 2 Bridge not initialized in server state"
    assert bridge.connected is True, (
        "ROS 2 Bridge failed to connect to robot (Check IP/Port)"
    )


@pytest.mark.asyncio
async def test_sensors_no_mock():
    """Verify that sensor data is either Live or returns an Offline Error, but NEVER mock 85%."""
    from yahboom_mcp.operations import sensors

    # Force a 'read_all' operation
    result = await sensors.execute(operation="read_all")

    assert result["success"] is True
    # If the bridge is connected, results must match real robot state, not hardcoded mock defaults.
    # In Pure Reality mode, if it's mock it will return an 'offline' status.
    assert result["status"] != "mock_data", (
        "FATAL: Sensors module is still returning 'Mock Central' data!"
    )

    data = result.get("result")
    if result["status"] == "live_data":
        # Check that we have a real float value, even if 0.0, but typically not exactly 11.8 or 85.0 always.
        assert data.get("battery") is not None
        assert data.get("voltage") is not None
    else:
        # If offline, should have no data
        assert data.get("data") is None


@pytest.mark.asyncio
async def test_display_closed_loop():
    """Verify OLED display command and I2C acknowledgment."""
    from yahboom_mcp.operations import display

    # Send a unique heartbeat string
    heartbeat = f"REALITY_{int(asyncio.get_event_loop().time())}"
    result = await display.execute(operation="write", param1=heartbeat, param2=0)

    assert result["success"] is True
    assert result["status"] == "applied", (
        f"OLED Verification failed: {result.get('log')}"
    )


@pytest.mark.asyncio
async def test_lightstrip_latching():
    """Verify Lightstrip command is accepted and published."""
    from yahboom_mcp.operations import lightstrip

    # Set to a verifiable color
    result = await lightstrip.execute(operation="set", param1=255, param2=0, param3=0)

    assert result["success"] is True
    assert result["result"]["status"] == "published"


@pytest.mark.asyncio
async def test_camera_frame_received():
    """Verify that VideoBridge is actually receiving frames from ROS 2."""
    video = _state.get("video_bridge")
    assert video is not None, "VideoBridge not initialized"
    assert video.active is True, "VideoBridge is not active"

    # Wait a moment for a frame to arrive (Auto-Discovery takes a moment)
    await asyncio.sleep(2.0)
    assert video.frame_count > 0, (
        "VideoBridge is active but 0 frames received (Check Topic/Auto-Discovery)"
    )
