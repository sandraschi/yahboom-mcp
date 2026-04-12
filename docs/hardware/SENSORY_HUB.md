# Boomy Sensory Hub (RPi 5 Expansion)

Boomy's sensory substrate is expanded via a local bridge running on the Raspberry Pi 5. This allows for high-frequency polling of physical buttons, ultrasound distance sensors, and infrared cliff/line sensors.

## Line follow & cliff (downward IR)

The **same** downward-facing **infrared reflectance** array is used for:

- **Line following** — dark line vs floor contrast.
- **Table edge / “cliff”** — when the beam sees little or no nearby floor (void / bright surface pattern), the stack treats that as a drop-off risk.

Convention in this project: **`0` = void / no line**, **`1` = line** (per channel), as published in `Int32MultiArray.data`. The bridge default topic is **`/line_sensor`** (see `YAHBOOM_LINE_TOPIC` on the MCP host). Older docs may say `/infrared_line`; remap or align with your `Mcnamu` / bringup launch.

### Onboard blue (or status) LEDs above the sensors

Many Raspbot boards mount **small indicator LEDs directly above** each downward IR sensor. They are **analog front-end or comparator indicators**: they light when the sensor sees **no close reflecting surface** (e.g. robot lifted, or edge/cliff) and often go dark when the floor is in range. They are **not** the chassis RGB lightstrip, **not** the patrol-car red/blue pattern, and **not** controlled via ROS topics — they mirror **local** sensor state. Software only sees the digitized values on `/line_sensor` (and mission logic such as cliff guard in `missions.py`).

## 🛰️ Technical Specification

### ROS 2 Topics

| Topic | Message Type | Purpose | Source |
|-------|--------------|---------|--------|
| `/sonar` | `sensor_msgs/Range` | Ultrasound distance (metres) | RPi 5 Bridge |
| `/line_sensor` (default) | `std_msgs/Int32MultiArray` | IR line/cliff channels (0=Void, 1=Line) | `Mcnamu` / driver — override with `YAHBOOM_LINE_TOPIC` |
| `/infrared_line` | `std_msgs/Int32MultiArray` | Legacy name for line array (same semantics) | Some bridges |
| `/button` | `std_msgs/Bool` | Top-mounted "KEY" button state (True=Pressed) | RPi 5 GPIO 18 |

### Hardware Mapping (RPi 5 GPIO)

| Peripheral | Board Pin | GPIO (BCM) | Logic |
|------------|-----------|------------|-------|
| **KEY Button** | Pin 12 | GPIO 18 | Pull-Up / Active Low |

## 🚀 Deployment (Robot-Side)

The bridge is implemented in `scripts/robot/peripheral_bridge.py`. It should be deployed to the robot and managed via `systemd`.

### Manual Startup
```bash
python3 ~/yahboom-mcp/scripts/robot/peripheral_bridge.py
```

### Automation (systemd)
Deploy the service file to allow Boomy's senses to start on boot:

```bash
# 1. Copy service file
sudo cp ~/yahboom-mcp/scripts/robot/yahboom-peripheral-bridge.service /etc/systemd/system/

# 2. Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable yahboom-peripheral-bridge.service
sudo systemctl start yahboom-peripheral-bridge.service
```

## 🛠️ Auto-Discovery
The `peripheral_bridge.py` includes a lightweight I2C scanning module that identifies:
- **SSD1306 / SH1106**: OLED displays (typically 0x3C).
- **BME280 / SGP40**: Environmental sensors (coming soon).

> [!NOTE]
> Ensure the `lgpio` library is installed on your Pi 5 for robust GPIO interaction without relying on legacy `RPi.GPIO` sysfs.
