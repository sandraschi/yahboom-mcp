# Copyright 2026 Yahboom MCP — MIT
"""HTTP GET dreame-mcp /api/v1/map JSON, convert base64 PNG to nav_msgs/OccupancyGrid for Nav2.

Requires dreame-mcp to return a rendered ``image`` (base64 PNG). The Dreame map frame is
*not* aligned with the Raspbot: set ``map_origin`` / use Nav2/TF to fuse when Boomy
gets its own LiDAR (e.g. MS200) for localization.
"""
from __future__ import annotations

import base64
import json
import math
import urllib.error
import urllib.request
from typing import Any

import rclpy
from geometry_msgs.msg import Point, Pose, Quaternion, TransformStamped
from nav_msgs.msg import MapMetaData, OccupancyGrid
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Header
import tf2_ros

try:
    from PIL import Image
    import io

    _HAS_PIL = True
except Exception:
    _HAS_PIL = False

_DEFAULT_URL = "http://127.0.0.1:10894/api/v1/map"


def _png_to_occupancy(
    png_bytes: bytes,
    free_pixel_min: int,
    occupied_pixel_max: int,
    flip_y: bool,
) -> tuple[list[int], int, int]:
    """Map image luminance to OccupancyGrid values (0=free, 100=occ, -1=unknown)."""
    if not _HAS_PIL:
        raise RuntimeError("python3-pil (Pillow) is required: sudo apt install python3-pil")
    im = Image.open(io.BytesIO(png_bytes)).convert("L")
    w, h = im.size
    px = list(im.getdata())
    y_iter = range(h - 1, -1, -1) if flip_y else range(h)
    out: list[int] = []
    for y in y_iter:
        for x in range(w):
            v = int(px[y * w + x])
            out.append(_pixel_to_cost(v, free_pixel_min, occupied_pixel_max))
    return out, w, h


def _pixel_to_cost(v: int, free_min: int, occ_max: int) -> int:
    if v >= free_min:
        return 0
    if v <= occ_max:
        return 100
    return -1


