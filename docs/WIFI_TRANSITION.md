# 📶 Boomy WiFi Transition Guide (v1.0.0)

This guide documents the procedure for switching Boomy (Yahboom Raspbot v2) from a tethered Ethernet connection to its native Access Point (AP) mode for field operations.

## 📋 Prerequisites
- **Ethernet Cable**: Required for initial configuration.
- **Diagnostics Dashboard**: Ensure `yahboom-mcp` is running in `dual` mode.
- **Default SSID**: `Yahboom_XXXX`
- **Default Password**: `yahboom`

## 🚀 Transition Steps

### 1. Initial Access (Ethernet)
Ensure Boomy is reachable over Ethernet at the default static IP:
- **IP**: `192.168.0.250`
- **Command**: `ping 192.168.0.250`

### 2. Identify WiFi Credentials
Login to Boomy via the **Diagnostic Shell** or standard SSH:
```bash
# Check WiFi interface status
nmcli device status
# List available connections
nmcli connection show
```
> [!NOTE]
> Yahboom robots typically broadcast an AP named `Yahboom_` followed by a unique identifier.

### 3. Network Handoff
1. **Connect PC**: Switch your workstation/laptop WiFi to the `Yahboom_XXXX` network.
2. **Unplug Ethernet**: Disconnect the physical cable from the Raspberry Pi 5.
3. **Internal IP**: In AP mode, the robot gateway is typically at `192.168.1.1`.

### 4. Update MCP Environment
On your workstation, update the environment variable to point to the new AP gateway:

**PowerShell:**
```powershell
$env:YAHBOOM_IP = "192.168.1.1"
# or
[System.Environment]::SetEnvironmentVariable("YAHBOOM_IP", "192.168.1.1", "User")
```

**Bash:**
```bash
export YAHBOOM_IP=192.168.1.1
```

### 5. Verify via Boomy Insight
1. Restart the `yahboom-mcp` server.
2. Navigate to [http://localhost:10893/diagnostics](http://localhost:10893/diagnostics).
3. Use the **Diagnostic Shell** to run `ip a` and verify the `wlan0` address is `192.168.1.1`.

## ⚠️ Troubleshooting
- **No AP Visible**: Use the Ethernet connection to run `sudo systemctl restart create_ap` or check `hostapd` logs.
- **Connection Refused**: Ensure the PC is on the *same* `192.168.1.x` subnet.
