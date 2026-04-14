import json
import logging
import os
import time
from typing import Any

from pydantic import BaseModel

logger = logging.getLogger("yahboom-mcp.operations.trajectory")


class TrajectoryPoint(BaseModel):
    timestamp: float
    x: float
    y: float
    z: float
    heading: float


class TrajectoryManager:
    """
    Manages recording and playback of robot trajectories.
    """

    def __init__(self, data_dir: str = "data/trajectories"):
        self.data_dir = data_dir
        self.active_recording: list[TrajectoryPoint] = []
        self.is_recording = False

        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def start_recording(self):
        self.active_recording = []
        self.is_recording = True
        logger.info("Started recording trajectory")

    def add_point(self, x: float, y: float, z: float, heading: float):
        if self.is_recording:
            self.active_recording.append(
                TrajectoryPoint(timestamp=time.time(), x=x, y=y, z=z, heading=heading)
            )

    def stop_recording(self, name: str) -> str | None:
        if not self.is_recording:
            return None

        self.is_recording = False
        filename = f"{name}_{int(time.time())}.json"
        filepath = os.path.join(self.data_dir, filename)

        with open(filepath, "w") as f:
            json.dump([p.dict() for p in self.active_recording], f, indent=2)

        logger.info(f"Trajectory saved to {filepath}")
        return filepath

    def list_trajectories(self) -> list[str]:
        return [f for f in os.listdir(self.data_dir) if f.endswith(".json")]

    def load_trajectory(self, filename: str) -> list[dict[str, Any]]:
        filepath = os.path.join(self.data_dir, filename)
        if not os.path.exists(filepath):
            return []

        with open(filepath) as f:
            return json.load(f)
