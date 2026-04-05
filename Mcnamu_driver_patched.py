#!/usr/bin/env python3
# encoding: utf-8
#
# Mcnamu_driver_patched.py — Yahboom Raspbot v2 ROS 2 driver
#
# Hardware architecture:
#   Motion (wheels, lights, ultrasonic, line follower):
#     → Raspbot class → I2C (/dev/i2c-1, addr 0x2b)
#   Sensors (IMU, battery, gyro):
#     → Rosmaster class → UART serial (/dev/ttyROSMASTER or /dev/ttyUSB0)
#   Voice hat: separate /dev/ttyVOICE — NOT handled here
#   OLED:      I2C (/dev/i2c-1, addr 0x3c) — handled by display.py via luma.oled
#
# Environment variables:
#   BOOMY_SENSOR_PORT   — serial port for Rosmaster (default: /dev/ttyROSMASTER)
#                         Falls back to /dev/ttyUSB0 if symlink not present
#   BOOMY_SENSOR_BAUD   — baud rate (default: 115200)

import os
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, BatteryState
from std_msgs.msg import Int32, Bool, Int32MultiArray, Float32
from yahboomcar_msgs.msg import ServoControl
from Raspbot_Lib import Raspbot
from Rosmaster_Lib import Rosmaster
import time
import math

# Battery cell chemistry constants
_CELL_COUNT   = 3          # 3S LiPo
_CELL_FULL_V  = 4.20       # V per cell fully charged
_CELL_EMPTY_V = 3.00       # V per cell empty (safe cutoff)
_BAT_FULL_V   = _CELL_COUNT * _CELL_FULL_V   # 12.6 V
_BAT_EMPTY_V  = _CELL_COUNT * _CELL_EMPTY_V  # 9.0 V

