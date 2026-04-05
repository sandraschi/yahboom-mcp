import os
from yahboom_mcp.core.ssh_bridge import SSHBridge


def deploy_diagnostic():
    ip = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    ssh = SSHBridge(ip)

    print(f"[*] Connecting to {ip}...")
    if not ssh.connect():
        print("[-] FAILED")
        return

    # 1. Create the diagnostic script on the robot
    # We use a heredoc to write the file
    diag_script = """
import sys
import os
import time

def test_oled():
    print("[OLED] Testing SSD1306_128_32 on i2c_bus=1...")
    try:
        import Adafruit_SSD1306
        from PIL import Image, ImageDraw, ImageFont
        
        # Yahboom parameters from yahboom_oled.py
        disp = Adafruit_SSD1306.SSD1306_128_32(rst=None, i2c_bus=1)
        disp.begin()
        disp.clear()
        disp.display()
        
        width, height = disp.width, disp.height
        image = Image.new('1', (width, height))
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.text((0, 0), "REALITY CHECK", font=font, fill=255)
        draw.text((0, 10), "SOTA v14.0", font=font, fill=255)
        
        disp.image(image)
        disp.display()
        print("[OLED] SUCCESS: Text written to display.")
    except Exception as e:
        print(f"[OLED] FAILED: {e}")

def test_speech():
    print("[SPEECH] Testing Serial Ports...")
    try:
        import serial
        ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyACM0', '/dev/ttyACM1']
        found = False
        for p in ports:
            try:
                with serial.Serial(p, 115200, timeout=1) as ser:
                    ser.write(b"$say,System reality check active#")
                    print(f"[SPEECH] SUCCESS: Sent command to {p}")
                    found = True
                    break
            except Exception as e:
                print(f"[SPEECH] Port {p} failed: {e}")
        if not found:
            print("[SPEECH] FAILED: No serial port available.")
    except Exception as e:
        print(f"[SPEECH] FAILED: {e}")

if __name__ == '__main__':
    test_oled()
    print("-" * 20)
    test_speech()
"""
    # Write to /tmp/diag.py
    ssh.execute(f"cat << 'EOF' > /tmp/diag.py\n{diag_script}\nEOF")

    # 2. Run the diagnostic script
    print("[*] Executing diagnostic on robot...")
    out, err, code = ssh.execute("python3 /tmp/diag.py")
    print("-" * 40)
    print(out)
    if err:
        print(f"STDERR: {err}")
    print("-" * 40)


if __name__ == "__main__":
    deploy_diagnostic()
