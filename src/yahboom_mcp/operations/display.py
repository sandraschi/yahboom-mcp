import logging
import os
import time

from fastmcp import Context

logger = logging.getLogger("yahboom-mcp.operations.display")

# Common OLED I2C addresses on the Raspbot v2
_OLED_ADDRS = ["0x3c", "0x3d"]


def _build_luma_script(
    driver: str, address: str, width: int, height: int, body: str
) -> str:
    """Generate a self-contained Python script for luma-based display ops."""
    return f"""
import sys
try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import {driver}
    from PIL import ImageFont

    serial = i2c(port=1, address={address})
    device = {driver}(serial, width={width}, height={height})
    font = ImageFont.load_default()

    {body}
    print("VERIFIED")
except Exception as e:
    print(f"ERROR: {{e}}", file=sys.stderr)
    sys.exit(1)
"""


def _python3_c_command(script_quoted: str) -> str:
    """Run python3 -c on the Pi; optional YAHBOOM_DISPLAY_CMD_PREFIX (e.g. docker exec name)."""
    prefix = os.environ.get("YAHBOOM_DISPLAY_CMD_PREFIX", "").strip()
    if prefix:
        return f"{prefix} python3 -c {script_quoted}"
    return f"python3 -c {script_quoted}"


def _nohup_python3_scroll(script_quoted: str) -> str:
    """Background scroll loop; same prefix semantics as _python3_c_command."""
    prefix = os.environ.get("YAHBOOM_DISPLAY_CMD_PREFIX", "").strip()
    if prefix:
        return f"nohup {prefix} python3 -c {script_quoted} >/dev/null 2>&1 &"
    return f"nohup python3 -c {script_quoted} >/dev/null 2>&1 &"


def _display_err_with_hint(err: str) -> str:
    """Append Pi-side install hint when remote Python lacks luma."""
    if not err:
        return err
    e = err.strip()
    if "luma" in e.lower() or "No module named" in e:
        return e + " — On the Pi: pip3 install luma.oled luma.core pillow"
    return e


async def _maybe_pause_ros_oled(ssh) -> None:
    """Stop the stock oled_node so luma can own the I2C display (default on). Set YAHBOOM_OLED_PAUSE_ROS=0 to skip."""
    flag = os.environ.get("YAHBOOM_OLED_PAUSE_ROS", "1").strip().lower()
    if flag in ("0", "false", "no", "off"):
        return
    await ssh.execute(
        "pkill -f '[y]ahboomcar_apriltag.*oled' 2>/dev/null || "
        "pkill -f '[o]led_node' 2>/dev/null || true"
    )


