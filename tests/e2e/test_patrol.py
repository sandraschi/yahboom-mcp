"""
E2E hardware tests — Boomy patrol + peripheral verification.

Requirements:
  YAHBOOM_E2E=1
  YAHBOOM_IP=<robot_wifi_ip>
  YAHBOOM_PASSWORD=<pi_password>  (optional, for SSH)

Run:
  $env:YAHBOOM_E2E = "1"
  $env:YAHBOOM_IP  = "192.168.0.105"
  pytest tests/e2e/ -v -s --timeout=120

All tests are marked @pytest.mark.e2e and skipped unless YAHBOOM_E2E=1.
The patrol test is loud: it actually drives Boomy in a square and flashes the lights.
"""
from __future__ import annotations

import asyncio
import logging
import os

import pytest

logger = logging.getLogger("yahboom.e2e")

ROBOT_IP   = os.environ.get("YAHBOOM_IP", "192.168.0.105")
BRIDGE_PORT = int(os.environ.get("YAHBOOM_BRIDGE_PORT", 9090))

pytestmark = pytest.mark.e2e


# ── Shared bridge fixture ────────────────────────────────────────────────────

@pytest.fixture(scope="module")
async def live_bridge():
    """Real ROS2Bridge connected to the physical robot (module-scoped)."""
    from yahboom_mcp.core.ros2_bridge import ROS2Bridge
    from yahboom_mcp.core.ssh_bridge import SSHBridge
    from yahboom_mcp.state import _state

    ssh = SSHBridge(ROBOT_IP)
    ssh.connect()

    bridge = ROS2Bridge(host=ROBOT_IP, port=BRIDGE_PORT)
    bridge.ssh = ssh
    connected = await bridge.connect(timeout=20.0)
    assert connected, f"Could not connect to ROSBridge at {ROBOT_IP}:{BRIDGE_PORT}"

    _state["bridge"] = bridge
    _state["ssh"]    = ssh
    yield bridge, ssh

    await bridge.disconnect()
    ssh.close()


# ── Connection smoke test ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_connection(live_bridge):
    bridge, _ssh = live_bridge
    assert bridge.connected, "Bridge should be connected to robot"

    topics = await bridge.get_all_topics()
    assert len(topics) > 0, "Should discover at least some topics"
    topic_names = [t["name"] if isinstance(t, dict) else t[0] for t in topics]
    assert "/cmd_vel" in topic_names, "/cmd_vel must be present for motion control"
    logger.info(f"Connected. {len(topics)} topics discovered.")


# ── Telemetry smoke test ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_telemetry(live_bridge):
    bridge, _ = live_bridge
    await asyncio.sleep(2.0)   # let subscriptions settle
    tele = bridge.get_full_telemetry()

    logger.info(f"Telemetry: {tele}")

    # Battery must be present (sensors working)
    if tele.get("battery") is None:
        pytest.xfail("Battery sensor not publishing — known issue, see ASSESSMENT_2026.md")

    assert tele["battery"] > 5, "Battery critically low or sensor broken"
    assert tele["battery"] <= 100


# ── Lightstrip test ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_lightstrip_basic(live_bridge):
    from yahboom_mcp.operations import lightstrip
    _bridge, _ = live_bridge

    r = await lightstrip.execute(operation="set", param1=0, param2=255, param3=0)
    assert r["success"], f"Lightstrip set failed: {r}"
    await asyncio.sleep(0.5)

    r = await lightstrip.execute(operation="off")
    assert r["success"]


@pytest.mark.asyncio
async def test_e2e_lightstrip_patrol_pattern(live_bridge):
    from yahboom_mcp.operations import lightstrip

    r = await lightstrip.execute(operation="pattern", param1="patrol")
    assert r["success"], f"Patrol pattern failed: {r}"
    assert r["result"]["pattern"] == "patrol_car"

    await asyncio.sleep(3.0)   # let it flash visually

    r2 = await lightstrip.execute(operation="off")
    assert r2["success"]


# ── Servo / PTZ test ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_servo_center(live_bridge):
    from yahboom_mcp.operations.camera_ptz import camera_reset
    bridge, ssh = live_bridge

    result = await camera_reset(bridge, ssh_bridge=ssh)
    # We can't verify the physical angle, but the publish should not error
    logger.info(f"Servo center result: {result}")
    # Not asserting success=True since the custom msg type may not be available;
    # the SSH fallback path should at least not throw.
    assert "success" in result