# Serial port resolution: prefer udev symlink, fall back to ttyUSB0
def _resolve_sensor_port() -> str:
    candidates = [
        os.environ.get("BOOMY_SENSOR_PORT", "/dev/ttyROSMASTER"),
        "/dev/ttyUSB0",
        "/dev/ttyUSB1",
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return p
    return "/dev/ttyUSB0"   # last resort, may fail


class YahboomCarDriver(Node):
    def __init__(self, name):
        super().__init__(name)

        sensor_port = _resolve_sensor_port()
        sensor_baud = int(os.environ.get("BOOMY_SENSOR_BAUD", "115200"))
        self.get_logger().info(f"Sensor serial port: {sensor_port} @ {sensor_baud}")

        # ── Motion Controller (I2C via Raspbot) ─────────────────────────────
        try:
            self.car = Raspbot()
            self.car.Ctrl_Ulatist_Switch(1)
            self.get_logger().info("Raspbot I2C motion controller OK")
        except Exception as e:
            self.get_logger().error(f"Raspbot I2C init failed: {e}")
            self.car = None

        # ── Sensor Controller (UART via Rosmaster) ───────────────────────────
        try:
            self.sensors = Rosmaster(com=sensor_port)
            self.sensors.create_receive_threading()
            time.sleep(0.5)   # let thread collect first packet
            # Quick sanity check — if gyro returns all zeros AND voltage is 0,
            # something is wrong with the serial connection
            gyro_check = self.sensors.get_gyroscope_data()
            volt_check  = self.sensors.get_battery_voltage()
            self.get_logger().info(
                f"Rosmaster UART OK — gyro={gyro_check}, volt={volt_check}"
            )
            self.sensors_ok = True
        except Exception as e:
            self.get_logger().error(f"Rosmaster UART init failed on {sensor_port}: {e}")
            self.get_logger().error(
                "HINT: check 'ls /dev/ttyUSB*' and udev rule for ttyROSMASTER. "
                "Also verify Docker has --device /dev/ttyUSB0 mapped."
            )
            self.sensors = None
            self.sensors_ok = False

        # ── ROS 2 Subscribers ────────────────────────────────────────────────
        self.create_subscription(Twist,          'cmd_vel',       self.cmd_vel_callback,    1)
        self.create_subscription(Int32MultiArray,'rgblight',      self.rgb_callback,       100)
        self.create_subscription(Int32,          'rgblight_effect',self.effect_callback,   100)
        self.create_subscription(Bool,           'buzzer',        self.buzzer_callback,    100)
        self.create_subscription(ServoControl,   'servo',         self.servo_callback,      10)

        # ── ROS 2 Publishers ─────────────────────────────────────────────────
        self.pub_line     = self.create_publisher(Int32MultiArray, 'line_sensor',   10)
        self.pub_sonar    = self.create_publisher(Float32,         'ultrasonic',    10)
        self.pub_imu      = self.create_publisher(Imu,             'imu/data',      10)
        self.pub_battery  = self.create_publisher(BatteryState,    'battery_state', 10)

        # ── Light effect state ───────────────────────────────────────────────
        self.current_effect = 0
        self.effect_step    = 0
        self.create_timer(0.2,  self.effect_loop)
        self.create_timer(0.1,  self.pub_data)

    # ── Motion ───────────────────────────────────────────────────────────────

    def cmd_vel_callback(self, msg: Twist):
        if not self.car:
            return
        vx = msg.linear.x
        vy = msg.linear.y
        vz = msg.angular.z

        # Mecanum wheel mixing
        k_spin = (117 + 132) / 8.0
        fb   = vx * 255
        lr   = -vy * 255
        spin = -vz * k_spin

        self.car.Ctrl_Muto(0, int(fb + lr + spin))
        self.car.Ctrl_Muto(1, int(fb - lr + spin))
        self.car.Ctrl_Muto(2, int(fb - lr - spin))
        self.car.Ctrl_Muto(3, int(fb + lr - spin))

    # ── Light effects ────────────────────────────────────────────────────────

    def effect_callback(self, msg: Int32):
        self.get_logger().info(f"Light effect: {msg.data}")
        self.current_effect = msg.data
        self.effect_step    = 0
        if self.current_effect == 0:
            self._set_rgb(0, 0, 0)

    def effect_loop(self):
        if self.current_effect == 0:
            return
        if self.current_effect == 10:   # Patrol car
            self.effect_step = (self.effect_step + 1) % 2
            if self.effect_step == 0:
                self._set_rgb(255, 0, 0)
            else:
                self._set_rgb(0, 0, 255)
        elif 1 <= self.current_effect <= 6:
            if self.sensors:
                try:
                    self.sensors.set_colorful_effect(self.current_effect, 6, 255)
                except Exception as e:
                    self.get_logger().debug(f"set_colorful_effect: {e}")

    def rgb_callback(self, msg: Int32MultiArray):
        self.current_effect = 0
        if len(msg.data) == 3:
            self._set_rgb(*msg.data)

    def _set_rgb(self, r: int, g: int, b: int):
        if self.sensors:
            try:
                self.sensors.set_colorful_lamps(0xFF, r, g, b)
            except Exception as e:
                self.get_logger().debug(f"set_colorful_lamps: {e}")
        if self.car:
            try:
                self.car.Ctrl_WQ2812_brightness_ALL(r, g, b)
            except Exception as e:
                self.get_logger().debug(f"Ctrl_WQ2812: {e}")

    # ── Other actuators ──────────────────────────────────────────────────────

    def buzzer_callback(self, msg: Bool):
        if self.car:
            self.car.Ctrl_BEEP_Switch(1 if msg.data else 0)

    def servo_callback(self, msg: ServoControl):
        if self.car:
            self.car.Ctrl_Servo(1, msg.servo_s1)
            self.car.Ctrl_Servo(2, msg.servo_s2)

    # ── Sensor publishing ────────────────────────────────────────────────────

    def pub_data(self):
        now = self.get_clock().now().to_msg()

        # ── I2C sensors (via Raspbot) ────────────────────────────────────────
        if self.car:
            # Line follower
            try:
                track = self.car.read_data_array(0x0a, 1)
                if track and len(track) >= 1:
                    val = int(track[0])
                    msg = Int32MultiArray(data=[
                        (val >> 2) & 1,
                        (val >> 3) & 1,
                        (val >> 1) & 1,
                         val       & 1,
                    ])
                    self.pub_line.publish(msg)
            except Exception as e:
                self.get_logger().debug(f"Line sensor read failed: {e}")

            # Ultrasonic
            try:
                h_data = self.car.read_data_array(0x1b, 1)
                l_data = self.car.read_data_array(0x1a, 1)
                if h_data and l_data and len(h_data) >= 1 and len(l_data) >= 1:
                    distance_cm = (h_data[0] << 8 | l_data[0]) / 10.0
                    self.pub_sonar.publish(Float32(data=float(distance_cm)))
            except Exception as e:
                self.get_logger().debug(f"Ultrasonic read failed: {e}")

        # ── UART sensors (via Rosmaster) ────────────────────────────────────
        if self.sensors:
            # Battery
            try:
                volt = self.sensors.get_battery_voltage()
                if volt is not None and float(volt) > 0.1:
                    bat                = BatteryState()
                    bat.voltage        = float(volt)
                    bat.percentage     = max(0.0, min(1.0,
                        (bat.voltage - _BAT_EMPTY_V) / (_BAT_FULL_V - _BAT_EMPTY_V)
                    ))
                    bat.power_supply_status = 2   # discharging
                    self.pub_battery.publish(bat)
            except Exception as e:
                self.get_logger().warning(f"Battery read failed: {e}")

            # IMU
            try:
                imu_msg              = Imu()
                imu_msg.header.stamp = now
                imu_msg.header.frame_id = "base_link"

                acc  = self.sensors.get_accelerometer_data()
                gyro = self.sensors.get_gyroscope_data()

                if acc and len(acc) >= 3:
                    imu_msg.linear_acceleration.x = float(acc[0])
                    imu_msg.linear_acceleration.y = float(acc[1])
                    imu_msg.linear_acceleration.z = float(acc[2])
                    # Mark acceleration covariance as known
                    imu_msg.linear_acceleration_covariance[0] = 0.01

                if gyro and len(gyro) >= 3:
                    deg2rad = math.pi / 180.0
                    imu_msg.angular_velocity.x = float(gyro[0]) * deg2rad
                    imu_msg.angular_velocity.y = float(gyro[1]) * deg2rad
                    imu_msg.angular_velocity.z = float(gyro[2]) * deg2rad
                    imu_msg.angular_velocity_covariance[0] = 0.01

                # Orientation unknown — tell downstream to ignore it
                imu_msg.orientation_covariance[0] = -1.0

                if acc or gyro:
                    self.pub_imu.publish(imu_msg)

            except Exception as e:
                self.get_logger().warning(f"IMU read failed: {e}")


def main(args=None):
    rclpy.init(args=args)
    driver = YahboomCarDriver("driver_node")
    driver.get_logger().info("Yahboom Raspbot v2 driver started")
    try:
        rclpy.spin(driver)
    except KeyboardInterrupt:
        pass
    finally:
        if driver.car:
            driver.car.Ctrl_Ulatist_Switch(0)
            driver.car.Ctrl_Car(0, 0, 0)
        if driver.sensors:
            driver.sensors.cancel_receive_threading()
        driver.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()


import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, BatteryState
from std_msgs.msg import Int32, Bool, Int32MultiArray, Float32
from yahboomcar_msgs.msg import ServoControl
from Raspbot_Lib import Raspbot
from Rosmaster_Lib import Rosmaster
import time
import math

class YahboomCarDriver(Node):
    def __init__(self, name):
        super().__init__(name)
        
        # Motion Controller (I2C)
        try:
            self.car = Raspbot()
            self.car.Ctrl_Ulatist_Switch(1)
            self.get_logger().info('Initialized Raspbot I2C for motion')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize Raspbot I2C: {e}')
            self.car = None
        
        # Sensory Controller (Serial)
        try:
            self.sensors = Rosmaster(com='/dev/ttyUSB0')
            self.sensors.create_receive_threading()
            self.get_logger().info('Initialized Rosmaster sensors on /dev/ttyUSB0')
        except Exception as e:
            self.get_logger().error(f'Failed to initialize Rosmaster sensors: {e}')
            self.sensors = None

        # Create subscribers
        self.create_subscription(Twist, 'cmd_vel', self.cmd_vel_callback, 1)
        self.create_subscription(Int32MultiArray, 'rgblight', self.RGBLightcallback, 100)
        self.create_subscription(Int32, 'rgblight_effect', self.effect_callback, 100)
        self.create_subscription(Bool, 'buzzer', self.Buzzercallback, 100)
        self.create_subscription(ServoControl, 'servo', self.servo_callback, 10)

        # Create publishers
        self.pub_line_sensor = self.create_publisher(Int32MultiArray, 'line_sensor', 10)
        self.pub_ultrasonic = self.create_publisher(Float32, 'ultrasonic', 10)
        self.pub_imu = self.create_publisher(Imu, 'imu/data', 10)
        self.pub_battery = self.create_publisher(BatteryState, 'battery_state', 10)

        # Effect State
        self.current_effect = 0
        self.effect_step = 0
        self.effect_timer = self.create_timer(0.2, self.effect_loop)

        # Timer to publish sensor data
        self.timer = self.create_timer(0.1, self.pub_data)

    def cmd_vel_callback(self, msg):
        if not self.car: return
        # Motion logic (I2C)
        vx = msg.linear.x
        vy = msg.linear.y
        vz = msg.angular.z

        speed_lr = -vy * 255
        speed_fb = vx * 255
        speed_spin = -vz * (117+132)/8

        r1 = speed_fb + speed_lr + speed_spin
        r2 = speed_fb - speed_lr + speed_spin
        r3 = speed_fb - speed_lr - speed_spin
        r4 = speed_fb + speed_lr - speed_spin

        self.car.Ctrl_Muto(0, int(r1))
        self.car.Ctrl_Muto(1, int(r2))
        self.car.Ctrl_Muto(2, int(r3))
        self.car.Ctrl_Muto(3, int(r4))

    def effect_callback(self, msg):
        self.get_logger().info(f'Switching light effect to: {msg.data}')
        self.current_effect = msg.data
        self.effect_step = 0
        if self.current_effect == 0:
            if self.sensors: self.sensors.set_colorful_lamps(0xFF, 0, 0, 0)
            if self.car: self.car.Ctrl_WQ2812_brightness_ALL(0, 0, 0)

    def effect_loop(self):
        if self.current_effect == 0: return

        # Effect 10: Patrol Car (Police)
        if self.current_effect == 10:
            self.effect_step = (self.effect_step + 1) % 2
            if self.effect_step == 0:
                # Red
                if self.sensors: self.sensors.set_colorful_lamps(0xFF, 255, 0, 0)
                if self.car: self.car.Ctrl_WQ2812_brightness_ALL(255, 0, 0)
            else:
                # Blue
                if self.sensors: self.sensors.set_colorful_lamps(0xFF, 0, 0, 255)
                if self.car: self.car.Ctrl_WQ2812_brightness_ALL(0, 0, 255)
        
        # Effect 1-6: Rosmaster built-in effects
        elif 1 <= self.current_effect <= 6:
            if self.sensors:
                try:
                    self.sensors.set_colorful_effect(self.current_effect, 6, 255)
                    # Stop loop after triggering built-in effect if it persists hardware-side
                    # but Rosmaster_Lib usually needs repeated calls or sets a mode.
                    # For now we'll just keep calling or set it once.
                except: pass

    def RGBLightcallback(self, msg):
        if not isinstance(msg, Int32MultiArray): return
        self.current_effect = 0 # Manual control overrides effects
        if len(msg.data) == 3:
            R, G, B = msg.data
            # Try Rosmaster lightstrip first
            if self.sensors:
                  try:
                      self.sensors.set_colorful_lamps(0xFF, R, G, B)
                  except: pass
            # Fallback to Raspbot I2C
            if self.car:
                  try:
                      self.car.Ctrl_WQ2812_brightness_ALL(R, G, B)
                  except: pass

    def Buzzercallback(self, msg):
        if self.car:
            self.car.Ctrl_BEEP_Switch(1 if msg.data else 0)

    def servo_callback(self, msg):
        if self.car:
            self.car.Ctrl_Servo(1, msg.servo_s1)
            self.car.Ctrl_Servo(2, msg.servo_s2)

    def pub_data(self):
        # Line sensor (I2C)
        if self.car:
            try:
                track = self.car.read_data_array(0x0a, 1)
                if track:
                    val = int(track[0])
                    msg = Int32MultiArray(data=[(val>>2)&1, (val>>3)&1, (val>>1)&1, val&1])
                    self.pub_line_sensor.publish(msg)
            except: pass

            # Ultrasonic (I2C)
            try:
                # Fix for index out of range check
                h_data = self.car.read_data_array(0x1b, 1)
                l_data = self.car.read_data_array(0x1a, 1)
                if h_data and l_data:
                    h = h_data[0]
                    l = l_data[0]
                    dis = (h << 8 | l) / 10.0
                    self.pub_ultrasonic.publish(Float32(data=float(dis)))
            except: pass

        # Battery & IMU (Serial/Rosmaster)
        if self.sensors:
            try:
                # Battery
                bat_msg = BatteryState()
                volt = self.sensors.get_battery_voltage()
                if volt:
                    bat_msg.voltage = float(volt)
                    bat_msg.percentage = (bat_msg.voltage - 9.0) / (12.6 - 9.0) if bat_msg.voltage > 9.0 else 0.0
                    self.pub_battery.publish(bat_msg)

                # IMU
                imu_msg = Imu()
                imu_msg.header.stamp = self.get_clock().now().to_msg()
                imu_msg.header.frame_id = 'base_link'
                
                acc = self.sensors.get_accelerometer_data()
                gyro = self.sensors.get_gyroscope_data()
                
                if acc:
                    imu_msg.linear_acceleration.x = float(acc[0])
                    imu_msg.linear_acceleration.y = float(acc[1])
                    imu_msg.linear_acceleration.z = float(acc[2])
                
                if gyro:
                    imu_msg.angular_velocity.x = float(gyro[0]) * (math.pi / 180.0)
                    imu_msg.angular_velocity.y = float(gyro[1]) * (math.pi / 180.0)
                    imu_msg.angular_velocity.z = float(gyro[2]) * (math.pi / 180.0)
                    
                self.pub_imu.publish(imu_msg)
            except: pass

def main(args=None):
    rclpy.init(args=args)
    driver = YahboomCarDriver('driver_node')
    driver.get_logger().info('Successfully started the hybrid chassis drive...')
    try:
        rclpy.spin(driver)
    except KeyboardInterrupt:
        if driver.car: driver.car.Ctrl_Ulatist_Switch(0)
        if driver.car: driver.car.Ctrl_Car(0, 0, 0)
        driver.get_logger().info('Shutting down...')
    finally:
        driver.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
