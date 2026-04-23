# Yahboom Raspbot v2 — Complete hardware stack

**Platform:** Raspbot v2 (Boomy) · ROS 2 Humble · Raspberry Pi 5  
**Tags:** `[yahboom-mcp, raspbot-v2, hardware, mecanum, rosmaster, rosbridge, i2c, battery]`  
**Related:** [`HARDWARE_AND_ROS2.md`](HARDWARE_AND_ROS2.md) · [`SENSORS.md`](SENSORS.md) · [`ROSMASTER_ESP32.md`](ROSMASTER_ESP32.md) · [`SENSORY_HUB.md`](SENSORY_HUB.md) · [`VOICE_AUDIO.md`](VOICE_AUDIO.md) · [`../ops/STARTUP_AND_BRINGUP.md`](../ops/STARTUP_AND_BRINGUP.md)

This document is the **single hardware inventory** for the Raspbot v2 stack: chassis through sensors, the **lower expansion board** (often confused with “rosbridge”), the **Raspberry Pi** tier, power, and ports. **§1** defines **MCU**, **rosbridge**, **Micro-ROS**, and the **Pi OS / Docker / ROS 2** stack in plain language. **§16** reserves space for a future **assembly** guide (the Yahboom printed leaflet is often thin). Revision-dependent details (exact MCU: ESP32-S3 vs older STM32) are called out where the fleet has seen both.

---

## 1. Terms and layers (read this first)

### 1.1 What “MCU” means here

**MCU** = **microcontroller unit** — a chip (or small module) that runs **firmware** (bare-metal or RTOS), **not** Linux.

On Raspbot v2, the **MCU lives on the Yahboom expansion / Rosmaster-class PCB under the Raspberry Pi** (the “car expansion board” in kit lists). In current generations that is commonly an **ESP32-S3**; some older documentation refers to an **STM32F103** in the same **mechanical** role. When we write **“the MCU”** in fleet docs, we mean **that lower board’s processor**, not the Raspberry Pi.

### 1.2 What “rosbridge” means (software on the Pi)

**Rosbridge** = **`rosbridge_suite`** / **`rosbridge_server`** — **Python ROS 2 nodes** that run **on the Raspberry Pi** (sometimes **inside Docker**, sometimes on the **host**, depending on image). They expose a **WebSocket** (classically port **9090**) and translate **JSON** ↔ ROS messages so a **PC** (e.g. Goliath running `yahboom-mcp` + `roslibpy`) can join the **same ROS 2 graph** as `Mcnamu_driver`, camera nodes, etc.

**Rosbridge does *not* run Micro-ROS.** It is a separate protocol stack (WebSocket/JSON).

### 1.3 What Micro-ROS is (and where it runs)

**Micro-ROS** = **ROS 2 client library on the MCU firmware** + typically a **`micro_ros_agent`** process on the **Pi** that bridges **serial** (high-speed UART over USB) into the **DDS** world. That is how the **ESP32** can appear as a first-class participant for motors/servos while the Pi runs heavy ROS nodes.

So: **Micro-ROS** = **MCU ↔ Pi** path. **Rosbridge** = **Pi ↔ PC** path. Both can be present; neither replaces the other.

### 1.4 Raspberry Pi software stack (typical Boomy image)

| Layer | What it is |
|-------|------------|
| **OS** | **Raspberry Pi OS** (Debian family) on the SD card — `apt`, `systemd`, drivers, **Docker Engine**. |
| **Docker** | Runs one or more containers (e.g. **`yahboom_ros2`** / **`yahboom_ros2_final`**) with **ROS 2 Humble** workspace, drivers, and often **rosbridge** + bringup inside the same graph the PC attaches to. |
| **Host processes** | Optional: `micro_ros_agent`, a host-only **`rosbridge.service`**, or helper scripts — depends on image and [`setup-autostart.sh`](../scripts/robot/setup-autostart.sh) / [`install-rosbridge-at-boot.sh`](../scripts/robot/install-rosbridge-at-boot.sh). |

**Correct mental model:** **Debian on Pi → Docker (often) → ROS 2 Humble in container → rosbridge WebSocket for the PC**; **parallel serial path → MCU** for real-time I/O via Micro-ROS where used.

---

## 2. Physical stack (bottom → top)