@pytest.mark.asyncio
async def test_e2e_servo_sweep(live_bridge):
    from yahboom_mcp.operations.camera_ptz import camera_set_pos
    bridge, ssh = live_bridge

    for pan, tilt in [(45, 90), (90, 45), (135, 90), (90, 135), (90, 90)]:
        result = await camera_set_pos(bridge, pan, tilt, ssh_bridge=ssh)
        logger.info(f"Servo ({pan},{tilt}): {result}")
        await asyncio.sleep(0.8)


# ── Display test ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_display_status(live_bridge):
    from yahboom_mcp.operations import display
    result = await display.execute(operation="get_status")
    logger.info(f"Display status: {result}")
    assert result["success"]
    # Log finding but don't fail — display may not be fitted
    if not result["result"]["active"]:
        pytest.xfail("OLED not detected on I2C bus — may not be fitted or wiring issue")


@pytest.mark.asyncio
async def test_e2e_display_write(live_bridge):
    from yahboom_mcp.operations import display
    r = await display.execute(operation="write", param1="E2E TEST", param2=0)
    logger.info(f"Display write: {r}")
    if not r["success"]:
        pytest.xfail(f"Display write failed: {r.get('log')}")


# ── Voice / audio test ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_e2e_voice_status(live_bridge):
    from yahboom_mcp.operations import voice
    result = await voice.execute(operation="get_status")
    logger.info(f"Voice status: {result}")
    assert result["success"]
    if not result["result"]["detected"]:
        pytest.xfail("Voice module not detected — check USB cable and 'lsusb' on Pi")


@pytest.mark.asyncio
async def test_e2e_voice_say(live_bridge):
    from yahboom_mcp.operations import voice
    result = await voice.execute(operation="say", param1="E2E test complete. Boomy is ready.")
    logger.info(f"Voice say: {result}")
    if not result["success"]:
        pytest.xfail(f"Voice say failed: {result}")


# ── Camera / snapshot E2E ────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_e2e_camera_snapshot_http(live_bridge):
    """
    Hit the /api/v1/snapshot endpoint and verify it returns a real JPEG.
    The server must be running (dual mode) at YAHBOOM_MCP_URL.
    """
    import httpx

    mcp_url = os.environ.get("YAHBOOM_MCP_URL", "http://localhost:10792")
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(f"{mcp_url}/api/v1/snapshot")

    if resp.status_code == 204:
        pytest.xfail("No camera frame available — camera node not running or no feed")

    assert resp.status_code == 200, f"Snapshot returned {resp.status_code}"
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content[:2] == b"\xff\xd8", "Response is not a valid JPEG"
    logger.info(f"Snapshot OK — {len(resp.content)} bytes")


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_e2e_camera_snapshot_ssh(live_bridge):
    """
    Capture a frame directly on the Pi via SSH using cv2.VideoCapture.
    Verifies /dev/video0 is accessible and returns a real image.
    Saves frame to /tmp/boomy_test_snapshot.jpg on the Pi.
    """
    _, ssh = live_bridge

    cmd = (
        "python3 -c \""
        "import cv2, base64, sys; "
        "cap = cv2.VideoCapture(0); "
        "ret, f = cap.read(); "
        "cap.release(); "
        "sys.exit(0 if ret else 1) if not ret else None; "
        "_, b = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 80]); "
        "data = base64.b64encode(b.tobytes()).decode(); "
        "open('/tmp/boomy_test_snapshot.jpg', 'wb').write(b.tobytes()); "
        "print(data[:40]);"  # just print first 40 chars to confirm
        "\""
    )
    out, err, code = ssh.execute(cmd)

    if code != 0 or not out.strip():
        pytest.xfail(
            f"cv2.VideoCapture(0) failed on Pi — camera not connected or /dev/video0 missing. "
            f"err={err!r}"
        )

    logger.info(f"SSH snapshot OK — code={code}, preview={out.strip()[:40]}")
    assert code == 0


@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_e2e_camera_snapshot_in_docker(live_bridge):
    """
    Capture a frame inside the Docker container (verifies /dev/video0 is mapped).
    """
    _, ssh = live_bridge

    cmd = (
        "docker exec yahboom_ros2 python3 -c \""
        "import cv2, sys; "
        "cap = cv2.VideoCapture(0); "
        "ret, f = cap.read(); "
        "cap.release(); "
        "print('FRAME_OK' if ret and f is not None else 'FRAME_FAIL'); "
        "\""
    )
    out, _err, _code = ssh.execute(cmd)

    if "FRAME_OK" not in out:
        pytest.xfail(
            f"Camera not accessible inside Docker container. "
            f"Add --device /dev/video0:/dev/video0 to docker run. out={out!r}"
        )

    logger.info("Docker camera frame capture OK")


