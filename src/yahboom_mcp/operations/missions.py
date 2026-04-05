import asyncio
import logging
import time
from typing import Dict, Any, Optional
from .lightstrip import execute as led_execute
from .display import execute as display_execute
from .voice import execute as voice_execute
from ..core.ros2_bridge import ROS2Bridge

logger = logging.getLogger(__name__)


class MissionManager:
    _instance: Optional["MissionManager"] = None

    def __init__(self, ros_bridge: ROS2Bridge):
        self.ros_bridge = ros_bridge
        self.active_mission: Optional[asyncio.Task] = None
        self.mission_id: Optional[str] = None
        self.status: str = "idle"
        self.progress: int = 0
        self.logs: list[str] = []
        self.start_time: float = 0
        self.last_error: Optional[str] = None
        self._safety_active: bool = False

    @classmethod
    def get_instance(cls, ros_bridge: Optional[ROS2Bridge] = None) -> "MissionManager":
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

    def get_status(self) -> Dict[str, Any]:
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

    async def _morning_briefing_mission(self):
        try:
            self._add_log("Fetching news and sensor briefing...")
            self.progress = 20
            await asyncio.sleep(2)

            # Simulated info
            briefing = "Today is sunny. Your battery is at 95 percent. The robot fleet is online."
            self._add_log("Broadcasting Audio Briefing...")
            await voice_execute("say", param1=briefing)

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


async def execute(action: str, mission_id: Optional[str] = None):
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
