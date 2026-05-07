# Rosmaster Hardware Architecture (Raspbot V2)

**Last updated**: 2026-05-07

## Dual-Bus Communication

The Rosmaster MCU (STM32) on the Raspbot V2 communicates with the Raspberry Pi 5 via **two separate buses**:

| Bus | Device | Address | Purpose |
|-----|--------|---------|---------|
| **I2C** | `/dev/i2c-1` | `0x2b` | Motors, servos, lightstrip, buzzer, ultrasonic, line sensors |
| **UART Serial** | `/dev/ttyUSB0` (CH341) | — | IMU (accel/gyro), battery voltage, odometry |

## I2C Register Map (address 0x2b)

```
0x01 — Motor control (Ctrl_Car, Ctrl_Muto)
0x02 — Servo control
0x03 — WQ2812 RGB strip ALL
0x04 — WQ2812 RGB strip single LED
0x05 — IR sensor switch
0x06 — Buzzer switch
0x07 — Ultrasonic power switch
0x08 — WQ2812 brightness ALL
0x09 — WQ2812 brightness single LED
0x0a — Line tracking sensor read (4-bit)
0x0c — Reserved / sensor data
0x1a — Ultrasonic distance LOW byte
0x1b — Ultrasonic distance HIGH byte
```

## UART Serial Protocol

The STM32 outputs IMU and battery data over UART at **921600 baud** via the CH341 USB-serial bridge (`/dev/ttyUSB0`). This data is read by `Rosmaster_Lib` (Yahboom's serial protocol library, not on PyPI — ships with the factory system image).

## Software Layers

```
┌──────────────────────────────────────────────┐
│ raspbot.pyc (Flask, port 6001)               │  ← Factory demo (host)
│  - Video streaming (/video_feed)             │
│  - Direct I2C + cv2.VideoCapture             │
│  - No IMU/battery reading                    │
├──────────────────────────────────────────────┤
│ yahboom_ros2_final (Docker)                  │  ← ROS 2 driver container
│  - Mcnamu_driver.py (Raspbot_Lib, I2C-only)  │
│  - Publishes: /cmd_vel, /rgblight, /servo,   │
│    /line_sensor, /ultrasonic                 │
│  - DOES NOT publish: /imu/data, /battery     │
├──────────────────────────────────────────────┤
│ yahboom_rosbridge_sidecar (Docker)           │  ← ROS 2 bridge
│  - rosbridge_websocket on port 9090          │
├──────────────────────────────────────────────┤
│ micro_ros_sidecar (Docker, EXITED)           │  ← Attempted ESP32 bridge
│  - microros/micro-ros-agent:humble           │
│  - Opens /dev/ttyUSB0, waits for client      │
│  - ESP32/STM32 does NOT speak micro-ROS      │
│  - Known Docker+serial bug (packet loss)      │
└──────────────────────────────────────────────┘
```

## Why IMU/Battery Don't Work

1. The factory `Mcnamu_driver.py` uses `Raspbot_Lib` (I2C-only) — it **never reads** IMU/battery
2. The `Rosmaster_Lib` that CAN read serial IMU/battery is **not installed** on this Pi
3. The `micro_ros_sidecar` was an experiment that doesn't work:
   - STM32/ESP32 firmware doesn't speak micro-ROS XRCE-DDS protocol
   - micro-ROS-in-Docker has known serial port issues (per micro-ROS GitHub)
   - Serial port `/dev/ttyUSB0` outputs no data when read directly (STM32 not streaming)

## Fix Path

To get IMU and battery:
1. **Option A** — Install `Rosmaster_Lib` on the Pi (requires internet; switch AP → home WiFi)
2. **Option B** — Write a lightweight Python serial reader that parses the STM32's binary protocol and publishes ROS topics
3. **Option C** — Use `pyserial` to read raw UART data from `/dev/ttyUSB0`, parse the STM32's data frames (typically CSV or binary format with IMU, battery, odometry fields)

## Factory Demo ("Shortcut")

The `raspbot.pyc` at `/home/pi/project_demo/raspbot/` is a Flask app on port **6001** that:
- Streams video via `/video_feed` (OpenCV capture from `/dev/video0`)
- Controls motors/lightstrip/servos via `Raspbot_Lib` (I2C)
- Does NOT use ROS at all
- Does NOT expose IMU/battery
- Is the Yahboom factory "out of box" experience
