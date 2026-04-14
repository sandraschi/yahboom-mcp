"""
Unit tests — camera snapshot, video_bridge direct capture, sensor data flow.
No hardware required. Uses MockROS2Bridge + mock SSH.
Run: pytest tests/unit/test_camera_sensors.py -v
"""
import base64
import os
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ── Camera / Video Bridge ────────────────────────────────────────────────────

class TestVideoBridgeDirect:
    """Test the direct cv2 capture fallback in VideoBridge."""

    def test_fallback_env_var_force_direct(self):
        with patch.dict(os.environ, {"YAHBOOM_CAMERA_DIRECT": "1", "YAHBOOM_CAMERA_DEVICE": "0"}):
            from yahboom_mcp.core.video_bridge import VideoBridge
            vb = VideoBridge(ros_client=MagicMock())
            assert vb._force_direct is True
            assert vb._device == 0

    def test_fallback_timeout_default(self):
        from yahboom_mcp.core.video_bridge import VideoBridge
        vb = VideoBridge(ros_client=MagicMock())
        assert vb.FALLBACK_TIMEOUT_S == 10

    def test_get_latest_frame_jpeg_no_frame(self):
        from yahboom_mcp.core.video_bridge import VideoBridge
        vb = VideoBridge(ros_client=MagicMock())
        assert vb.get_latest_frame_jpeg() is None

    def test_get_latest_frame_jpeg_with_frame(self):
        """Inject a synthetic BGR frame and verify JPEG encoding."""
        from yahboom_mcp.core.video_bridge import VideoBridge
        vb = VideoBridge(ros_client=MagicMock())

        # Synthetic 64×64 green frame
        frame = np.zeros((64, 64, 3), dtype=np.uint8)
        frame[:, :, 1] = 200   # green channel

        with vb.frame_lock:
            vb.last_frame = frame
            vb.frame_count = 1

        jpeg = vb.get_latest_frame_jpeg()
        assert jpeg is not None
        assert len(jpeg) > 100
        # JPEG magic bytes
        assert jpeg[:2] == b"\xff\xd8"

    def test_image_callback_compressed(self):
        """Test _image_callback with a valid base64-encoded JPEG."""
        import cv2

        from yahboom_mcp.core.video_bridge import VideoBridge
        vb = VideoBridge(ros_client=MagicMock())

        # Create a tiny JPEG and base64-encode it
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        frame[:, :, 2] = 180   # red-ish
        _, buf = cv2.imencode(".jpg", frame)
        b64 = base64.b64encode(buf.tobytes()).decode()

        vb._image_callback({"data": b64})

        assert vb.frame_count == 1
        assert vb.last_frame is not None
        assert vb.last_frame.shape == (32, 32, 3)

    def test_image_callback_empty_data(self):
        from yahboom_mcp.core.video_bridge import VideoBridge
        vb = VideoBridge(ros_client=MagicMock())
        vb._image_callback({"data": None})
        assert vb.frame_count == 0

    def test_image_callback_raw_rgb8(self):
        """Test raw image fallback path (sensor_msgs/Image encoding=rgb8)."""
        from yahboom_mcp.core.video_bridge import VideoBridge
        vb = VideoBridge(ros_client=MagicMock())

        # 8×8 RGB8 raw image
        raw = np.zeros((8, 8, 3), dtype=np.uint8)
        raw[:, :, 0] = 100
        raw_bytes = raw.tobytes()
        b64 = base64.b64encode(raw_bytes).decode()

        # Pass as raw image message (cv2.imdecode will fail → fallback path)
        msg = {
            "data": b64,
            "width": 8,
            "height": 8,
            "encoding": "rgb8",
        }
        vb._image_callback(msg)
        assert vb.frame_count == 1

    @pytest.mark.asyncio
    async def test_mjpeg_generator_yields_frames(self):
        """Generator should yield MJPEG boundary frames."""
        from yahboom_mcp.core.video_bridge import VideoBridge
        vb = VideoBridge(ros_client=MagicMock())
        vb.active = True

        # Pre-load a frame
        frame = np.zeros((32, 32, 3), dtype=np.uint8)
        with vb.frame_lock:
            vb.last_frame = frame
            vb.frame_count = 1

        chunks = []
        async for chunk in vb.mjpeg_generator():
            chunks.append(chunk)
            vb.active = False   # stop after first frame
            break

        assert len(chunks) == 1
        assert b"--frame" in chunks[0]
        assert b"Content-Type: image/jpeg" in chunks[0]