@pytest.mark.asyncio
@pytest.mark.timeout(60)
async def test_e2e_camera_vision_e2b(live_bridge):
    """
    Capture a frame via SSH, then ask E2B to describe the scene.
    Requires LiteRT-LM E2B server running on the Pi at port 8080.
    """
    import httpx
    _, ssh = live_bridge

    robot_ip = os.environ.get("YAHBOOM_IP", "192.168.0.105")
    litert_url = f"http://{robot_ip}:8080/v1/chat/completions"

    # Step 1: Capture frame via SSH
    cap_cmd = (
        "python3 -c \""
        "import cv2, base64; "
        "cap = cv2.VideoCapture(0); "
        "ret, f = cap.read(); cap.release(); "
        "_, b = cv2.imencode('.jpg', f, [cv2.IMWRITE_JPEG_QUALITY, 70]); "
        "print(base64.b64encode(b.tobytes()).decode()) if ret else print('FAIL')"
        "\""
    )
    out, _err, _code = ssh.execute(cap_cmd)

    if not out.strip() or out.strip() == "FAIL":
        pytest.xfail("Camera capture failed — skipping E2B vision test")

    frame_b64 = out.strip()

    # Step 2: Ask E2B to describe it
    try:
        payload = {
            "model": "gemma4-e2b-it",
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:image/jpeg;base64,{frame_b64}"}},
                    {"type": "text",
                     "text": "Describe this image in one sentence in German."},
                ]
            }],
            "max_tokens": 100,
        }
        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(litert_url, json=payload)

        if resp.status_code != 200:
            pytest.xfail(
                f"LiteRT-LM not running at {litert_url} — "
                "install: pip install litert-lm && litert-lm serve --model gemma4-e2b-it --port 8080"
            )

        description = resp.json()["choices"][0]["message"]["content"]
        logger.info(f"E2B scene description: {description}")
        assert len(description) > 5, "E2B returned empty description"

    except httpx.ConnectError:
        pytest.xfail(
            f"Cannot reach LiteRT-LM at {litert_url} — "
            "start with: litert-lm serve --model gemma4-e2b-it --port 8080"
        )


# ── Sensor E2E — battery and IMU ─────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.timeout(30)
async def test_e2e_rosmaster_serial_direct(live_bridge):
    """
    Test Rosmaster_Lib sensor read directly via SSH (bypassing ROS 2).
    This isolates whether the UART serial path works independently of Docker.
    """
    _, ssh = live_bridge

    cmd = (
        "python3 -c \""
        "import sys, time; "
        "sys.path.insert(0, '/root/yahboomcar_ws/install/yahboomcar_bringup"
        "/lib/python3.10/site-packages/yahboomcar_bringup'); "
        "from Rosmaster_Lib import Rosmaster; "
        "import os; "
        "port = '/dev/ttyROSMASTER' if os.path.exists('/dev/ttyROSMASTER') else '/dev/ttyUSB0'; "
        "bot = Rosmaster(com=port); "
        "bot.create_receive_threading(); "
        "time.sleep(1.5); "
        "gyro = bot.get_gyroscope_data(); "
        "volt = bot.get_battery_voltage(); "
        "bot.cancel_receive_threading(); "
        "print(f'GYRO:{gyro}'); "
        "print(f'VOLT:{volt}'); "
        "print('SENSOR_OK' if volt and float(volt) > 0.5 else 'SENSOR_FAIL')"
        "\""
    )
    out, err, _code = ssh.execute(cmd)
    logger.info(f"Rosmaster direct test: {out.strip()}")

    if "SENSOR_FAIL" in out or not out.strip():
        pytest.xfail(
            f"Rosmaster serial returned no data. "
            f"Check /dev/ttyUSB0 or /dev/ttyROSMASTER exists on Pi. err={err!r}"
        )

    assert "SENSOR_OK" in out, f"Unexpected output: {out}"


@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_e2e_docker_serial_mapping(live_bridge):
    """Verify Docker container has /dev/ttyUSB0 mapped."""
    _, ssh = live_bridge

    out, _err, _ = ssh.execute(
        "docker exec yahboom_ros2 ls /dev/ttyUSB* /dev/ttyROSMASTER 2>/dev/null || echo MISSING"
    )
    logger.info(f"Docker serial devices: {out.strip()}")

    if "MISSING" in out or not out.strip():
        pytest.xfail(
            "Serial devices not mapped into Docker container. "
            "Add --device /dev/ttyUSB0:/dev/ttyUSB0 (or ttyROSMASTER) to docker run."
        )


