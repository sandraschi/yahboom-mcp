#!/usr/bin/env python3
"""PTZ-sweep LiDAR scan using TFmini-S + camera pan servo.

Sweeps pan servo 0-180°, reads TFmini range at each step,
publishes LaserScan. Camera is always boresighted with laser."""
import math, serial, time, rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Range
from std_msgs.msg import Int32MultiArray
import threading


class SweepScanNode(Node):
    def __init__(self):
        super().__init__("sweep_scan")
        self.scan_pub = self.create_publisher(LaserScan, "/scan", 10)
        self.servo_pub = self.create_publisher(Int32MultiArray, "/servo", 10)

        self.pan_angle = 90
        self.tilt_angle = 90
        self.latest_range = 0.0
        self.range_lock = threading.Lock()

        self.declare_parameter("tfmini_port", "/dev/ttyUSB1")
        self.declare_parameter("sweep_min_deg", 0)
        self.declare_parameter("sweep_max_deg", 180)
        self.declare_parameter("step_deg", 5)
        self.declare_parameter("dwell_ms", 200)
        self.declare_parameter("auto_sweep", True)
        self.declare_parameter("sweep_interval_sec", 15.0)

        port = self.get_parameter("tfmini_port").value
        self.auto_sweep = self.get_parameter("auto_sweep").value
        interval = self.get_parameter("sweep_interval_sec").value

        self.tfmini = None
        try:
            self.tfmini = serial.Serial(port, 115200, timeout=0.5)
            self.get_logger().info(f"TFmini on {port}")
        except Exception as e:
            self.get_logger().error(f"TFmini: {e}")

        if self.tfmini:
            self.read_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.read_thread.start()

        if self.auto_sweep:
            self.create_timer(interval, self.sweep_once)

    def _read_loop(self):
        while rclpy.ok():
            try:
                raw = self.tfmini.read(9)
                if len(raw) == 9 and raw[0] == 0x59 and raw[1] == 0x59:
                    dist = raw[2] | (raw[3] << 8)
                    strength = raw[4] | (raw[5] << 8)
                    if strength < 65535:
                        with self.range_lock:
                            self.latest_range = dist / 100.0
            except Exception:
                pass
            time.sleep(0.01)

    def _set_servo(self, pan: int, tilt: int):
        msg = Int32MultiArray(data=[1, pan, 2, tilt])
        self.servo_pub.publish(msg)

    def sweep_once(self):
        min_d = self.get_parameter("sweep_min_deg").value
        max_d = self.get_parameter("sweep_max_deg").value
        step = self.get_parameter("step_deg").value
        dwell = self.get_parameter("dwell_ms").value / 1000.0

        angles = list(range(min_d, max_d + 1, step))
        if angles[-1] != max_d:
            angles.append(max_d)

        ranges = []
        for angle in angles:
            self._set_servo(angle, self.tilt_angle)
            time.sleep(dwell)
            with self.range_lock:
                ranges.append(self.latest_range)

        now = self.get_clock().now()
        scan = LaserScan()
        scan.header.stamp = now.to_msg()
        scan.header.frame_id = "laser"
        scan.angle_min = math.radians(min_d)
        scan.angle_max = math.radians(max_d)
        scan.angle_increment = math.radians(step)
        scan.time_increment = dwell
        scan.range_min = 0.1
        scan.range_max = 12.0
        scan.ranges = ranges
        self.scan_pub.publish(scan)
        self.get_logger().info(f"Sweep done: {len(ranges)} pts")


def main():
    rclpy.init()
    rclpy.spin(SweepScanNode())


if __name__ == "__main__":
    main()
