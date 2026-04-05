#!/usr/bin/env bash
# =============================================================================
# fix_network_priority.sh
# Set WiFi as the primary interface and Ethernet as fallback on the Pi 5.
# Run ONCE on the Pi via SSH.
#
# Usage:
#   ssh pi@192.168.0.250 'bash -s' < scripts/fix_network_priority.sh
# =============================================================================

set -euo pipefail

echo "=== Raspbot v2 — Network Priority Fix ==="
echo "Setting WiFi (wlan0) as primary, Ethernet (eth0) as fallback"
echo ""

# Show current state
echo "--- Current routing table ---"
ip route show
echo ""

echo "--- Current NetworkManager connections ---"
nmcli connection show
echo ""

# Get the active WiFi SSID
WIFI_CON=$(nmcli -t -f NAME,TYPE,DEVICE connection show --active | grep wifi | head -1 | cut -d: -f1)
ETH_CON=$(nmcli -t -f NAME,TYPE,DEVICE connection show | grep ethernet | head -1 | cut -d: -f1)

if [[ -z "$WIFI_CON" ]]; then
    echo "ERROR: No active WiFi connection found."
    echo "Connect to WiFi first: nmcli device wifi connect <SSID> password <pw>"
    exit 1
fi

echo "WiFi connection profile: '$WIFI_CON'"
echo "Ethernet connection profile: '$ETH_CON'"
echo ""

# Set metrics: WiFi = 100 (lower = higher priority), Ethernet = 200
echo "Setting WiFi metric to 100 (high priority)..."
nmcli connection modify "$WIFI_CON" ipv4.route-metric 100
nmcli connection modify "$WIFI_CON" ipv6.route-metric 100

if [[ -n "$ETH_CON" ]]; then
    echo "Setting Ethernet metric to 200 (low priority / fallback)..."
    nmcli connection modify "$ETH_CON" ipv4.route-metric 200
    nmcli connection modify "$ETH_CON" ipv6.route-metric 200
fi

# Reconnect WiFi to apply new metric
echo "Reconnecting WiFi to apply settings..."
nmcli connection up "$WIFI_CON" || true

echo ""
echo "--- New routing table ---"
ip route show

echo ""
WIFI_IP=$(ip -4 addr show wlan0 | grep inet | awk '{print $2}' | cut -d/ -f1)
echo "=== Done ==="
echo "WiFi IP (wlan0): ${WIFI_IP:-not assigned yet}"
echo "Ethernet remains reachable at 192.168.0.250 as fallback."
echo ""
echo "On Windows, update your MCP server:"
echo "  \$env:YAHBOOM_IP = \"$WIFI_IP\""
echo "  \$env:YAHBOOM_FALLBACK_IP = \"192.168.0.250\""