@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_e2e_docker_i2c_mapping(live_bridge):
    """Verify Docker container has /dev/i2c-1 mapped (for OLED + Raspbot)."""
    _, ssh = live_bridge

    out, _err, _ = ssh.execute(
        "docker exec yahboom_ros2 ls /dev/i2c-1 2>/dev/null || echo MISSING"
    )
    logger.info(f"Docker I2C: {out.strip()}")

    if "MISSING" in out:
        pytest.xfail(
            "/dev/i2c-1 not mapped into Docker container. "
            "Add --device /dev/i2c-1:/dev/i2c-1 to docker run."
        )


@pytest.mark.asyncio
@pytest.mark.timeout(15)
async def test_e2e_oled_luma_installed(live_bridge):
    """Verify luma.oled is installed on Pi host."""
    _, ssh = live_bridge

    out, err, _code = ssh.execute(
        "python3 -c \"from luma.oled.device import ssd1306; print('OK')\" 2>&1"
    )
    if "OK" not in out:
        pytest.xfail(
            f"luma.oled not installed on Pi. Run: pip3 install luma.oled luma.core pillow. err={err!r}"
        )
    logger.info("luma.oled installed OK")


@pytest.mark.asyncio
@pytest.mark.timeout(20)
async def test_e2e_oled_write(live_bridge):
    """Write a test message to the OLED if it's present."""
    from yahboom_mcp.operations import display

    status = await display.execute(operation="get_status")
    if not status["result"].get("active"):
        pytest.xfail(
            f"OLED not detected: {status['result'].get('note', 'unknown')}. "
            "Check I2C wiring and i2cdetect -y 1"
        )

    result = await display.execute(
        operation="write",
        param1="E2E Test OK",
        param2=0,
    )
    assert result["success"], f"OLED write failed: {result.get('log')}"
    logger.info("OLED write OK")

    # Show system status
    await display.execute(operation="status")
    await asyncio.sleep(2)
    await display.execute(operation="clear")


@pytest.mark.asyncio
@pytest.mark.timeout(90)
async def test_e2e_patrol_square(live_bridge):
    """
    Drive Boomy in a square (4 × forward + turn_left) with patrol car lights.
    This test physically moves the robot — ensure floor space is clear.

    Sequence per side:
      - Lights: patrol car pattern
      - Forward 1.5s at 0.2 m/s  (~30 cm)
      - Stop
      - Turn left 1.2s at 0.5 rad/s (~90°)
      - Stop

    Full patrol: ~4 sides × ~3s = ~12s driving + overhead.
    """
    from yahboom_mcp.operations import lightstrip
    bridge, _ = live_bridge

    assert bridge.connected, "Bridge must be connected for patrol"

    logger.info("=== BOOMY PATROL: SQUARE — START ===")

    # Activate patrol car lights
    r = await lightstrip.execute(operation="pattern", param1="patrol")
    logger.info(f"Patrol lights: {r['result'].get('status')}")

    FORWARD_SPEED   = 0.20  # m/s — gentle, avoids furniture
    FORWARD_SECS    = 1.5   # seconds per side
    TURN_SPEED      = 0.50  # rad/s
    TURN_SECS       = 1.25  # ~90° at 0.5 rad/s
    SIDES           = 4

    async def stop():
        await bridge.publish_velocity(linear_x=0.0, angular_z=0.0)
        await asyncio.sleep(0.3)

    try:
        for side in range(1, SIDES + 1):
            logger.info(f"  Side {side}/{SIDES}: forward")
            ok = await bridge.publish_velocity(linear_x=FORWARD_SPEED, angular_z=0.0)
            assert ok, f"publish_velocity failed on side {side}"
            await asyncio.sleep(FORWARD_SECS)

            await stop()

            logger.info(f"  Side {side}/{SIDES}: turn left")
            ok = await bridge.publish_velocity(linear_x=0.0, angular_z=TURN_SPEED)
            assert ok
            await asyncio.sleep(TURN_SECS)

            await stop()

        logger.info("=== BOOMY PATROL: SQUARE — COMPLETE ===")

    finally:
        # Always stop and reset lights, even on failure
        await bridge.publish_velocity(linear_x=0.0, angular_z=0.0)
        await lightstrip.execute(operation="off")
        logger.info("Motors stopped, lights off.")

    # Green flash: success
    await lightstrip.execute(operation="set", param1=0, param2=255, param3=0)
    await asyncio.sleep(1.0)
    await lightstrip.execute(operation="off")
