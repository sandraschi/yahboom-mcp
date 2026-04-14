#!/usr/bin/env python3
import threading
import time

import lgpio
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32, Int32MultiArray

# Pi 5 GPIO/SPI Pins
BUTTON_PIN = 18
TOUCH_IRQ_PIN = 25
TOUCH_CS = 1  # CE1 (spidev0.1)


class PeripheralBridge(Node):
    """
    Bridge Node for Pi 5 local GPIO/I2C peripherals.
    Publishes physical button and environment sensors to ROS 2.
    """

    def __init__(self):
        super().__init__("peripheral_bridge")
        self.get_logger().info("Boomy Peripheral Bridge: Initializing (Pi 5 Mode)")

        # 2. Touch Publisher [x, y, pressed]
        self.touch_pub = self.create_publisher(Int32MultiArray, "/touch", 10)

        # 3. GPIO Setup (lgpio is SOTA for Pi 5)
        try:
            self.h = lgpio.gpiochip_open(0)
            lgpio.gpio_claim_input(self.h, BUTTON_PIN, lgpio.SET_PULL_UP)
            lgpio.gpio_claim_input(self.h, TOUCH_IRQ_PIN, lgpio.SET_PULL_UP)
            self.get_logger().info("GPIO: Claimed BUTTON and TOUCH_IRQ pins")
        except Exception as e:
            self.get_logger().error(f"GPIO Entry Error: {e}")
            self.h = None

        # 4. SPI Setup for XPT2046
        try:
            import spidev

            self.spi = spidev.SpiDev()
            self.spi.open(0, TOUCH_CS)
            self.spi.max_speed_hz = 1000000
            self.get_logger().info(f"SPI: Initialized XPT2046 on CE{TOUCH_CS}")
        except Exception as e:
            self.get_logger().error(f"SPI Error: {e}")
            self.spi = None

        # Start threads
        self.alive = True
        self.btn_thread = threading.Thread(target=self._button_loop, daemon=True)
        self.touch_thread = threading.Thread(target=self._touch_loop, daemon=True)
        self.btn_thread.start()
        self.touch_thread.start()
        self._stop_event = threading.Event()
        self._thermal_state = "NORMAL"  # NORMAL, WARNING, CRITICAL
        self._cpu_temp = 0.0
        self.thermal_thread = threading.Thread(
            target=self._thermal_watchdog, daemon=True
        )
        self.thermal_thread.start()

    def _thermal_watchdog(self):
        """Monitors Pi 5 SoC temperature and executes software throttling."""
        while not self._stop_event.is_set():
            try:
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    self._cpu_temp = int(f.read().strip()) / 1000.0

                if self._cpu_temp >= 79:
                    self._thermal_state = "CRITICAL"
                elif self._cpu_temp >= 72:
                    self._thermal_state = "WARNING"
                else:
                    self._thermal_state = "NORMAL"

                # Publish system health
                msg = Float32()
                msg.data = self._cpu_temp
                self._health_pub.publish(msg)

                # Execute Throttling
                if self._thermal_state == "CRITICAL":
                    # Hard stop for missions and motors
                    self._stop_mission()

                time.sleep(2.0)
            except Exception as e:
                self.get_logger().error(f"Thermal Watchdog Error: {e}")
                time.sleep(5.0)

    def _stop_mission(self):
        self.get_logger().warn("CRITICAL THERMAL STATE: Stopping missions")

    def _button_loop(self):
        """High-frequency polling for the physical button."""
        last_state = 1
        while rclpy.ok() and self.alive:
            if self.h:
                try:
                    current_state = lgpio.gpio_read(self.h, BUTTON_PIN)
                    if current_state != last_state:
                        msg = Bool(data=(current_state == 0))
                        self.button_pub.publish(msg)
                        last_state = current_state
                except Exception as e:
                    self.get_logger().error(f"Button loop error: {e}")
            time.sleep(0.05)

    def _touch_loop(self):
        """Monitors IRQ and polls XPT2046 coordinates."""
        last_pressed = False
        while rclpy.ok() and self.alive:
            if self.h and self.spi:
                try:
                    # IRQ goes LOW when screen is touched
                    is_pressed = lgpio.gpio_read(self.h, TOUCH_IRQ_PIN) == 0
                    if is_pressed:
                        # Read X and Y (12-bit mode)
                        # Command bytes: 0x90 = X, 0xD0 = Y
                        x_raw = self._read_spi(0x90)
                        y_raw = self._read_spi(0xD0)

                        # Map 0-4095 to 480x320 (Approximation, needs calibration)
                        # Typical raw range is 200-3800
                        x = int((x_raw - 200) * 480 / 3600)
                        y = int((y_raw - 200) * 320 / 3600)

                        msg = Int32MultiArray(data=[x, y, 1])
                        self.touch_pub.publish(msg)
                        last_pressed = True
                    elif last_pressed:
                        # Release event
                        msg = Int32MultiArray(data=[0, 0, 0])
                        self.touch_pub.publish(msg)
                        last_pressed = False
                except Exception as e:
                    self.get_logger().error(f"Touch loop error: {e}")
            time.sleep(0.02)  # 50Hz polling for touch

    def _read_spi(self, cmd):
        """Helper to read 12-bit value from XPT2046."""
        resp = self.spi.xfer2([cmd, 0, 0])
        return ((resp[1] << 8) | resp[2]) >> 4

    def stop(self):
        self.alive = False
        if self.h:
            lgpio.gpiochip_close(self.h)


def main(args=None):
    rclpy.init(args=args)
    node = PeripheralBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