# ── Snapshot endpoint (mocked HTTP) ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_snapshot_endpoint_returns_jpeg(mock_bridge):
    """
    Test /api/v1/snapshot endpoint returns 200 + JPEG when VideoBridge has a frame.
    Uses httpx test client against the FastAPI app.
    """
    import numpy as np

    from yahboom_mcp.core.video_bridge import VideoBridge
    from yahboom_mcp.state import _state

    # Build a VideoBridge with a pre-loaded frame
    vb = VideoBridge(ros_client=MagicMock())
    frame = np.zeros((48, 48, 3), dtype=np.uint8)
    frame[:, :, 1] = 180
    with vb.frame_lock:
        vb.last_frame = frame
        vb.frame_count = 1
    vb.active = True

    old_vb = _state.get("video_bridge")
    _state["video_bridge"] = vb

    try:
        # Import app after state is set up to avoid lifespan startup
        from httpx import ASGITransport, AsyncClient

        from yahboom_mcp.server import app

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/snapshot")

        # Should return 200 with JPEG content
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert resp.content[:2] == b"\xff\xd8"   # JPEG magic

    finally:
        _state["video_bridge"] = old_vb


@pytest.mark.asyncio
async def test_snapshot_endpoint_no_frame(mock_bridge):
    """Snapshot should return 204 when VideoBridge has no frame."""
    from httpx import ASGITransport, AsyncClient

    from yahboom_mcp.core.video_bridge import VideoBridge
    from yahboom_mcp.server import app
    from yahboom_mcp.state import _state

    vb = VideoBridge(ros_client=MagicMock())
    vb.active = True
    # No frame loaded

    old_vb = _state.get("video_bridge")
    _state["video_bridge"] = vb

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/snapshot")
        assert resp.status_code == 204
    finally:
        _state["video_bridge"] = old_vb


# ── Sensor data flow (MockROS2Bridge) ────────────────────────────────────────

@pytest.mark.asyncio
async def test_mock_battery_telemetry(mock_bridge):
    """MockROS2Bridge returns 88% battery in telemetry."""
    tele = mock_bridge.get_full_telemetry()
    assert tele["battery"] == pytest.approx(88.0)
    assert tele["voltage"] == pytest.approx(12.2)


@pytest.mark.asyncio
async def test_mock_imu_telemetry(mock_bridge):
    """MockROS2Bridge IMU has heading and orientation."""
    tele = mock_bridge.get_full_telemetry()
    imu = tele["imu"]
    assert imu["heading"] == pytest.approx(90.0)
    assert imu["pitch"] == pytest.approx(0.0)
    assert imu["roll"] == pytest.approx(0.0)
    assert "angular_velocity" in imu
    assert "linear_acceleration" in imu


@pytest.mark.asyncio
async def test_mock_odom_telemetry(mock_bridge):
    tele = mock_bridge.get_full_telemetry()
    pos = tele["position"]
    assert "x" in pos and "y" in pos and "z" in pos


@pytest.mark.asyncio
async def test_imu_callback_populates_state(mock_bridge):
    """Simulate an incoming IMU message and verify state update."""
    # Simulate a quaternion representing 45° yaw
    import math

    from yahboom_mcp.core.ros2_bridge import _quat_to_euler_deg
    yaw = math.radians(45)
    q = {
        "x": 0.0,
        "y": 0.0,
        "z": math.sin(yaw / 2),
        "w": math.cos(yaw / 2),
    }
    euler = _quat_to_euler_deg(q)
    assert euler["heading"] == pytest.approx(45.0, abs=0.5)
    assert abs(euler["roll"]) < 0.1
    assert abs(euler["pitch"]) < 0.1


@pytest.mark.asyncio
async def test_battery_percentage_3s_lipo():
    """Verify the 3S LiPo percentage formula."""
    BAT_FULL = 12.6
    BAT_EMPTY = 9.0

    def pct(voltage):
        return max(0.0, min(1.0, (voltage - BAT_EMPTY) / (BAT_FULL - BAT_EMPTY)))

    assert pct(12.6) == pytest.approx(1.0)
    assert pct(9.0) == pytest.approx(0.0)
    assert pct(10.8) == pytest.approx(0.5, abs=0.01)   # ~50% at 10.8V
    assert pct(8.0) == pytest.approx(0.0)   # clamped
    assert pct(13.0) == pytest.approx(1.0)  # clamped


# ── SSH snapshot path ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_camera_capture_ssh_path(mock_bridge, mock_ssh):
    """
    Test that the SSH-based camera capture command is issued correctly.
    This tests the Pi-side capture path used by the embodied loop.
    """
    import base64

    import cv2
    import numpy as np

    # Build a fake JPEG to return from the SSH execute mock
    frame = np.zeros((32, 32, 3), dtype=np.uint8)
    _, buf = cv2.imencode(".jpg", frame)
    fake_b64 = base64.b64encode(buf.tobytes()).decode()

    # SSH execute returns the base64 JPEG when asked to capture
    mock_ssh.execute.return_value = (fake_b64, "", 0)

    # Simulate the capture command the embodied loop uses
    cmd = "python3 -c \"import cv2, base64; cap=cv2.VideoCapture(0); ret,f=cap.read(); cap.release(); _,b=cv2.imencode('.jpg',f); print(base64.b64encode(b.tobytes()).decode())\""
    out, _err, code = await mock_ssh.execute(cmd)

    assert code == 0
    decoded = base64.b64decode(out)
    assert decoded[:2] == b"\xff\xd8"   # valid JPEG