```
Floor
  ↑  Mecanum wheels (×4) + gearmotors
  ↑  Metal chassis (Yahboom Raspbot v2 bracket)
  ↑  Battery pack (2S Li-ion, in tray under / behind chassis)
  ↑  [ Car expansion board / Rosmaster driver tier ]  ← USB + 40-pin to Pi
  ↑  Raspberry Pi 5 (SBC)
  ↑  Camera + 2-DOF PTZ assembly (USB or ribbon to Pi)
  ↑  Optional: OLED, voice hat, LIDAR USB, extra HATs
```

Mechanically, the **Pi sits above** the expansion/driver PCB. A **USB cable** (often USB-A on the expansion board to USB-C on the Pi, or via the 40-pin stacking header depending on kit) carries **serial** (Micro-ROS agent ↔ ESP32) and enumeration of extra USB devices (camera, voice module, LIDAR). The **40-pin GPIO header** mates the Pi to the expansion board for **I2C**, **power**, and sometimes **SPI**.

---

## 3. Chassis, motors, and mecanum wheels

| Item | Description |
|------|-------------|
| **Chassis** | Metal frame (Raspbot v2); mounting for four motor brackets, battery tray, expansion board, and Pi stack. Typical ready-to-run mass is on the order of **~0.9–1.0 kg** including Pi and battery (kit-dependent). |
| **Drive** | **Four independent DC gearmotors** (one per wheel). Retail listings often cite **~245 RPM ±10%** class motors with **~0.8 N·m** torque (verify on your sticker). |
| **Wheels** | **Mecanum (omni) set ×4** — each wheel has free rollers at 45° so that combined speeds produce **holonomic** motion: forward/back, strafe left/right, rotate in place, and diagonal blends. |
| **ROS interface** | High-level motion is **`geometry_msgs/Twist` on `/cmd_vel`**: `linear.x` forward, `linear.y` strafe (mecanum), `angular.z` yaw rate. The driver stack maps that to four motor PWM channels on the expansion tier. |
| **Odometry** | **Quadrature encoders** on the motors feed wheel ticks into the driver; fused into **`/odom`** (`nav_msgs/Odometry`) on the ROS 2 side. Dead-reckoning drifts without LIDAR/SLAM. |

---

## 4. RGB lightstrip

| Item | Description |
|------|-------------|
| **Hardware** | **WS2812B** (or compatible) addressable RGB strip along the chassis (“RGB light bar” in Yahboom listings). |
| **Control** | In the **ROS + factory driver** path, colors and patterns are driven from the expansion / **`Raspbot`** I2C API (see [`HARDWARE_DIAGNOSIS_VOICE_I2C.md`](HARDWARE_DIAGNOSIS_VOICE_I2C.md): `Ctrl_WQ2812_brightness_ALL` style calls). In **ROS 2 graph** mode, **`yahboom-mcp`** publishes to **`/rgblight`** (`std_msgs/Int32MultiArray`) and pattern engines in `operations/lightstrip.py` drive patrol / rainbow / breathe / fire. |
| **Power** | Fed from the expansion board’s regulated 5 V logic rail (not raw battery). |

---

## 5. PTZ servos and camera

| Item | Description |
|------|-------------|
| **PTZ** | **2-DOF gimbal**: pan + tilt. Yahboom kits commonly use **YB-SG90-class digital servos**, **4.8–6.0 V** rail, mounted on a **PTZ bracket** with a small **camera platform PCB** carrying the sensor. |
| **ROS** | Camera PTZ uses **`yahboomcar_msgs/msg/ServoControl` on `/servo`** with fields **`servo_s1` (pan, ID 1)** and **`servo_s2` (tilt, ID 2)**. The driver applies **both** angles every publish — see [`ROSBRIDGE.md`](ROSBRIDGE.md) (Publisher details, **`publish_servo`**). |
| **Actuation path** | On **ESP32-S3 Rosmaster** stacks, PWM for servos is generated on the co-processor after commands traverse **Micro-ROS** from the Pi (**921600** baud class links are used in fleet configs). PTZ is **not** found on the Pi’s I2C bus. |
| **Camera** | Typically a **USB webcam** (e.g. **480p/720p**, **~110° HFOV** class) or **Raspberry Pi Camera Module** via **CSI ribbon**. ROS exposes **`/camera/image_raw`** (or compressed); **`VideoBridge`** on the gateway restreams **MJPEG** at **`GET /stream`**. |

---

## 6. IMU (inertial measurement unit)

