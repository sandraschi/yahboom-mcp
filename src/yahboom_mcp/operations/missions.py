import asyncio
import logging
import time
from typing import Any, Optional

from .. import fail_response
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
                raise ValueError("MissionManager requires a ROS2Bridge for the first initialization")
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
        elif mission_id in ("explore", "map", "explore_and_map"):
            self.active_mission = asyncio.create_task(self._explore_and_map_mission())
        elif mission_id in ("boomy_draw", "draw_floor"):
            self.active_mission = asyncio.create_task(self._boomy_draw_mission())
        elif mission_id in ("boomy_talkbot", "talkbot"):
            self.active_mission = asyncio.create_task(self._boomy_talkbot_mission())
        else:
            self.status = "error"
            self.last_error = f"Unknown mission ID: {mission_id}"
            self._add_log(f"Error: {self.last_error}")
            return fail_response(self.last_error)

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

    def _lidar_available(self) -> bool:
        """Check if LIDAR (/scan) data is actually publishing."""
        scan = self.ros_bridge.state.get("scan") or {}
        return bool(scan.get("obstacles"))  # non-empty obstacles dict = live LIDAR

    def _lidar_front_obstructed(self, threshold: float = 0.30) -> bool:
        """Check LIDAR front/front_left/front_right sectors. False when LIDAR absent."""
        scan = self.ros_bridge.state.get("scan") or {}
        obstacles = scan.get("obstacles") or {}
        for sector in ("front", "front_left", "front_right"):
            dist = obstacles.get(sector)
            if dist is not None and dist < threshold:
                return True
        return False

    async def _sense_obstacle(self) -> bool:
        """
        Returns True if obstacle detected within threshold.
        Checks ultrasonic (always available) + LIDAR front sectors (gracefully degraded).
        """
        # 1. Ultrasonic — primary, always available
        sonar = self.ros_bridge.state.get("ir_proximity", 1.0)
        if isinstance(sonar, (int, float)) and sonar < 0.20:
            return True

        # 2. LIDAR front sectors — optional, skipped if not mounted
        if self._lidar_available():
            return self._lidar_front_obstructed(threshold=0.30)

        return False

    async def _avoid_obstacle(self) -> bool:
        """
        Execute a Tangent-Pivot Avoidance maneuver with post-avoidance safety creep.
        1. Stop. 2. Sound alert. 3. Pivot 45°. 4. Move to bypass. 5. Re-pivot.
        6. Safety creep — verify forward clearance before declaring success.

        Returns True if obstacle cleared, False if still blocked.
        """
        self._add_log("🛡️ BENNY ALERT: Executing Tangent Avoidance...")
        # 1. Stop
        await self.ros_bridge.publish_velocity(0.0, 0.0)

        # 2. Alert
        await led_execute(None, operation="set", param1=100, param2=0, param3=0)  # Flash Red
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

        # 6. Safety creep — verify forward path before full resume
        self._add_log("🛡️ Safety creep: verifying forward clearance...")
        creep_clear = True
        await self.ros_bridge.publish_velocity(linear_x=0.08, angular_z=0.0)
        for _ in range(8):  # 800ms slow creep with active checking
            await asyncio.sleep(0.1)
            if await self._sense_obstacle():
                self._add_log("🛡️ Obstacle STILL present after avoidance!")
                creep_clear = False
                break
        await self.ros_bridge.publish_velocity(0.0, 0.0)

        if creep_clear:
            await led_execute(None, operation="set", param1=0, param2=0, param3=100)  # Resume Blue
        else:
            await led_execute(None, operation="set", param1=100, param2=0, param3=0)  # Stay red
        return creep_clear

    async def stop_mission(self):
        if self.active_mission:
            self.active_mission.cancel()
            self.status = "aborted"
            self._add_log("Mission manually aborted.")
            return {"success": True}
        return fail_response("No active mission")

    def get_status(self) -> dict[str, Any]:
        return {
            "mission_id": self.mission_id,
            "status": self.status,
            "progress": self.progress,
            "logs": self.logs,
            "uptime": round(asyncio.get_event_loop().time() - self.start_time, 1) if self.start_time > 0 else 0,
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
            await display_execute(None, operation="scroll", param1="!!! PATROL ACTIVE !!!")
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
                avoid_attempts = 0
                while movement_time < 2.0:
                    await self._check_critical_safety()
                    if await self._sense_obstacle():
                        cleared = await self._avoid_obstacle()
                        if not cleared:
                            avoid_attempts += 1
                            if avoid_attempts >= 2:
                                self._add_log(
                                    f"⚠️ Quadrant {i}: obstacle persistent after {avoid_attempts} attempts — diverting."
                                )
                                # Try opposite turn to find clear path
                                await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=-0.8)
                                await asyncio.sleep(1.5)
                                await self.ros_bridge.publish_velocity(0.0, 0.0)
                            else:
                                self._add_log(f"Resuming Quadrant {i} movement (avoid attempt {avoid_attempts})...")
                        else:
                            avoid_attempts = 0
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
            await display_execute(None, operation="write", param1="WAKE UP BOOMY!", param2=2)

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

    async def _explore_and_map_mission(self):
        """
        SLAM-based apartment mapping exploration.
        Requires LIDAR (/scan) mounted and slam_toolbox running on the robot.

        Sequence:
          1. Verify LIDAR is available — abort gracefully if not
          2. Launch slam_toolbox async on robot via SSH
          3. Drive boustrophedon (lawnmower) pattern covering the space
          4. Check obstacles with LIDAR + ultrasonic during traversal
          5. After coverage, save the occupancy grid map via SSH
          6. Return to approximate start position
        """
        try:
            # ── 1. LIDAR preflight ────────────────────────────────────────────
            self._add_log("Mapping: checking LIDAR availability...")
            await display_execute(None, operation="scroll", param1="LIDAR CHECK")

            if not self._lidar_available():
                self._add_log("❌ LIDAR not detected. SLAM mapping requires /scan topic.")
                self._add_log("   Mount YDLIDAR X4 (or compatible) and verify ros2 topic list shows /scan.")
                await voice_execute(
                    None,
                    operation="say",
                    param1="LIDAR not found. Cannot map without laser scanner.",
                )
                self.status = "error"
                self.last_error = "LIDAR unavailable: /scan topic not publishing"
                return fail_response("LIDAR not detected. Mount YDLIDAR X4 and verify /scan on the robot.")

            self._add_log("✅ LIDAR detected — proceeding with SLAM mapping.")
            self.progress = 10

            # ── 2. Launch slam_toolbox on robot ──────────────────────────────
            self._add_log("Mapping: launching slam_toolbox async...")
            ssh = getattr(self.ros_bridge, "ssh", None)
            slam_launched = False
            if ssh and ssh.connected:
                slam_cmd = (
                    'docker exec yahboom_ros2_final bash -c "'
                    "source /opt/ros/humble/setup.bash && "
                    "source /root/yahboomcar_ws/install/setup.bash && "
                    "setsid ros2 run slam_toolbox async_slam_toolbox_node "
                    "--ros-args -p odom_frame:=odom -p base_frame:=base_footprint "
                    "-p map_frame:=map -p use_sim_time:=false "
                    '> /tmp/slam_output.log 2>&1 &"'
                )
                await ssh.execute(slam_cmd)
                await asyncio.sleep(3)  # Give slam_toolbox time to initialize
                slam_launched = True
                self._add_log("✅ slam_toolbox async launched on robot.")
            else:
                self._add_log("⚠️ SSH not available — cannot auto-launch slam_toolbox. Start it manually.")
            self.progress = 20

            # ── 3. Boustrophedon exploration ─────────────────────────────────
            self._add_log("Mapping: beginning boustrophedon coverage...")
            await display_execute(None, operation="scroll", param1="MAPPING")
            await voice_execute(None, operation="say", param1="Beginning apartment mapping")

            # Pattern: forward sweep, turn 180°, forward sweep, repeat
            # Each forward sweep: 4.0s at 0.15 m/s (~0.6m)
            # Turning: 0.6 rad/s × π/0.6 ~ 5.2s for 180°
            SWEEP_SECS = 4.0
            TURN_SECS = 5.2
            SWEEPS = 5
            SWEEP_SPEED = 0.15

            for sweep in range(SWEEPS):
                await self._check_critical_safety()

                # Forward sweep
                self._add_log(f"Mapping: sweep {sweep + 1}/{SWEEPS}")
                sweep_time = 0.0
                while sweep_time < SWEEP_SECS:
                    await self._check_critical_safety()
                    if await self._sense_obstacle():
                        cleared = await self._avoid_obstacle()
                        if not cleared:
                            self._add_log("Mapping: obstruction blocking path — widening search.")
                            # Try strafe to find gap (mecanum advantage)
                            await self.ros_bridge.publish_velocity(linear_x=0.0, linear_y=0.15)
                            await asyncio.sleep(1.0)
                            await self.ros_bridge.publish_velocity(0.0, 0.0)
                    await self.ros_bridge.publish_velocity(linear_x=SWEEP_SPEED, angular_z=0.0)
                    await asyncio.sleep(0.1)
                    sweep_time += 0.1

                await self.ros_bridge.publish_velocity(0.0, 0.0)
                self.progress = 20 + int((sweep + 1) / SWEEPS * 60)

                # Turn 180° for next sweep (except after last)
                if sweep < SWEEPS - 1:
                    self._add_log("Mapping: turning for next sweep...")
                    turn_time = 0.0
                    while turn_time < TURN_SECS:
                        await self._check_critical_safety()
                        await self.ros_bridge.publish_velocity(linear_x=0.0, angular_z=0.6)
                        await asyncio.sleep(0.1)
                        turn_time += 0.1
                    await self.ros_bridge.publish_velocity(0.0, 0.0)

            self.progress = 80

            # ── 4. Save the map ──────────────────────────────────────────────
            self._add_log("Mapping: saving occupancy grid...")
            await display_execute(None, operation="scroll", param1="SAVING MAP")

            map_saved = False
            if ssh and ssh.connected and slam_launched:
                save_cmd = (
                    'docker exec yahboom_ros2_final bash -c "'
                    "source /opt/ros/humble/setup.bash && "
                    "mkdir -p /home/pi/maps && "
                    "ros2 run nav2_map_server map_saver_cli "
                    "-f /home/pi/maps/apartment "
                    '--ros-args -p map_subscribe_transient_local:=true"'
                )
                _, err, code = await ssh.execute(save_cmd)
                if code == 0:
                    map_saved = True
                    self._add_log("✅ Map saved to /home/pi/maps/apartment (.pgm + .yaml)")
                else:
                    self._add_log(f"⚠️ Map save exit code {code}: {err}")
            else:
                self._add_log("⚠️ SSH unavailable — map not saved. Run map_saver_cli manually.")

            self.progress = 90

            # ── 5. Return to start ──────────────────────────────────────────
            self._add_log("Mapping: returning to start position...")
            await voice_execute(None, operation="say", param1="Mapping complete. Returning home.")
            await self.ros_bridge.publish_velocity(linear_x=-0.12, angular_z=0.0)
            await asyncio.sleep(2.0)
            await self.ros_bridge.publish_velocity(0.0, 0.0)

            # ── Complete ──────────────────────────────────────────────────────
            self._add_log("✅ Apartment mapping complete!")
            await led_execute(None, operation="set", param1=0, param2=80, param3=40)
            status_msg = f"Mapping {'saved' if map_saved else 'completed (map NOT saved)'}."
            self.status = "completed"
            self.progress = 100
            await display_execute(None, operation="write", param1="MAP  DONE", param2=2)
            return {"success": True, "map_saved": map_saved, "message": status_msg}

        except asyncio.CancelledError:
            self._add_log("Mapping mission cancelled.")
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            raise
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)
            self._add_log(f"Mapping error: {e}")
            await self.ros_bridge.publish_velocity(0.0, 0.0)
            return fail_response(str(e))

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

    async def _boomy_draw_mission(self):
        from ..operations import demo_showcase

        try:
            self._add_log("Starting Boomy floor-draw demo")
            self.progress = 10
            result = await demo_showcase.execute("draw", pattern="smiley", skip_color_swap_pause=True)
            while True:
                st = await demo_showcase.execute("draw_status")
                self.progress = min(95, self.progress + 5)
                if st.get("status") in ("completed", "error", "stopped", "cancelled"):
                    break
                if st.get("running") is False and st.get("status") != "running":
                    break
                await asyncio.sleep(0.5)
            self.progress = 100
            self.status = "completed" if result.get("success") else "error"
            self._add_log("Draw demo finished")
        except asyncio.CancelledError:
            await demo_showcase.execute("draw_stop")
            raise
        except Exception as e:
            self.status = "error"
            self.last_error = str(e)

    async def _boomy_talkbot_mission(self):
        from ..operations import demo_showcase

        try:
            self._add_log("Starting Boomy talkbot demo")
            self.progress = 10
            await demo_showcase.execute(
                "talkbot",
                max_turns=2,
                use_speech_mcp=False,
                scripted_user_lines=["My name is Alex", "Can you draw?"],
            )
            while True:
                st = await demo_showcase.execute("talkbot_status")
                self.progress = min(95, self.progress + 5)
                if st.get("status") in ("completed", "error", "stopped", "cancelled"):
                    break
                if st.get("running") is False:
                    break
                await asyncio.sleep(0.5)
            self.progress = 100
            self.status = "completed"
            self._add_log("Talkbot demo finished")
        except asyncio.CancelledError:
            await demo_showcase.execute("talkbot_stop")
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
    return fail_response("Invalid action")
