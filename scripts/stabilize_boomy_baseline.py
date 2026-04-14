import sys
import time

from yahboom_mcp.core.ssh_bridge import SSHBridge

ROBOT_IP = "192.168.0.250"
RETRIES = 20
DELAY = 10

print(f"--- BOOMY STABILIZATION: WAITING FOR CLEAN HEARTBEAT ({ROBOT_IP}) ---")

bridge = SSHBridge(ROBOT_IP, "pi", "yahboom")

connected = False
for i in range(RETRIES):
    try:
        bridge.connect()
        connected = True
        print(f"\n[SUCCESS] Boomy SSH Link Established (Attempt {i + 1}).")
        break
    except Exception:
        print(".", end="", flush=True)
        time.sleep(DELAY)

if not connected:
    print("\n[ERROR] Boomy heartbeat failed to return. Substrate isolated.")
    sys.exit(1)

try:
    print("\n--- BASELINE KERNEL AUDIT ---")
    out, _, _ = bridge.execute("cat /proc/cmdline")
    print(f"Original Cmdline: {out}")

    # We apply the quirk even if already there, ensuring a clean single line
    print("\n--- HARDENING KERNEL COMMAND LINE (UAS DISALED) ---")
    cmdline_path = "/boot/firmware/cmdline.txt"

    # Get current file content cleanly
    out, _, _ = bridge.execute(f"cat {cmdline_path}")
    content = out.replace("\n", " ").replace("\r", " ").strip()

    # Remove existing quirks first to avoid duplicates
    parts = content.split(" ")
    parts = [p for p in parts if "usb-storage.quirks" not in p]
    new_cmdline = f"usb-storage.quirks=0bda:9210:u {' '.join(parts)}"

    print(f"New Cmdline: {new_cmdline}")
    bridge.sudo_execute(f'echo "{new_cmdline}" | sudo tee {cmdline_path}')

    print("\nBOOMY BASELINE STABILIZED.")
    print("YOU MAY NOW HOT-PLUG SSD #2 (Gently/Firmly).")

    bridge.close()

except Exception as e:
    print(f"Stabilization Error: {e!s}")
    bridge.close()
    sys.exit(1)