| Item | Description |
|------|-------------|
| **Role** | Heading, pitch, roll; gyro and accel for stabilization and telemetry. |
| **Hardware placement** | **On or tightly coupled to the expansion / Rosmaster tier** (MPU-9250 / ICM-42670-class parts appear in internal docs depending on revision). |
| **ROS** | **`sensor_msgs/Imu` on `/imu/data`** (~100 Hz typical). `yahboom-mcp` converts quaternion → Euler for the dashboard. |
| **Transport note** | Some factory Python paths read IMU/battery streams over **USB-UART** (`/dev/ttyUSB*`) from the expansion tier; **udev** rules are required when multiple USB serial devices exist (voice module, ESP32 bridge). See [`VOICE_AUDIO.md`](VOICE_AUDIO.md) §2. |

---

## 7. Front distance sensing (ultrasonic)

| Item | Description |
|------|-------------|
| **Hardware** | **Ultrasonic rangefinder** module mounted forward (kit: single module common). |
| **ROS** | **`sensor_msgs/Range` on `/sonar`** (override with `YAHBOOM_ULTRASONIC_TOPIC` if your bringup remaps). Distance in **metres** for `yahboom-mcp` telemetry and obstacle logic. |
| **Alternate bus** | Legacy / factory **`Raspbot`** Python can expose distance via **I2C register reads** on the expansion board; the **ROS 2** bringup normalizes to topics for `Mcnamu_driver` / Docker stack. |

---

## 8. Line / cliff sensing (downward IR)

| Item | Description |
|------|-------------|
| **Hardware** | **Four-channel IR reflectance** module (“tracking” module in kit lists): downward-looking LEDs/photodiodes for **line following** and **table-edge (cliff)** detection. |
| **Semantics** | Convention in this repo: **`0` = void / no line / drop-off risk**, **`1` = line / floor present** per channel in **`std_msgs/Int32MultiArray`** on **`/line_sensor`** (or legacy `/infrared_line`). See [`SENSORY_HUB.md`](SENSORY_HUB.md). |
| **Indicator LEDs** | Small **blue/status LEDs** above each sensor often mirror **analog** “no floor” detection; they are **not** the RGB lightstrip and are **not** individually controllable from ROS. |
| **Safety** | Mission / avoidance code treats **all channels void** as **cliff / edge** condition — see [`../core/AVOIDANCE_STRATEGY.md`](../core/AVOIDANCE_STRATEGY.md). |

---

## 9. “Rosbridge board” — what it actually is (and what it is not)

> **Naming collision (important)**  
> In **ROS** documentation, **rosbridge** means **`rosbridge_suite`** — **software** (Python nodes) on the **Raspberry Pi** (often **inside Docker**) exposing **WebSocket port ~9090** so a **PC** can use **JSON**, not DDS, to talk to the ROS 2 graph.  
> In **conversation**, people sometimes call the **green / blue Yahboom expansion PCB under the Pi** the “rosbridge board.” That PCB is the **Rosmaster / motor-driver tier** with an **MCU** (§1.1); it does **not** execute `rosbridge_server` by itself.

### 9.1 Lower expansion / Rosmaster tier (physical)

| Aspect | Typical Raspbot v2 (ESP32-S3 generation) |
|--------|------------------------------------------|
| **MCU** | **Espressif ESP32-S3** dual-core Xtensa LX7 (up to **240 MHz** class), **512 KB SRAM** + **PSRAM** option (2–8 MB depending on rev). *Older kits may use STM32F103-class MCUs; same mechanical tier, different firmware.* |
| **USB to Pi** | **CP2102** (or CH340) **USB↔UART** — enumerates as **`/dev/ttyUSB0`** / **`/dev/ttyACM0`**. Used for **Micro-ROS** (and/or proprietary streams) between **Pi ↔ MCU**. |
| **Motor outputs** | **4× PWM** H-bridge channels for mecanum quadrature. |
| **Encoders** | Quadrature decoding for odometry. |
| **Servo headers** | **Multi-channel PWM** for PTZ (and expansion servos). |
| **RGB** | **WS2812B** controller for chassis strip. |
| **On-MCU IMU** | Some revisions expose **6-axis** IMU on the ESP32 board **in addition to** or **instead of** separate MPU parts — always trust your live **`/imu/data`** source. |
| **Power** | Distributes **battery** (see §12), **5 V** for logic/servos, **charging jack** path, and **buzzer** where fitted. |

### 9.2 Software “rosbridge” (on the Pi)

