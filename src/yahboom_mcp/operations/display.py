from fastmcp import Context
import logging
import time

logger = logging.getLogger("yahboom-mcp.operations.display")

async def execute(
    ctx: Context | None = None,
    operation: str = "",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Execute OLED/LCD Display operations via SSH I2C Bridge.
    Supported Ops:
    Supported Ops:
      write         → Write text (param1: text, param2: line_num, payload.driver: ssd1306|sh1106|st7789|ili9486)
      clear         → Clear the display
      all           → Show high-density system dashboard (IP/CPU/RAM/Temp)
      get_status    → Returns active/detected status (0x3c/0x3d/SPI)
    """
    correlation_id = ctx.correlation_id if ctx else "manual-execution"
    logger.info(f"Display: {operation}", extra={"correlation_id": correlation_id})

    from ..state import _state
    ssh = _state.get("ssh_bridge")

    if not ssh or not ssh.connected:
        return {
            "success": False,
            "operation": operation,
            "error": "SSH bridge not connected",
            "status": "offline"
        }

    if operation == "write":
        text = str(param1) if param1 else ""
        line = int(param2) if param2 else 0
        driver_type = payload.get("driver", "ssd1306") if payload else "ssd1306"
        
        import base64
        script = f"""
try:
    from luma.core.render import canvas
    from PIL import ImageFont
    
    if "{driver_type}" == "ili9486":
        from luma.core.interface.serial import spi
        from luma.lcd.device import ili9486
        serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
        device = ili9486(serial, width=480, height=320)
        font_size = 32
    else:
        from luma.core.interface.serial import i2c
        from luma.oled.device import {driver_type}
        serial = i2c(port=1, address=0x3c)
        device = {driver_type}(serial)
        font_size = 12

    with canvas(device) as draw:
        font = ImageFont.load_default()
        draw.text((0, {line}*font_size), "{text}", fill="white", font=font)
    print("VERIFIED")
except Exception as e:
    print(f"ERROR: {{e}}")
"""
        encoded_script = base64.b64encode(script.encode()).decode()
        shell_cmd = f"python3 -c \"import base64; exec(base64.b64decode('{encoded_script}').decode())\""
        out, err, code = ssh.execute(shell_cmd)
        verified = "VERIFIED" in out
        result = {"success": verified, "status": "applied" if verified else "failed", "log": out if "ERROR" in out else ""}

    elif operation == "scroll":
        text = str(param1) if param1 else "YAHBOOM ROS 2 BRIDGE ACTIVE"
        import base64
        # Background scrolling script using nohup to prevent blocking
        script = f"""
import Adafruit_SSD1306
import time
from PIL import Image, ImageDraw, ImageFont
disp = Adafruit_SSD1306.SSD1306_128_64(rst=None, i2c_bus=1)
disp.begin()
width, height = disp.width, disp.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)
font = ImageFont.load_default()
text = "{text}"
w, h = draw.textsize(text, font=font)
x = width
while True:
    draw.rectangle((0,0,width,height), outline=0, fill=0)
    draw.text((x, 32), text, font=font, fill=255)
    disp.image(image)
    disp.display()
    x -= 4
    if x < -w: x = width
    time.sleep(0.05)
"""
        encoded_script = base64.b64encode(script.encode()).decode()
        # Kill any existing scroll processes first
        ssh.execute("pkill -f 'import base64; exec(base64.b64decode' || true")
        # Run in background via nohup
        bg_cmd = f"nohup python3 -c \"import base64; exec(base64.b64decode('{encoded_script}').decode())\" > /dev/null 2>&1 &"
        ssh.execute(bg_cmd)
        result = {"success": True, "status": "scrolling"}

    elif operation == "all":
        driver_type = payload.get("driver", "ssd1306") if payload else "ssd1306"
        import base64
        # High-density dashboard script
        script = f"""
import psutil, subprocess, time
from luma.core.render import canvas
from PIL import ImageFont

if "{driver_type}" == "ili9486":
    from luma.core.interface.serial import spi
    from luma.lcd.device import ili9486
    serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25)
    device = ili9486(serial, width=480, height=320)
    hi_res = True
else:
    from luma.core.interface.serial import i2c
    from luma.oled.device import {driver_type}
    serial = i2c(port=1, address=0x3c)
    device = {driver_type}(serial)
    hi_res = False

with canvas(device) as draw:
    f_title = ImageFont.load_default() # Scaling later
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    temp = 0
    try: temp = float(open('/sys/class/thermal/thermal_zone0/temp').read())/1000
    except: pass
    ip = subprocess.check_output(['hostname', '-I']).decode().split()[0]
    
    if hi_res:
        draw.text((20, 10), "BOOMY SYSTEM HUB", fill="white")
        draw.rectangle((20, 50, 460, 310), outline="white", fill="black")
        draw.text((40, 70), f"CPU: {{cpu}}%", fill="white")
        draw.rectangle((150, 75, 150 + (cpu*2), 90), fill="white")
        draw.text((40, 110), f"RAM: {{ram}}%", fill="white")
        draw.rectangle((150, 115, 150 + (ram*2), 130), fill="white")
        draw.text((40, 150), f"TEMP: {{temp}}C", fill="white")
        draw.text((40, 190), f"IP: {{ip}}", fill="white")
        # Avatar placeholder
        draw.ellipse((300, 180, 420, 300), outline="white")
        draw.text((320, 220), "FACE", fill="white")
    else:
        draw.text((0, 0), f"IP: {{ip}}", fill="white")
        draw.text((0, 15), f"CPU: {{cpu}}%", fill="white")
        draw.text((0, 30), f"RAM: {{ram}}%", fill="white")
        draw.text((0, 45), f"TEMP: {{temp}}C", fill="white")
    
    print("VERIFIED")
"""
        encoded_script = base64.b64encode(script.encode()).decode()
        ssh.execute(f"python3 -c \"import base64; exec(base64.b64decode('{encoded_script}').decode())\"")
        result = {"success": True}

    elif operation == "clear":
        # Kill scrolling if active
        ssh.execute("pkill -f 'import base64; exec(base64.b64decode' || true")
        py_cmd = "import Adafruit_SSD1306; disp = Adafruit_SSD1306.SSD1306_128_64(rst=None, i2c_bus=1); disp.begin(); disp.clear(); disp.display()"
        ssh.execute(f"python3 -c \"{py_cmd}\"")
        result = {"success": True}

    elif operation == "get_status":
        # Check I2C bus 1 for common OLED/LCD addresses
        i2c_out, _, _ = ssh.execute("i2cdetect -y 1")
        oled_active = "3c" in i2c_out
        result = {
            "active": oled_active, 
            "addr_map": {
                "ssd1306": "3c" if oled_active else None,
                "sh1106": "3c" if oled_active else None,
                "st7789": "SPI"  # LCD hats are often SPI based
            }
        }

    else:
        result = {"error": f"Unknown display operation: {operation}"}

    return {
        "success": result.get("success", False) if "error" not in result else False,
        "operation": operation,
        "status": result.get("status", "unknown"),
        "log": result.get("log", ""),
        "result": result,
        "timestamp": time.time(),
        "correlation_id": correlation_id,
    }