async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    OLED display operations via SSH.

    Operations:
      write       → Write text line (param1=text, param2=line_num 0-3)
      clear       → Blank the display
      status      → Write IP+CPU+RAM to display (quick system status)
      get_status  → Probe I2C bus, return detected addresses and driver
      scroll      → Background scrolling marquee (param1=text)

    Driver auto-detected from I2C probe (ssd1306 default).
    Override with payload={"driver": "sh1106", "address": "0x3d"}.
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Display: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state
    ssh = _state.get("ssh")

    if not ssh or not ssh.connected:
        return {
            "success": False,
            "operation": operation,
            "error": "SSH bridge not connected — display unreachable",
            "status": "offline",
            "correlation_id": correlation_id,
        }

    driver  = (payload or {}).get("driver", "ssd1306")
    address = (payload or {}).get("address", "0x3c")
    width   = int((payload or {}).get("width",  128))
    height  = int((payload or {}).get("height",  64))

    result: dict = {}

    # ── get_status: probe I2C bus ────────────────────────────────────────────
    if operation == "get_status":
        i2c_out, _, _ = await ssh.execute("i2cdetect -y 1 2>/dev/null || echo 'i2c_error'")
        detected = [a.replace("0x", "") for a in _OLED_ADDRS if a.replace("0x", "") in i2c_out]
        active = len(detected) > 0

        # Quick luma ping if addresses found
        driver_ok = False
        if active:
            probe_addr = f"0x{detected[0]}"
            probe_script = _build_luma_script(
                driver, probe_addr, width, height,
                "with canvas(device) as draw: draw.text((0,0), 'OK', fill='white', font=font)"
            )
            out, _, _code = await ssh.execute(
                _python3_c_command(__import__("shlex").quote(probe_script))
            )
            driver_ok = "VERIFIED" in out

        result = {
            "success": True,
            "active": active,
            "detected_addresses": detected,
            "driver_responding": driver_ok,
            "driver": driver,
            "note": (
                "Display found and responding" if driver_ok
                else ("Display found at I2C but driver not responding — check luma.oled install" if active
                      else "No OLED detected on I2C bus 1 — check wiring and address (0x3c/0x3d)")
            ),
        }

    # ── clear ────────────────────────────────────────────────────────────────
    elif operation == "clear":
        # Kill any running scroll loop
        await ssh.execute("pkill -f 'display_scroll_loop' 2>/dev/null || true")
        await _maybe_pause_ros_oled(ssh)
        body = "with canvas(device) as draw: pass  # blank frame"
        script = _build_luma_script(driver, address, width, height, body)
        out, err, _ = await ssh.execute(
            _python3_c_command(__import__("shlex").quote(script))
        )
        ok = "VERIFIED" in out
        result = {
            "success": ok,
            "status": "cleared" if ok else "failed",
            "log": _display_err_with_hint(err) if not ok else "",
        }

    # ── write ────────────────────────────────────────────────────────────────
    elif operation == "write":
        await _maybe_pause_ros_oled(ssh)
        text = str(param1) if param1 is not None else ""
        line = int(param2) if param2 is not None else 0
        y    = line * 14   # ~14px per line at default font
        # Escape braces and quotes for embedding in the script body
        safe_text = text.replace("\\", "\\\\").replace('"', '\\"').replace("'", "\\'")
        body = f'with canvas(device) as draw: draw.text((0, {y}), "{safe_text}", fill="white", font=font)'
        script = _build_luma_script(driver, address, width, height, body)
        out, err, _ = await ssh.execute(
            _python3_c_command(__import__("shlex").quote(script))
        )
        ok = "VERIFIED" in out
        result = {
            "success": ok,
            "status": "written" if ok else "failed",
            "text": text,
            "line": line,
            "log": _display_err_with_hint(err) if not ok else "",
        }

    # ── status dashboard ─────────────────────────────────────────────────────
    elif operation == "status":
        await _maybe_pause_ros_oled(ssh)
        body = """
import psutil, subprocess
cpu  = psutil.cpu_percent(interval=0.2)
ram  = psutil.virtual_memory().percent
try:
    temp = float(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1000
except Exception:
    temp = 0.0
try:
    ip = subprocess.check_output(['hostname', '-I'], text=True).split()[0]
except Exception:
    ip = '?.?.?.?'

with canvas(device) as draw:
    draw.text((0,  0), f"IP: {ip}",       fill='white', font=font)
    draw.text((0, 14), f"CPU: {cpu:.0f}%", fill='white', font=font)
    draw.text((0, 28), f"RAM: {ram:.0f}%", fill='white', font=font)
    draw.text((0, 42), f"TEMP: {temp:.1f}C", fill='white', font=font)
"""
        script = _build_luma_script(driver, address, width, height, body)
        out, err, _ = await ssh.execute(
            _python3_c_command(__import__("shlex").quote(script))
        )
        ok = "VERIFIED" in out
        result = {
            "success": ok,
            "status": "displayed" if ok else "failed",
            "log": _display_err_with_hint(err) if not ok else "",
        }

    # ── scroll (background marquee) ──────────────────────────────────────────
    elif operation == "scroll":
        await _maybe_pause_ros_oled(ssh)
        text = str(param1) if param1 else "BOOMY PATROL ACTIVE"
        safe_text = text.replace("'", "\\'")
        # Kill previous scroll
        await ssh.execute("pkill -f 'display_scroll_loop' 2>/dev/null || true")
        import shlex
        scroll_script = f"""
# display_scroll_loop
import time, sys
try:
    from luma.core.interface.serial import i2c
    from luma.core.render import canvas
    from luma.oled.device import {driver}
    from PIL import ImageFont, ImageDraw, Image

    serial = i2c(port=1, address={address})
    device = {driver}(serial, width={width}, height={height})
    font = ImageFont.load_default()
    text = '{safe_text}'
    x = {width}
    while True:
        with canvas(device) as draw:
            draw.text((x, 25), text, fill='white', font=font)
        x -= 3
        if x < -len(text) * 6:
            x = {width}
        time.sleep(0.04)
except Exception as e:
    print(f'SCROLL ERROR: {{e}}', file=sys.stderr)
"""
        await ssh.execute(_nohup_python3_scroll(shlex.quote(scroll_script)))
        result = {"success": True, "status": "scrolling", "text": text}

    else:
        result = {"success": False, "error": f"Unknown display operation: {operation}"}

    return {
        "success": result.get("success", False),
        "operation": operation,
        "status": result.get("status", "unknown"),
        "log": result.get("log", ""),
        "result": result,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
