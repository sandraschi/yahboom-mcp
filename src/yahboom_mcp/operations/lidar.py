"""
LIDAR portmanteau backend: Yahboom /scan (optional) and Dreame D20 Pro map (optional).

- Yahboom: reads from ROS2Bridge state["scan"] when bridge connected (/scan topic).
- Dreame: reads map/scan from optional DREAME_MAP_URL (e.g. robotics-mcp or dreame-mcp endpoint).
"""

import logging
import os
from typing import Any

logger = logging.getLogger("yahboom-mcp.operations.lidar")


async def execute(
    ctx: Any = None,
    operation: str = "read",
    source: str = "auto",
    param1: str | float | None = None,
    param2: str | float | None = None,
    payload: dict | None = None,
) -> dict:
    """
    Execute LIDAR operations: read (summary), read_raw (yahboom only), read_dreame_map.

    source: yahboom | dreame | auto (try yahboom then dreame).
    """
    correlation_id = getattr(ctx, "correlation_id", None) if ctx else "manual-execution"
    logger.info(
        "LIDAR operation: %s source=%s",
        operation,
        source,
        extra={"correlation_id": correlation_id},
    )

    op_lower = operation.lower().strip()
    src_lower = source.lower().strip()

    try:
        if op_lower == "read":
            return await _read_scan(correlation_id, src_lower)
        if op_lower == "read_raw":
            return await _read_raw_scan(correlation_id, src_lower)
        if op_lower == "read_dreame_map":
            return await _read_dreame_map(correlation_id, param1, payload)
        return {
            "success": False,
            "operation": operation,
            "error": f"Unknown operation: {operation}. Use read, read_raw, or read_dreame_map.",
            "correlation_id": correlation_id,
        }
    except Exception as e:
        logger.error("LIDAR operation failed: %s", e, exc_info=True)
        return {
            "success": False,
            "operation": operation,
            "error": str(e),
            "correlation_id": correlation_id,
        }


async def _read_scan(correlation_id: str, source: str) -> dict:
    """Return obstacle summary (nearest per sector + global nearest)."""
    from ..state import _state

    bridge = _state.get("bridge")
    yahboom_ok = bridge and bridge.connected
    scan = (await bridge.get_sensor_data("scan")) if yahboom_ok else {}

    if source == "dreame":
        return await _read_dreame_map(correlation_id, None, None)

    if source == "auto" and not yahboom_ok:
        dreame_result = await _read_dreame_map(correlation_id, None, None)
        if dreame_result.get("success"):
            return dreame_result
        return {
            "success": False,
            "source": "auto",
            "error": "No LIDAR source available: Yahboom bridge disconnected and Dreame map not configured (set DREAME_MAP_URL).",
            "correlation_id": correlation_id,
        }

    if not yahboom_ok:
        return {
            "success": False,
            "source": "yahboom",
            "error": "Yahboom ROS bridge not connected. LIDAR requires /scan from robot.",
            "correlation_id": correlation_id,
        }

    return {
        "success": True,
        "source": "yahboom",
        "operation": "read",
        "scan": {
            "obstacles": scan.get("obstacles", {}),
            "nearest_m": scan.get("nearest_m"),
            "range_max_m": scan.get("range_max_m"),
            "num_points": scan.get("num_points"),
        },
        "correlation_id": correlation_id,
    }


async def _read_raw_scan(correlation_id: str, source: str) -> dict:
    """Return scan summary; raw ranges are not cached in bridge to save memory."""
    from ..state import _state

    if source == "dreame":
        return await _read_dreame_map(correlation_id, None, None)

    bridge = _state.get("bridge")
    if not bridge or not bridge.connected:
        return {
            "success": False,
            "source": "yahboom",
            "error": "Yahboom ROS bridge not connected.",
            "correlation_id": correlation_id,
        }

    scan = await bridge.get_sensor_data("scan")
    return {
        "success": True,
        "source": "yahboom",
        "operation": "read_raw",
        "scan": {
            "obstacles": scan.get("obstacles", {}),
            "nearest_m": scan.get("nearest_m"),
            "range_max_m": scan.get("range_max_m"),
            "num_points": scan.get("num_points"),
        },
        "note": "Full ranges[] not cached; use scan.obstacles and scan.nearest_m for planning.",
        "correlation_id": correlation_id,
    }


async def _read_dreame_map(
    correlation_id: str, param1: Any, payload: dict | None
) -> dict:
    """Fetch LIDAR/map data from Dreame D20 Pro scan if DREAME_MAP_URL is configured."""
    url = os.environ.get("DREAME_MAP_URL", "").strip()
    if not url:
        return {
            "success": False,
            "source": "dreame",
            "operation": "read_dreame_map",
            "error": "DREAME_MAP_URL not set. Set to robotics-mcp or dreame-mcp map/scan endpoint (e.g. http://localhost:PORT/api/dreame/map).",
            "correlation_id": correlation_id,
        }

    try:
        import httpx

        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.get(url)
            if r.status_code != 200:
                return {
                    "success": False,
                    "source": "dreame",
                    "error": f"Dreame map endpoint returned HTTP {r.status_code}",
                    "correlation_id": correlation_id,
                }
            data = (
                r.json()
                if r.headers.get("content-type", "").startswith("application/json")
                else {"raw": r.text[:2000]}
            )
    except Exception as e:
        logger.debug("Dreame map fetch failed: %s", e)
        return {
            "success": False,
            "source": "dreame",
            "error": str(e),
            "correlation_id": correlation_id,
        }

    return {
        "success": True,
        "source": "dreame",
        "operation": "read_dreame_map",
        "map": data,
        "correlation_id": correlation_id,
    }
