import asyncio
import logging
import time
from typing import Any, Optional

from ..core.ros2_bridge import ROS2Bridge
from .display import execute as display_execute
from .lightstrip import execute as led_execute
from .voice import execute as voice_execute

logger = logging.getLogger(__name__)


class MissionManager:
    _instance: Optional["MissionManager"] = None

    def __init__(self, ros_bridge: ROS2Bridge):
        self.ros_bridge = ros_bridge
        self.active_mission: asyncio.Task | None = None
        self.mission_id: str | None = None
        self.status: str = "idle"
        self.progress: int = 0
        self.logs: list[str] = []
        self.start_time: float = 0
        self.last_error: str | None = None
        self._safety_active: bool = False

    @classmethod
    def get_instance(cls, ros_bridge: ROS2Bridge | None = None) -> "MissionManager":
        if cls._instance is None:
            if ros_bridge is None:
                raise ValueError(
                    "MissionManager requires a ROS2Bridge for the first initialization"
                )
            cls._instance = cls(ros_bridge)
        return cls._instance

    def _add_log(self, msg: str):
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {msg}")
        if len(self.logs) > 50:
            self.logs.pop(0)
        logger.info(f"Mission {self.mission_id}: {msg}")

    async def run_mission(self, mission_id: str):
        if self.active_mission and not self.active_mission.done():
            self._add_log(f"Aborting previous mission {self.mission_id}...")
            self.active_mission.cancel()
            try:
                await self.active_mission
            except asyncio.CancelledError:
                pass

        self.mission_id = mission_id
        self.status = "running"
        self.progress = 0
        self.logs = []
        self.start_time = asyncio.get_event_loop().time()
        self.last_error = None

        self._add_log(f"Starting mission: {mission_id.upper()}")

        if mission_id == "patrol":
            self.active_mission = asyncio.create_task(self._patrol_car_mission())
        elif mission_id == "alarm":
            self.active_mission = asyncio.create_task(self._smart_alarm_mission())
        elif mission_id == "briefing":
            self.active_mission = asyncio.create_task(self._morning_briefing_mission())
        elif mission_id == "kaffeehaus":
            self.active_mission = asyncio.create_task(self._kaffeehaus_mission())
        else:
            self.status = "error"
            self.last_error = f"Unknown mission ID: {mission_id}"
            self._add_log(f"Error: {self.last_error}")
            return {"success": False, "error": self.last_error}

        return {"success": True, "mission": mission_id}

    async def _check_critical_safety(self):
        """
        Poll for non-negotiable safety violations (Cliff/User Stop).
        To be called in loops within mission implementations.
        """
        # 1. Cliff Detection (Line Sensors: 0=Void/White)
        line = self.ros_bridge.state.get("line_sensors", [1, 1, 1])
        if line == [0, 0, 0]:
            self._add_log("⚠️ CLIFF DETECTED! Emergency stop engaged.")
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            self.status = "emergency_halt"
            raise asyncio.CancelledError("Cliff safety violation")

        # 2. Physical Button Interrupt
        if self.ros_bridge.state.get("button_pressed", False):
            self._add_log("🔘 Physical button pressed. Aborting mission.")
            from ..server import _state

            sequencer = _state.get("sequencer")
            if sequencer and sequencer.active:
                await sequencer.stop()
            self.status = "aborted"
            raise asyncio.CancelledError("User manual override")

    async def _sense_obstacle(self) -> bool:
        """Returns True if sonar detects an obstacle within 20cm."""
        sonar = self.ros_bridge.state.get("ir_proximity", 1.0)
        return sonar < 0.20  # 20cm threshold for reactive avoidance

    async def _avoid_obstacle(self):
        """
        Execute a Tangent-Pivot Avoidance maneuver.
        1. Stop. 2. Sound alert. 3. Pivot 45°. 4. Move to bypass. 5. Re-pivot.
        """
        self._add_log("🛡️ BENNY ALERT: Executing Tangent Avoidance...")
        # 1. Stop
        await self.ros_bridge.publish_velocity(0.0, 0.0)

        # 2. Alert
        await led_execute(
            None, operation="set", param1=100, param2=0, param3=0
        )  # Flash Red
        await voice_execute(None, operation="say", param1="PARDON")
        await asyncio.sleep(1)

        # 3. Pivot 45° (approx 0.8 rad/s for 1s)
        self._add_log("🛡️ Pivoting to bypass tangent...")
        await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.8)
        await asyncio.sleep(1.0)
        await self.ros_bridge.publish_velocity(0.0, 0.0)

        # 4. Move forward to bypass
        self._add_log("🛡️ Bypassing obstacle...")
        await self.ros_bridge.publish_velocity(linear_x=0.15, angular_z=0.0)
        await asyncio.sleep(1.5)
        await self.ros_bridge.publish_velocity(0.0, 0.0)

        # 5. Counter-Pivot to resume heading
        self._add_log("🛡️ Resuming patrol heading...")
        await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=-0.8)
        await asyncio.sleep(1.0)
        await self.ros_bridge.publish_velocity(0.0, 0.0)

        await led_execute(
            None, operation="set", param1=0, param2=0, param3=100
        )  # Resume Blue

    async def stop_mission(self):
        if self.active_mission:
            self.active_mission.cancel()
            self.status = "aborted"
            self._add_log("Mission manually aborted.")
            return {"success": True}
        return {"success": False, "error": "No active mission"}

    def get_status(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "status": self.status,
            "progress": self.progress,
            "logs": self.logs,
            "uptime": round(asyncio.get_event_loop().time() - self.start_time, 1)
            if self.start_time > 0
            else 0,
            "last_error": self.last_error,
        }

    # --- Mission Implementations ---

    async def _patrol_car_mission(self):
        try:
            self._add_log("Engaging police strobe (LED mode 1)...")
            await led_execute(
                None,
                operation="set",
                param1=255,
                param2=0,
                param3=0,
                payload={"mode": 1},
            )
            self.progress = 10

            self._add_log("Displaying PATROL metadata...")
            await display_execute(
                None, operation="scroll", param1="!!! PATROL ACTIVE !!!"
            )
            self.progress = 20

            self._add_log("Triggering 🔊 Siren Alert...")
            await voice_execute(None, operation="play", param1=1)
            self.progress = 30
            await asyncio.sleep(2)

            # Patrol Square
            for i in range(1, 5):
                await self._check_critical_safety()
                self._add_log(f"Moving to Quadrant {i}...")

                # Check safety and obstacles during movement
                movement_time = 0
                while movement_time < 2.0:
                    await self._check_critical_safety()
                    if await self._sense_obstacle():
                        await self._avoid_obstacle()
                        self._add_log(f"Resuming Quadrant {i} movement...")

                    await self.ros_bridge.publish_velocity(linear_x=0.2, angular_z=0.0)
                    await asyncio.sleep(0.1)
                    movement_time += 0.1

                self._add_log(f"Analyzing Quadrant {i} (Capturing)...")
                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.0)
                await asyncio.sleep(1)

                self._add_log("Pivoting 90° for next quadrant...")
                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.8)
                await asyncio.sleep(1.5)
                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.0)

                self.progress = 30 + (i * 15)

            self._add_log("Patrol mission completed. Returning to idle.")
            await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.0)
            await led_execute(None, operation="off")
            await display_execute(None, operation="clear")
            self.status = "completed"
            self.progress = 100

        except asyncio.CancelledError:
            self._add_log("Patrol mission cancelled.")
            await self.ros_bridge.move(0.0, 0.0)
            raise
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            self._add_log(f"Critical error: {e}")

    async def _smart_alarm_mission(self):
        try:
            self._add_log("Initiating Sunrise sequence...")
            for i in range(1, 11):
                await self._check_critical_safety()  # Physical button silences alarm
                brightness = i * 25
                # Warm orange to bright yellow
                await led_execute(brightness, int(brightness * 0.8), 0)
                self.progress = i * 10
                await asyncio.sleep(1)

            self._add_log("Displaying Wake Up message...")
            await display_execute(
                None, operation="write", param1="WAKE UP BOOMY!", param2=2
            )

            self._add_log("Broadcasting Morning Greeting...")
            await voice_execute(
                None,
                operation="say",
                param1="Good morning Sandra! It is time to strut your stuff at Cafe Central.",
            )
            self.progress = 100
            self.status = "completed"

        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)

    async def _kaffeehaus_mission(self):
        """
        Kaffeehaus demo routine — ~30 seconds, crowd-legible, no large space needed.
        Sequence:
          1. Greeting fanfare (sound + OLED)
          2. Rainbow spin — slow 360° with rainbow LEDs
          3. Bow — forward/back pulse
          4. Strafe waltz — left/right sway
          5. Obstacle-aware forward creep with blue breathe LEDs
          6. Victory spin + fanfare
          7. Return to idle
        """
        try:
            # ── 1. Greeting ──────────────────────────────────────────────────
            self._add_log("Kaffeehaus: Greeting sequence...")
            await display_execute(None, operation="scroll", param1="SERVUS WIEN!")
            await led_execute(None, operation="set", param1=255, param2=215, param3=0)  # gold
            await voice_execute(None, operation="play", param1=3)  # greeting sound
            await asyncio.sleep(2.0)
            self.progress = 10

            # ── 2. Rainbow spin ──────────────────────────────────────────────
            self._add_log("Kaffeehaus: Rainbow spin...")
            await led_execute(None, operation="pattern", param1="rainbow")
            # One full 360° turn: angular_z=0.6 rad/s × ~10.5 s ≈ 2π rad
            spin_time = 0.0
            while spin_time < 10.5:
                await self._check_critical_safety()
                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.6)
                await asyncio.sleep(0.1)
                spin_time += 0.1
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            await asyncio.sleep(0.3)
            self.progress = 30

            # ── 3. Bow ───────────────────────────────────────────────────────
            self._add_log("Kaffeehaus: Bow...")
            await led_execute(None, operation="set", param1=255, param2=215, param3=0)  # gold
            await self.ros_bridge.publish_velocity(linear_x=0.18, angular_z=0.0)
            await asyncio.sleep(0.5)
            await self.ros_bridge.publish_velocity(linear_x=-0.18, angular_z=0.0)
            await asyncio.sleep(0.5)
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            await asyncio.sleep(0.3)
            self.progress = 45

            # ── 4. Strafe waltz — left/right sway ───────────────────────────
            self._add_log("Kaffeehaus: Waltz sway...")
            await led_execute(None, operation="set", param1=180, param2=0, param3=220)  # violet
            for _ in range(3):
                await self._check_critical_safety()
                # strafe left (linear_y > 0 on mecanum)
                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.0, linear_y=0.18)
                await asyncio.sleep(0.6)
                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.0, linear_y=-0.18)
                await asyncio.sleep(0.6)
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            await asyncio.sleep(0.3)
            self.progress = 60

            # ── 5. Obstacle-aware creep ──────────────────────────────────────
            self._add_log("Kaffeehaus: Forward creep with obstacle check...")
            await led_execute(None, operation="pattern", param1="breathe")
            await display_execute(None, operation="scroll", param1="BOOMY ONLINE")
            creep_time = 0.0
            while creep_time < 2.5:
                await self._check_critical_safety()
                if await self._sense_obstacle():
                    self._add_log("Kaffeehaus: Obstacle detected — holding position.")
                    await self.ros_bridge.publish_velocity(0.0, 0.0)
                    await asyncio.sleep(0.5)
                    creep_time += 0.5
                    continue
                await self.ros_bridge.publish_velocity(linear_x=0.12, angular_z=0.0)
                await asyncio.sleep(0.1)
                creep_time += 0.1
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            await asyncio.sleep(0.3)
            self.progress = 80

            # ── 6. Victory spin + fanfare ────────────────────────────────────
            self._add_log("Kaffeehaus: Victory spin!")
            await led_execute(None, operation="pattern", param1="patrol")
            await voice_execute(None, operation="play", param1=5)  # victory sound
            await display_execute(None, operation="scroll", param1="*** DANKE WIEN ***")
            victory_time = 0.0
            while victory_time < 4.0:
                await self._check_critical_safety()
                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=1.2)
                await asyncio.sleep(0.1)
                victory_time += 0.1
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            self.progress = 95

            # ── 7. Idle ──────────────────────────────────────────────────────
            self._add_log("Kaffeehaus: Demo complete.")
            await led_execute(None, operation="set", param1=0, param2=60, param3=30)  # dim green idle
            await display_execute(None, operation="write", param1="BOOMY  IDLE", param2=2)
            self.status = "completed"
            self.progress = 100

        except asyncio.CancelledError:
            self._add_log("Kaffeehaus mission cancelled.")
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            await led_execute(None, operation="off")
            raise
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            self._add_log(f"Kaffeehaus error: {e}")
            await self.ros_bridge.publish_velocity(0.0, 0.0)

    async def _morning_briefing_mission(self):
        try:
            self._add_log("Fetching news and sensor briefing...")
            self.progress = 20
            await asyncio.sleep(2)

            # Simulated info
            briefing = "Today is sunny. Your battery is at 95 percent. The robot fleet is online."
            self._add_log("Broadcasting Audio Briefing...")
            await voice_execute(None, operation="say", param1=briefing)

            self._add_log("Executing morning stretch...")
            await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.5)
            await asyncio.sleep(1)
            await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=-0.5)
            await asyncio.sleep(1)
            await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.0)

            self.progress = 100
            self.status = "completed"
            self._add_log("Briefing complete.")

        except asyncio.CancelledError:
            raise
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)


async def execute(action: str, mission_id: str | None = None):
    # This will be called from the server, passing the bridge instance
    # The bridge instance should be managed in server.py
    # For now, we will assume singleton is initialized in server.py
    mgr = MissionManager.get_instance()
    if action == "run":
        return await mgr.run_mission(mission_id)
    elif action == "stop":
        return await mgr.stop_mission()
    elif action == "status":
        return mgr.get_status()
    return {"success": False, "error": "Invalid action"}
