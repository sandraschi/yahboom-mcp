#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool, Float32MultiArray
import lgpio
import time
import threading

# GPIO Pin for Yahboom Raspbot v2 KEY button
# Standard pin is 18 (PWM range) or 24. We'll monitor 18.
BUTTON_PIN = 18

class PeripheralBridge(Node):
    """
    Bridge Node for Pi 5 local GPIO/I2C peripherals.
    Publishes physical button and environment sensors to ROS 2.
    """
    def __init__(self):
        super().__init__('peripheral_bridge')
        self.get_logger().info('Boomy Peripheral Bridge: Initializing (Pi 5 Mode)')
        
        # 1. Button Publisher
        self.button_pub = self.create_publisher(Bool, '/button', 10)
        
        # 2. Environment Placeholder (Xmas Tree)
        self.env_pub = self.create_publisher(Float32MultiArray, '/environment', 10)
        
        # 3. GPIO Setup (lgpio is SOTA for Pi 5)
        try:
            self.h = lgpio.gpiochip_open(0)
            lgpio.gpio_claim_input(self.h, BUTTON_PIN, lgpio.SET_PULL_UP)
            self.get_logger().info(f'GPIO: Claimed BUTTON_PIN {BUTTON_PIN} with Pull-Up')
        except Exception as e:
            self.get_logger().error(f'GPIO Error: {e}')
            self.h = None

        # Start monitoring thread
        self.alive = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _monitor_loop(self):
        """High-frequency polling for the physical button."""
        last_state = 1 # Pull-up = 1 (Released)
        while rclpy.ok() and self.alive:
            if self.h:
                try:
                    # 0 = Pressed, 1 = Released
                    current_state = lgpio.gpio_read(self.h, BUTTON_PIN)
                    if current_state != last_state:
                        msg = Bool()
                        msg.data = (current_state == 0)
                        self.button_pub.publish(msg)
                        state_str = "PRESSED" if current_state == 0 else "RELEASED"
                        self.get_logger().info(f'Button transition: {state_str}')
                        last_state = current_state
                except Exception as e:
                    self.get_logger().error(f'Monitor loop error: {e}')
            time.sleep(0.05) # 20Hz debounce

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

if __name__ == '__main__':
    main()
