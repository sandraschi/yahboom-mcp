# Yahboom Raspbot v2 — Connectivity Guide

**Updated:** 2026-04-04
**Status:** WiFi is the primary operational interface. Ethernet is for initial setup / recovery only.

---

## Network Architecture

The Pi 5 has two network interfaces. They must **not** both be active as default routes simultaneously
or they fight over routing and the MCP server may connect to the wrong interface or lose the connection
mid-session.

| Interface | IP | Role |
|---|---|---|
| `wlan0` | DHCP from home router (assign static lease) | **Primary — daily operation** |
| `eth0` | `192.168.0.250` (static) | **Fallback — initial setup, recovery only** |

**Correct NetworkManager setup on the Pi:**

```bash
# Check current routes
ip route show

# Give WiFi higher priority (lower metric = preferred)
nmcli connection modify "YourWiFiSSID" ipv4.route-metric 100
nmcli connection modify "Wired connection 1" ipv4.route-metric 200
nmcli connection up "YourWiFiSSID"

# Verify: default route should now point to wlan0
ip route show default
# Expected: default via <router_ip> dev wlan0 proto dhcp metric 100
```

Once set, the metric persists across reboots. When you need Ethernet for recovery, plug in the cable —
it will be reachable at `192.168.0.250` but won't hijack the default route.

**Assign a static DHCP lease for WiFi:**

On your router, find the Raspbot Pi 5 MAC address (`ip link show wlan0` on the Pi) and assign it a
fixed IP — e.g. `192.168.0.105`. This avoids hunting for a changing DHCP IP each session.

---

## MCP Server Configuration

Set the robot IP via environment variable before starting the server:

```powershell
# Windows (PowerShell) — WiFi IP, primary
$env:YAHBOOM_IP = "192.168.0.105"

# Ethernet fallback (recovery only) — still reachable as FALLBACK, not primary
$env:YAHBOOM_FALLBACK_IP = "192.168.0.250"

uv run python -m yahboom_mcp.server --mode dual --port 10792
```

The `ROS2Bridge` tries `YAHBOOM_IP` first, then `YAHBOOM_FALLBACK_IP` if the primary fails.

```bash
# Or permanently in your environment / .env file:
YAHBOOM_IP=192.168.0.105
YAHBOOM_FALLBACK_IP=192.168.0.250
YAHBOOM_BRIDGE_PORT=9090
```

---

## Finding the Robot's WiFi IP

If you haven't assigned a static DHCP lease yet:

- **Router DHCP table:** Look for device named `raspberrypi`.
- **OLED display:** If the screen is working, it shows the current IP on boot.
- **nmap scan:** `nmap -sn 192.168.0.0/24` — look for the Pi's MAC prefix.
- **SSH via Ethernet first:** `ssh pi@192.168.0.250` → `ip addr show wlan0` → note the `inet` address.

---

## ROSBridge at Boot

ROSBridge must be running on the Pi before the MCP server can connect.

**One-time setup (run on the Pi):**

```bash
# Install rosbridge (if not already in yahboomcar image)
sudo apt install ros-humble-rosbridge-suite

# Create systemd service so it starts automatically
cat > ~/.config/systemd/user/rosbridge.service << 'EOF'
[Unit]
Description=ROS 2 ROSBridge WebSocket
After=network.target

[Service]
ExecStart=/bin/bash -c 'source /opt/ros/humble/setup.bash && source ~/yahboomcar_ws/install/setup.bash && ros2 launch rosbridge_server rosbridge_websocket_launch.xml'
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user enable rosbridge
systemctl --user start rosbridge
```

**Or start manually for a single session:**

```bash
source /opt/ros/humble/setup.bash
source ~/yahboomcar_ws/install/setup.bash
ros2 launch rosbridge_server rosbridge_websocket_launch.xml
```

**If running inside Docker (yahboom_ros2 container):**

```bash
docker exec yahboom_ros2 bash -c \
  'source /opt/ros/humble/setup.bash && source /root/yahboomcar_ws/install/setup.bash && \
   ros2 launch rosbridge_server rosbridge_websocket_launch.xml &'
```

---

## Verifying the Connection

```bash
# From Windows/PC — check ROSBridge port is open on the Pi
Test-NetConnection -ComputerName 192.168.0.105 -Port 9090

# From the Pi — check topics are publishing
ros2 topic list
ros2 topic echo /imu/data --once
ros2 topic echo /battery_state --once

# From the MCP server health endpoint (once server is running)
curl http://localhost:10792/api/v1/health
# Expected: { "status": "ok", "connected": true, ... }
```

---

## Troubleshooting

**Ping works but ROSBridge won't connect:**
- Check `ros2 topic list` on the Pi — if empty, bringup isn't running.
- Check firewall: `sudo ufw status` on the Pi. Port 9090 must be open.
- Check the docker container is running: `docker ps | grep yahboom_ros2`.

**Server connects then drops repeatedly:**
- Likely the eth/wifi route fight. Fix with the NetworkManager metric commands above.
- Check `ip route show` on the Pi during a drop — if `eth0` becomes default, that's the cause.

**Connected on Ethernet, WiFi not working:**
- On the Pi: `nmcli connection show` — confirm the WiFi profile exists and is "activated".
- `nmcli device wifi list` — check SSID is visible.
- `nmcli connection up "YourWiFiSSID"` to force it up.

**IP changed after router restart:**
- Assign a static DHCP lease on the router for the Pi's wlan0 MAC.
- Or set a static IP directly on the Pi: `nmcli connection modify "YourWiFiSSID" ipv4.addresses "192.168.0.105/24" ipv4.method manual`.
