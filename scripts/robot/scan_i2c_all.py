import re
import subprocess


def scan_i2c():
    for bus_idx in range(11):
        try:
            print(f"Scanning Bus {bus_idx}...")
            # Use -y to assume yes and not hang
            result = subprocess.run(
                ["sudo", "i2cdetect", "-y", str(bus_idx)],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                # Check for any address (looking for hex patterns like 2b)
                addresses = re.findall(r"[0-9a-f]{2}", result.stdout)
                # Filter out the headers (00, 10, etc.)
                found = [
                    addr
                    for addr in addresses
                    if addr not in ["00", "10", "20", "30", "40", "50", "60", "70"]
                ]
                if found:
                    print(f"  Found devices on Bus {bus_idx}: {found}")
                else:
                    print(f"  No devices on Bus {bus_idx}")
            else:
                print(f"  Bus {bus_idx} command failed.")
        except subprocess.TimeoutExpired:
            print(f"  Bus {bus_idx} scan timed out.")
        except Exception as e:
            print(f"  Bus {bus_idx} error: {e}")


if __name__ == "__main__":
    scan_i2c()
