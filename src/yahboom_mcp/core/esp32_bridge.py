"""
ESP32 WiFi bridge: TCP client that speaks the line-based text protocol.
Same public interface as ROS2Bridge so the server can swap bridges via env.
"""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("yahboom-mcp.core.esp32_bridge")

_DEFAULT_PORT = 2323


def _parse_float(s: str, default: float = 0.0) -> float:
    try:
        return float(s.strip())
    except (ValueError, TypeError):
        return default


class ESP32Bridge:
    """
    TCP bridge to an ESP32 running the yahboom-mcp text protocol.
    Protocol: PC sends "CMD,lx,ly,az\\n"; ESP32 sends "IMU,...", "BAT,...", "ODOM,..." lines.
    """

    def __init__(self, host: str = "192.168.1.11", port: int = _DEFAULT_PORT):
        self.host = host
        self.port = port
        self.connected = False
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._read_task: Optional[asyncio.Task] = None
        self.state: Dict[str, Any] = {
            "imu": {},
            "odom": {},
            "battery": {},
            "scan": {},
            "last_update": 0.0,
        }
        self.ros = None  # No ROS; video_bridge checks this

    async def connect(self) -> bool:
        """Connect to ESP32 TCP server."""
        try:
            logger.info("Connecting to ESP32 bridge at %s:%s...", self.host, self.port)
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=10.0,
            )
            self.connected = True
            self._read_task = asyncio.create_task(self._read_loop())
            logger.info("ESP32 bridge connected")
            return True
        except asyncio.TimeoutError:
            logger.error("ESP32 connection timeout to %s:%s", self.host, self.port)
            self.connected = False
            return False
        except OSError as e:
            logger.error("ESP32 connection failed: %s", e)
            self.connected = False
            return False

    async def _read_loop(self) -> None:
        """Background task: read lines and update state."""
        if not self._reader:
            return
        buf = b""
        try:
            while self.connected and self._reader:
                try:
                    chunk = await self._reader.read(256)
                    if not chunk:
                        break
                    buf += chunk
                except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
                    break
                while b"\n" in buf or b"\r" in buf:
                    line, _, buf = buf.partition(b"\n")
                    if b"\r" in line:
                        line, _, _ = line.partition(b"\r")
                    try:
                        text = line.decode("utf-8").strip()
                    except UnicodeDecodeError:
                        continue
                    if not text:
                        continue
                    self._parse_line(text)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.debug("ESP32 read loop error: %s", e)
        finally:
            self.connected = False

    def _parse_line(self, line: str) -> None:
        """Parse one telemetry line and update state."""
        parts = line.split(",", 1)
        if len(parts) < 2:
            return
        tag, rest = parts[0].strip().upper(), parts[1]
        vals = [x.strip() for x in rest.split(",")]

        if tag == "IMU" and len(vals) >= 4:
            # IMU,heading,pitch,roll,yaw (degrees)
            self.state["imu"] = {
                "heading": _parse_float(vals[0]),
                "pitch": _parse_float(vals[1]),
                "roll": _parse_float(vals[2]),
                "yaw": _parse_float(vals[3]) if len(vals) > 3 else _parse_float(vals[0]),
                "orientation": {},
                "angular_velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
                "linear_acceleration": {"x": 0.0, "y": 0.0, "z": 0.0},
            }
        elif tag == "BAT" and len(vals) >= 1:
            # BAT,percentage,voltage
            pct = _parse_float(vals[0], -1.0)
            if pct >= 0:
                self.state["battery"] = {
                    "percentage": round(pct, 1),
                    "voltage": round(_parse_float(vals[1]), 2) if len(vals) > 1 else None,
                    "power_supply_status": None,
                }
        elif tag == "ODOM" and len(vals) >= 5:
            # ODOM,x,y,z,linear,angular
            self.state["odom"] = {
                "position": {
                    "x": _parse_float(vals[0]),
                    "y": _parse_float(vals[1]),
                    "z": _parse_float(vals[2]),
                },
                "heading": 0.0,
                "velocity": {
                    "linear": _parse_float(vals[3]),
                    "angular": _parse_float(vals[4]),
                },
            }
        self.state["last_update"] = time.monotonic()

    async def disconnect(self) -> None:
        """Close TCP connection and stop read task."""
        self.connected = False
        if self._read_task and not self._read_task.done():
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        if self._writer:
            try:
                self._writer.close()
                await asyncio.wait_for(self._writer.wait_closed(), timeout=2.0)
            except Exception:
                pass
            self._writer = None
        self._reader = None
        logger.info("ESP32 bridge disconnected")

    async def publish_velocity(
        self, linear_x: float, angular_z: float, linear_y: float = 0.0
    ) -> bool:
        """Send CMD,lx,ly,az to the ESP32."""
        if not self.connected or not self._writer:
            logger.warning("Cannot publish velocity: ESP32 not connected")
            return False
        try:
            line = f"CMD,{linear_x:.4f},{linear_y:.4f},{angular_z:.4f}\n"
            self._writer.write(line.encode("utf-8"))
            await self._writer.drain()
            logger.debug("Published CMD: x=%s y=%s z=%s", linear_x, linear_y, angular_z)
            return True
        except (ConnectionResetError, BrokenPipeError, OSError) as e:
            logger.warning("ESP32 write failed: %s", e)
            self.connected = False
            return False

    async def get_sensor_data(self, key: str) -> Dict[str, Any]:
        """Return cached sensor data by key: imu | battery | odom | scan."""
        return self.state.get(key, {})

    def get_full_telemetry(self) -> Dict[str, Any]:
        """Same shape as ROS2Bridge.get_full_telemetry for drop-in replacement."""
        imu = self.state.get("imu", {})
        battery = self.state.get("battery", {})
        odom = self.state.get("odom", {})
        scan = self.state.get("scan", {})

        vel = odom.get("velocity", {})

        return {
            "battery": battery.get("percentage"),
            "voltage": battery.get("voltage"),
            "imu": {
                "heading": imu.get("heading"),
                "yaw": imu.get("yaw"),
                "pitch": imu.get("pitch"),
                "roll": imu.get("roll"),
                "angular_velocity": imu.get("angular_velocity"),
                "linear_acceleration": imu.get("linear_acceleration"),
            },
            "velocity": {
                "linear": vel.get("linear", 0.0),
                "angular": vel.get("angular", 0.0),
            },
            "position": odom.get("position"),
            "scan": {
                "nearest_m": scan.get("nearest_m"),
                "obstacles": scan.get("obstacles"),
            },
        }