def _fetch_map_json(url: str, timeout_sec: float) -> dict[str, Any]:
    """GET JSON from dreame-mcp (or compatible) /api/v1/map."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        body = resp.read()
    return json.loads(body.decode("utf-8", errors="replace"))


def _euler_to_quat(roll: float, pitch: float, yaw: float) -> tuple[float, float, float, float]:
    """Roll/pitch/yaw in radians to quaternion (x, y, z, w)."""
    cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return (x, y, z, w)


class DreameMapPublisherNode(Node):
    def __init__(self) -> None:
        super().__init__("dreame_map_publisher")
        if not _HAS_PIL:
            self.get_logger().error(
                "Pillow (python3-pil) not importable. Install: sudo apt install python3-pil"
            )
        p = self.declare_parameter
        self._dreame_url = p("dreame_map_url", _DEFAULT_URL)
        self._http_timeout = p("http_timeout_sec", 25.0)
        self._period = p("update_period_sec", 0.0)
        self._map_frame = p("map_frame", "map")
        self._map_topic = p("map_topic", "/dreame_floorplan")
        self._resolution = p("map_resolution", 0.05)
        self._origin_x = p("map_origin_x", 0.0)
        self._origin_y = p("map_origin_y", 0.0)
        self._origin_z = p("map_origin_z", 0.0)
        self._origin_yaw = p("map_origin_yaw_deg", 0.0)
        self._free_min = p("image_free_pixel_gte", 200)
        self._occ_max = p("image_occupied_pixel_lte", 50)
        self._flip_y = p("flip_image_y", True)
        self._pub_tf = p("publish_map_to_odom_tf", False)
        self._odom_frame = p("odom_frame", "odom")
        # Static identity map→odom so rviz/Nav2 can show something before AMCL; turn off
        # when a real localizer provides map→odom.
        map_qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self._pub = self.create_publisher(OccupancyGrid, self._map_topic.value, map_qos)
        self._tf_broadcaster: tf2_ros.StaticTransformBroadcaster | None = None
        if self._pub_tf.value:
            self._tf_broadcaster = tf2_ros.StaticTransformBroadcaster(self)
        if self._period.value and float(self._period.value) > 0.0:
            t = max(2.0, float(self._period.value))
            self.create_timer(t, self._on_timer)
        # First fetch shortly after start
        self._startup = self.create_timer(0.5, self._on_startup_once)
        self.get_logger().info(
            "Dreame map bridge: url=%s topic=%s frame=%s"
            % (
                self._dreame_url.value,
                self._map_topic.value,
                self._map_frame.value,
            )
        )

    def _on_startup_once(self) -> None:
        self._startup.cancel()
        self._publish_once()

    def _on_timer(self) -> None:
        if not self._period.value or float(self._period.value) <= 0.0:
            return
        self._publish_once()

    def _publish_once(self) -> None:
        if not _HAS_PIL:
            return
        try:
            data = _fetch_map_json(
                str(self._dreame_url.value), float(self._http_timeout.value)
            )
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as e:
            self.get_logger().warning("Dreame map fetch failed: %s" % e)
            return
        if data.get("success") is False and not data.get("raw_b64"):
            err = data.get("error", data.get("detail", "unknown"))
            self.get_logger().warning("Dreame map not successful: %s" % err)
            return
        if "detail" in data and "image" not in data and "raw_b64" not in data:
            self.get_logger().warning("Dreame HTTP error detail: %s" % data.get("detail", data))
            return
        b64 = data.get("image")
        if not b64 or not isinstance(b64, str):
            self.get_logger().warning(
                "No base64 'image' in response — dreame-mcp must decode+render the map. "
                "Relying on 'image' for Nav2; raw_b64-only is not supported in this bridge."
            )
            return
        try:
            png = base64.b64decode(b64, validate=False)
        except Exception as e:
            self.get_logger().warning("image base64 decode failed: %s" % e)
            return
        if len(png) < 8 or png[:4] != b"\x89PNG":
            self.get_logger().warning("image field is not a PNG; skip")
            return
        try:
            gte = int(self._free_min.value)
            lte = int(self._occ_max.value)
            occ_data, w, h = _png_to_occupancy(
                png, gte, lte, bool(self._flip_y.value)
            )
        except Exception as e:
            self.get_logger().error("PNG to occupancy failed: %s" % e)
            return
        res = float(self._resolution.value)
        ox = float(self._origin_x.value)
        oy = float(self._origin_y.value)
        oz = float(self._origin_z.value)
        yaw = math.radians(float(self._origin_yaw.value))
        when = self.get_clock().now()
        st = when.to_msg()
        xq, yq, zq, wq = _euler_to_quat(0.0, 0.0, yaw)
        m = MapMetaData(
            map_load_time=st,
            resolution=res,
            width=w,
            height=h,
            origin=Pose(
                position=Point(x=ox, y=oy, z=oz),
                orientation=Quaternion(x=xq, y=yq, z=zq, w=wq),
            ),
        )
        hmsg = Header(stamp=st, frame_id=str(self._map_frame.value))
        grid = OccupancyGrid(
            header=hmsg,
            info=m,
            data=occ_data,
        )
        self._pub.publish(grid)
        self.get_logger().info("Published %s (%dx%d cells)" % (self._map_topic.value, w, h))
        if self._pub_tf and self._tf_broadcaster:
            tf = TransformStamped()
            tf.header.stamp = hmsg.stamp
            tf.header.frame_id = str(self._map_frame.value)
            tf.child_frame_id = str(self._odom_frame.value)
            tf.transform.translation.x = 0.0
            tf.transform.translation.y = 0.0
            tf.transform.translation.z = 0.0
            tf.transform.rotation.x = 0.0
            tf.transform.rotation.y = 0.0
            tf.transform.rotation.z = 0.0
            tf.transform.rotation.w = 1.0
            # StaticTransformBroadcaster expects a list
            self._tf_broadcaster.sendTransform([tf])
            self.get_logger().info(
                "Static TF: %s -> %s (identity). Disable publish_map_to_odom_tf if AMCL provides this."
                % (self._map_frame.value, self._odom_frame.value)
            )


def main() -> None:
    rclpy.init()
    node = DreameMapPublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