| Aspect | Detail |
|--------|--------|
| **Package** | **`rosbridge_server`** / **`rosbridge_suite`**. |
| **Runs on** | **Linux on the Raspberry Pi** — same machine as Docker; often **inside** the ROS container in Yahboom images. |
| **Role** | WebSocket **JSON** bridge into ROS 2 topics for **`roslibpy`** on **Goliath** (`yahboom-mcp` `ROS2Bridge`). |
| **Port** | Default **`9090`** (`YAHBOOM_BRIDGE_PORT`). |

### 9.3 Rosbridge vs Micro-ROS (explicit)

| | **Rosbridge (`rosbridge_suite`)** | **Micro-ROS** |
|---|-------------------------------------|----------------|
| **Purpose** | Let a **PC** speak to ROS 2 over **WebSocket/JSON**. | Let an **MCU** speak ROS 2 over **serial** via an **agent** on the Pi. |
| **Runs on** | **Pi** (Python, Linux). | **Firmware on MCU** + **agent** on Pi. |
| **Typical port** | TCP **9090** (WebSocket). | UART `/dev/ttyUSB*` etc. |
| **Used by** | `yahboom-mcp` / browsers / non-ROS tools. | ESP32 motor/servo real-time path. |

**Summary:** Keep **“MCU board under the Pi”**, **“Micro-ROS serial link”**, and **“rosbridge WebSocket on the Pi for the PC”** as **three** separate ideas.

---

## 10. Raspberry Pi 5 (on top of the expansion tier)

| Subsystem | Typical use on Raspbot v2 |
|-----------|---------------------------|
| **USB-C (power)** | **5 V PD** input for Pi (official adapter). Separate from battery rail — Pi is powered when USB-C is connected; **robot motion** still requires battery + expansion power path per kit wiring. |
| **USB-A / USB-3** | **Camera** (USB), **LIDAR** (USB), **AI voice module** (USB serial), **keyboard/wifi dongle** (if used). Prefer **USB 3** (blue) for high-bandwidth camera/LIDAR. |
| **Ethernet RJ-45** | Optional **wired** link to LAN or tethered PC (useful when Wi‑Fi AP mode is not used). |
| **Wi-Fi / Bluetooth** | On-module; used for **Raspbot AP**, home Wi‑Fi, or SSH. |
| **CSI camera port** | **22-pin 0.5 mm** ribbon to **Raspberry Pi Camera** (alternative to USB cam). |
| **40-pin GPIO header** | **Stacks onto expansion board**: **I2C-1** (`SDA`/`SCL`) for OLED and some legacy **`Raspbot`** calls, **3.3 V logic**, **SPI** if used, **UART** on GPIO pins if enabled in `config.txt`, **GND**. **Do not** assume PTZ servos appear on I2C — see §5. |
| **Micro SD** | Boot / rootfs for Raspberry Pi OS or Yahboom-flavored image. |
| **PoE header** | Present on Pi 5 board; **not** required for Raspbot v2 default kit. |

**What can be connected (typical):**

- **USB:** Camera, LIDAR, CSK4002 voice board, USB audio, USB Ethernet adapter.  
- **CSI:** Pi Camera Module variants.  
- **GPIO / I2C (via header):** OLED (e.g. **0x3C**), environmental add-ons, **KEY** button via GPIO18 (see [`SENSORY_HUB.md`](SENSORY_HUB.md)).  
- **Ethernet:** Docked / lab tether.  

Docker / ROS 2 stacks may need **`--device /dev/video0`**, **`/dev/ttyUSB*`**, **`/dev/i2c-1`** passed into containers — see bringup scripts in `scripts/robot/`.

---

## 11. I2C bus summary (Pi ↔ expansion)

| Function | Typical bus | Notes |
|----------|-------------|--------|
| Motor / lightstrip legacy API | **I2C-1** | `Raspbot` class addresses (e.g. **0x2b**) on **`/dev/i2c-1`**. |
| OLED display | **I2C-1** | **SSD1306/SH1106** at **0x3C** common. |
| Ultrasonic / line (legacy Python) | **I2C-1** | Register reads on expansion; ROS stack may remap to topics. |
| IMU (ROS path) | **Topic `/imu/data`** | Sourced from driver stack on expansion / MCU path. |

Always run **`i2cdetect -y 1`** on a live Pi to confirm addresses for **your** revision.

---

## 12. Battery, charger, and main power switch

