from yahboom_mcp.core.ssh_bridge import SSHBridge

bridge = SSHBridge("192.168.0.250", "pi", "yahboom")
bridge.connect()

print("--- BOOMY ALIVE: HANDSHAKE SUCCESS ---")
out, err, code = bridge.execute("cat /boot/firmware/cmdline.txt")
print(f"Physical Cmdline:\n{out}")

print("\n--- APPLYING QUIRK CORRECTLY ---")
# Force it into a clean, single-line state
content = out.replace("\n", " ").replace("\r", " ").strip()
if "usb-storage.quirks=0bda:9210:u" not in content:
    new_content = f"usb-storage.quirks=0bda:9210:u {content}"
    print(f"New Cmdline: {new_content}")
    bridge.sudo_execute(f'echo "{new_content}" | sudo tee /boot/firmware/cmdline.txt')
    print("CMDLINE UPDATED.")
else:
    print("Quirk already present in file.")

print("\n--- VERIFYING COGNITIVE STACK ---")
out, err, code = bridge.execute("ollama list")
print(f"Ollama Stack:\n{out}")

print("\n--- VERIFYING SSD HARDWARE ---")
out, err, code = bridge.execute("lsblk /dev/sda")
print(f"SSD State (Pre-Reboot):\n{out}")

bridge.close()
print("BOOMY SUBSTRATE REPAIR: COMPLETED.")