| Item | Typical specification (verify on pack) |
|------|----------------------------------------|
| **Chemistry** | **2S lithium-ion** (two **18650** cells in series). |
| **Nominal voltage** | **7.4 V** (Yahboom docs: operating roughly **5.6–8.4 V** window). |
| **Capacity** | Often **2000 mAh** class in bundled pack. |
| **BMS** | Over-charge, over-discharge, over-current, short-circuit protection on quality packs. |
| **Charger** | **12.6 V** constant-voltage charger (for 2S) with LED **red = charging / green = full** (Yahboom guidance). |
| **Main switch** | **Hard power** on the **expansion board** — cuts motor and logic rails for storage/shipping. **Yahboom requires: turn OFF before plugging in the barrel charger** to avoid damage / sparking. |
| **ROS** | **`/battery_state`** (`sensor_msgs/BatteryState`) — voltage and **percentage** (0–1 in ROS, scaled to 0–100% in dashboard). |
| **Alarm** | Low-battery **buzzer** on expansion per Yahboom user guide. |

---

## 13. Optional / addon modules (not all in base kit)

| Module | Interface | Notes |
|--------|-----------|--------|
| **MS200 / YDLIDAR / RPLIDAR** | **USB** | Publishes **`/scan`**. See [`HARDWARE_AND_ROS2.md`](HARDWARE_AND_ROS2.md) §5. |
| **CSK4002 voice hat** | **USB serial** | Wake word + 85 fixed phrases; arbitrary TTS via Pi ALSA. [`VOICE_AUDIO.md`](VOICE_AUDIO.md). |
| **3.5" touch / peripheral bridge** | **SPI / GPIO** | See [`RASPI_SOFTWARE_STACK.md`](../ops/RASPI_SOFTWARE_STACK.md) and `scripts/robot/peripheral_bridge.py`. |

---

## 14. Software cross-reference (`yahboom-mcp`)

| Hardware | ROS topics / API (when bridge live) |
|----------|-------------------------------------|
| Mecanum motion | Publish **`/cmd_vel`** |
| Lightstrip | Publish **`/rgblight`** |
| PTZ | Publish **`/servo`** (`ServoControl`) |
| IMU | Subscribe **`/imu/data`** |
| Odom | Subscribe **`/odom`** |
| Battery | Subscribe **`/battery_state`** |
| Forward range | Subscribe **`/sonar`** |
| Line / cliff | Subscribe **`/line_sensor`** |
| LIDAR | Subscribe **`/scan`** |
| Video | **`/camera/image_raw`** → MJPEG `/stream` |

---

## 15. Assembly (placeholder for detailed build guide)

The **printed quick-start** shipped in the Yahboom box is often **too terse** for a confident first build (cable dress, mecanum roller orientation, strain relief, and first power-on sequence). This section will grow into a **fleet-grade assembly and checkout** document.

**Planned content (TODO — contributions welcome):**

1. **Mechanical** — frame halves, motor bracket torque order, **mecanum wheel orientation** (roller diagonals must match Yahboom diagram or the car “crabs” wrong), wheel encoder plugs.  
2. **Electrical** — battery tray polarity, **JST/XT60** double-check, stacking **40-pin** Pi onto expansion (no bent pins), **USB-A–to–USB-C** link from expansion to Pi if applicable, **camera ribbon** insertion depth.  
3. **Peripherals** — ultrasonic height, **four-channel IR** distance to floor, **PTZ** mechanical limits (don’t bind servos at end of travel).  
4. **First boot** — main **switch** position, **charger rule** (off before barrel plug), SD image / Wi‑Fi AP vs home LAN.  
5. **ROS smoke test** — `ros2 topic list`, **`rosbridge` port 9090**, Docker **`--device`** checklist for `/dev/video0`, `/dev/ttyUSB*`, `/dev/i2c-1`.

Until those steps exist here, use the Yahboom booklet for **part identification** only, and cross-check motor directions and wheel patterns against official video or forum threads if the paper instructions are ambiguous.

---

## 16. See also

- **[Startup & bringup](../ops/STARTUP_AND_BRINGUP.md)** — Power-on order, Docker, **rosbridge_suite** vs network.  
- **[ROSBRIDGE.md](ROSBRIDGE.md)** — `ROS2Bridge` protocol details.  
- **[SENSORS.md](SENSORS.md)** — Deep dive on IMU, odom, battery, LIDAR math.  
- **[Yahboom battery safety](https://www.yahboom.net/public/upload/upload-html/1734684647/Robot%20Charging%20and%20Battery%20Considerations.html)** — official charging procedure.
