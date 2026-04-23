"""
Layered robot stack probes for /api/v1/health `stack` and driver/ros graph caching.

Order of layers (bottom-up on the Pi, as surfaced to the operator):
  Goliath → robot IP (TCP), SSH session, Pi network/Wi-Fi, Docker engine,
  ROS container, ROS graph inside container, rosbridge WebSocket from this PC.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import shlex
import time
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("yahboom-mcp.stack-probe")

# ─── Driver / ros2 node graph (docker exec … ros2 node list) ─────────────────

_driver_stack_lock = asyncio.Lock()
_driver_stack_cache: dict[str, Any] | None = None
_driver_stack_cache_until: float = 0.0

_stack_overview_lock = asyncio.Lock()
_stack_overview_cache: dict[str, Any] | None = None
_stack_overview_cache_until: float = 0.0


def invalidate_stack_caches() -> None:
    """Clear all stack-related caches (after reconnect, resync, bringup)."""
    global _driver_stack_cache, _driver_stack_cache_until
    global _stack_overview_cache, _stack_overview_cache_until
    _driver_stack_cache = None
    _driver_stack_cache_until = 0.0
    _stack_overview_cache = None
    _stack_overview_cache_until = 0.0


def invalidate_driver_stack_cache() -> None:
    """Backward-compatible alias."""
    invalidate_stack_caches()


async def _tcp_port_open(host: str, port: int, timeout: float = 1.2) -> dict[str, Any]:
    """True if something accepts TCP on host:port from this machine."""
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port),
            timeout=timeout,
        )
    except TimeoutError:
        return {"ok": False, "error": "timeout"}
    except OSError as e:
        return {"ok": False, "error": str(e) or type(e).__name__}
    except Exception as e:
        return {"ok": False, "error": type(e).__name__}
    else:
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        try:
            close_m = getattr(reader, "aclose", None)
            if callable(close_m):
                await close_m()
        except Exception:
            pass
        return {"ok": True, "error": None}


async def _driver_stack_probe_uncached(ssh) -> dict[str, Any]:
    """
    Inspect `ros2 node list` inside YAHBOOM_ROS2_CONTAINER (default yahboom_ros2_final).
    """
    container = (os.environ.get("YAHBOOM_ROS2_CONTAINER") or "yahboom_ros2_final").strip()
    base: dict[str, Any] = {
        "container": container,
        "status": "unknown",
        "matched_nodes": [],
        "rosbridge_node_seen": None,
        "ros_node_line_count": 0,
        "node_lines": None,
        "detail": "",
    }
    if not ssh or not getattr(ssh, "connected", False):
        base["status"] = "ssh_offline"
        base["detail"] = "SSH not connected — cannot read docker ROS graph."
        return base

    cmd = (
        f"docker exec {container} bash -c "
        f"'source /opt/ros/humble/setup.bash; "
        f"source /root/yahboomcar_ws/install/setup.bash; "
        f"ros2 node list 2>/dev/null'"
    )
    try:
        out, err, code = await ssh.execute(cmd)
    except Exception as e:
        base["status"] = "probe_failed"
        base["detail"] = f"SSH exec failed: {e}"
        return base

    lines = [ln.strip() for ln in (out or "").splitlines() if ln.strip()]
    base["node_lines"] = lines
    base["ros_node_line_count"] = len(lines)
    blob = (out or "").lower()

    matched: list[str] = []
    if "mcnamu_driver" in blob:
        matched.append("Mcnamu_driver")
    if "driver_node" in blob:
        matched.append("driver_node")
    base["matched_nodes"] = matched

    base["rosbridge_node_seen"] = "rosbridge_websocket" in blob

    if code != 0 and not lines:
        base["status"] = "probe_failed"
        base["detail"] = (err or "empty node list").strip()[:200] or f"exit {code}"
        return base

    if matched:
        base["status"] = "running"
        rb = "yes" if base["rosbridge_node_seen"] else "no"
        base["detail"] = (
            f"Hardware driver class node(s) present in {container} "
            f"({', '.join(matched)}). rosbridge_websocket in same graph: {rb}."
        )
    else:
        base["status"] = "absent"
        base["detail"] = (
            f"No Mcnamu_driver / driver_node in `ros2 node list` inside {container} "
            f"({len(lines)} nodes). Bringup may be down or still starting."
        )
    return base


async def driver_stack_snapshot(ssh) -> dict[str, Any]:
    """Cached driver-stack probe (TTL YAHBOOM_DRIVER_PROBE_SECS, default 5)."""
    global _driver_stack_cache, _driver_stack_cache_until
    ttl = max(1.0, float(os.environ.get("YAHBOOM_DRIVER_PROBE_SECS", "5")))
    now = time.time()
    async with _driver_stack_lock:
        if _driver_stack_cache is not None and now < _driver_stack_cache_until:
            return _driver_stack_cache
        snap = await _driver_stack_probe_uncached(ssh)
        _driver_stack_cache = snap
        _driver_stack_cache_until = time.time() + ttl
        return snap


def _wifi_parse(iw_out: str) -> dict[str, Any]:
    """Best-effort SSID from `iw dev wlan0 link` output."""
    raw = (iw_out or "").strip()
    low = raw.lower()
    if not raw or "no such device" in low or "nl80211 not found" in low:
        return {"state": "no_wlan", "ssid": None, "raw_preview": None}
    ssid = None
    for line in raw.splitlines():
        s = line.strip()
        if "ssid:" in s.lower():
            idx = s.lower().find("ssid:")
            rest = s[idx + 5 :].strip()
            if rest:
                ssid = rest
                break
    not_linked = "not connected" in low or "no station" in low
    if not_linked:
        st = "disconnected"
    elif ssid or "connected to" in low:
        st = "connected"
    else:
        st = "unknown"
    return {
        "state": st,
        "ssid": ssid,
        "raw_preview": raw[:240] + ("…" if len(raw) > 240 else "") if raw else None,
    }


def _find_alternate_yahboom_container(ps_preview: str, configured: str) -> str | None:
    """If another yahboom* container is Up while the configured name differs, return its name."""
    want = configured.strip().lower()
    for raw_ln in ps_preview.splitlines():
        ln = raw_ln.strip()
        if "\t" not in ln:
            continue
        name, status = ln.split("\t", 1)
        if name.strip().lower() == want:
            continue
        if "yahboom" not in name.lower():
            continue
        low = status.lower()
        if low.startswith("up") or " up " in low:
            return name.strip()
    return None


def _container_state_summary(
    name: str,
    status: str,
    exit_code: Any,
    oom: Any,
    err: str,
) -> str:
    body = f"Container `{name}` — state `{status}`."
    if exit_code is not None:
        body += f" ExitCode={exit_code}."
    if oom:
        body += " OOMKilled=true (host killed the container, often out of memory)."
    if err:
        body += f" Engine error: {err[:200]}"
    return body


_LOG_REDACT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?i)((?:password|passwd|pwd|apikey|api_key|secret|token|client_secret|access_token)\s*[:=]\s*)\S+"
        ),
        r"\1***",
    ),
    (re.compile(r"(?i)(Authorization:\s*Bearer\s+)\S+"), r"\1***"),
    (re.compile(r"(?i)((?:AwsAccessKeyId|AwsSecretAccessKey|SessionToken)\s*[:=]\s*)\S+"), r"\1***"),
)


def _docker_container_name_safe(name: str) -> bool:
    s = name.strip()
    if not s or len(s) > 128:
        return False
    return bool(re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_.-]*$", s))


def _sanitize_docker_logs_preview(raw: str, *, max_chars: int, max_line_chars: int = 480) -> tuple[str, bool]:
    """Redact common secret patterns, cap line length, then cap total size."""
    if not raw or not raw.strip():
        return "", False
    lines_out: list[str] = []
    for line in raw.splitlines():
        if "BEGIN" in line and "PRIVATE KEY" in line:
            lines_out.append("*** [REDACTED: PEM private key block] ***")
            continue
        ln = line[:max_line_chars]
        for pat, repl in _LOG_REDACT_PATTERNS:
            ln = pat.sub(repl, ln)
        lines_out.append(ln)
    text = "\n".join(lines_out)
    truncated = len(text) > max_chars
    if truncated:
        cut = max_chars - 72
        text = text[:cut].rstrip() + "\n... [preview truncated: YAHBOOM_DOCKER_LOGS_MAX_CHARS]"
    return text, truncated


def _sync_restart_loop_flag(ros_container: dict[str, Any]) -> None:
    lf = ros_container.get("lifecycle") or {}
    ros_container["restart_loop"] = lf.get("phase") == "restart_loop"


async def _maybe_attach_docker_logs_preview(
    ssh,
    ros_container: dict[str, Any],
    configured_name: str,
) -> None:
    """When the ROS container is unhealthy, pull `docker logs --tail N` over SSH (size-limited, redacted)."""
    ros_container.setdefault("docker_logs_preview", None)
    ros_container.setdefault("docker_logs_error", None)
    ros_container.setdefault("docker_logs_truncated", False)
    ros_container.setdefault("docker_logs_lines_fetched", 0)

    if not ssh or not getattr(ssh, "connected", False):
        return
    name = configured_name.strip()
    if not _docker_container_name_safe(name):
        ros_container["docker_logs_error"] = "unsafe_or_empty_container_name"
        return

    dst = str(ros_container.get("docker_state") or "").strip().lower()
    if dst == "not_found":
        return

    running = ros_container.get("running")
    lf = ros_container.get("lifecycle") or {}
    in_restart_loop = lf.get("phase") == "restart_loop"

    if running is True and not in_restart_loop:
        return

    lines = max(10, min(200, int(os.environ.get("YAHBOOM_DOCKER_LOGS_TAIL", "80"))))
    max_chars = max(2000, min(64000, int(os.environ.get("YAHBOOM_DOCKER_LOGS_MAX_CHARS", "16000"))))

    cmd = f"docker logs {shlex.quote(name)} --tail {lines} 2>&1"
    try:
        out, err, code = await ssh.execute(cmd)
    except Exception as e:
        logger.warning("docker logs over ssh failed: %s", e)
        ros_container["docker_logs_error"] = str(e)[:240]
        return

    raw = out or ""
    if err:
        raw = f"{raw}\n{err}" if raw else err
    if code != 0 and not (raw or "").strip():
        ros_container["docker_logs_error"] = f"docker_logs_exit_{code}"
        return

    preview, truncated = _sanitize_docker_logs_preview(raw or "", max_chars=max_chars)
    if preview.strip():
        ros_container["docker_logs_preview"] = preview
        ros_container["docker_logs_truncated"] = truncated
        ros_container["docker_logs_lines_fetched"] = len(preview.splitlines())
    else:
        ros_container["docker_logs_preview"] = None
        ros_container["docker_logs_truncated"] = False
        ros_container["docker_logs_lines_fetched"] = 0


def _docker_timestamp_meaningful(ts: Any) -> bool:
    """True if Docker State timestamp is a real clock time (not the API zero placeholder)."""
    if ts is None:
        return False
    s = str(ts).strip()
    if not s:
        return False
    if s.startswith("0001-01-01"):
        return False
    if s.startswith("0000-12-31"):
        return False
    return True


def _apply_container_lifecycle(ros_container: dict[str, Any], *, ssh_connected: bool) -> None:
    """Set `lifecycle` {phase, label, detail} — never started vs ran then exited vs running, etc."""
    if not ssh_connected:
        ros_container["lifecycle"] = {
            "phase": "no_ssh",
            "label": "SSH offline",
            "detail": "Connect the control SSH session to read Docker State on the Pi.",
        }
        return

    running = ros_container.get("running")
    dst = str(ros_container.get("docker_state") or "").strip().lower()
    started = _docker_timestamp_meaningful(ros_container.get("started_at"))
    finished = _docker_timestamp_meaningful(ros_container.get("finished_at"))
    ec = ros_container.get("exit_code")
    name = str(ros_container.get("name") or "container")

    if running is True:
        ros_container["lifecycle"] = {
            "phase": "running",
            "label": "Running now",
            "detail": "Docker has this container’s main process up at probe time.",
        }
        return

    if dst == "not_found":
        ros_container["lifecycle"] = {
            "phase": "not_found",
            "label": "Container name not on this Pi",
            "detail": f"No container named `{name}` — wrong name or different compose project.",
        }
        return

    if dst in ("inspect_error", "inspect_parse_error"):
        ros_container["lifecycle"] = {
            "phase": "unknown",
            "label": "Could not classify",
            "detail": (ros_container.get("summary") or "Docker inspect failed or returned an error string.")[:280],
        }
        return

    if running is None and dst == "unknown":
        ros_container["lifecycle"] = {
            "phase": "unavailable",
            "label": "State unreadable",
            "detail": (ros_container.get("summary") or "No usable State from Docker.")[:280],
        }
        return

    if "restarting" in dst:
        ros_container["lifecycle"] = {
            "phase": "restart_loop",
            "label": "Restart loop (crash loop)",
            "detail": (
                "Docker is in a restart loop: it starts this container, the main process exits, "
                "and Docker tries again. This is not “never started” — read `docker logs` on the Pi "
                "for the repeating error before the exit."
            ),
        }
        return

    if "paused" in dst:
        ros_container["lifecycle"] = {
            "phase": "paused",
            "label": "Paused",
            "detail": "It was started, then `docker pause` froze it — different from exited or never run.",
        }
        return

    if "removing" in dst:
        ros_container["lifecycle"] = {
            "phase": "removing",
            "label": "Removing",
            "detail": "Docker is tearing this container down — transient state.",
        }
        return

    if dst == "created" or dst.startswith("created ("):
        ros_container["lifecycle"] = {
            "phase": "never_started",
            "label": "Never run to completion",
            "detail": "Still in `created` (or no start time) — Docker has not left it running yet; usually run `docker start` once.",
        }
        return

    if "exited" in dst or dst.strip() == "dead" or finished or (started and running is False and ec not in (None,)):
        ros_container["lifecycle"] = {
            "phase": "ran_then_stopped",
            "label": "Started, then exited",
            "detail": "Docker did start this container at least once; the main process later stopped. Use exit code and logs to see why.",
        }
        return

    if started and running is False and "up" not in dst:
        ros_container["lifecycle"] = {
            "phase": "ran_then_stopped",
            "label": "Started, then exited",
            "detail": "Inspect shows a recorded start time but the container is not running — treat as a prior run that stopped.",
        }
        return

    ros_container["lifecycle"] = {
        "phase": "unknown",
        "label": "Unusual state",
        "detail": f"Docker reports `{dst or '?'}` — see `docker inspect {name}` on the Pi if this persists.",
    }


def _attach_container_remediation(ros_container: dict[str, Any], *, not_found: bool) -> None:
    """Populate `remediation_steps` for operators when the ROS container is missing or not running."""
    name = str(ros_container.get("name") or "yahboom_ros2_final")
    steps: list[str] = []
    alt = ros_container.get("alternate_running_container")
    if alt:
        steps.append(
            f"This probe targets `{name}` but `{alt}` is Up — set YAHBOOM_ROS2_CONTAINER to `{alt}` "
            "or rename the compose service to match what the app expects."
        )
    if not_found:
        steps.append("On the Pi (SSH), run `docker ps -a` and pick the Yahboom-related container name.")
        steps.append("Set YAHBOOM_ROS2_CONTAINER to that exact name, then refresh this page.")
        ros_container["remediation_steps"] = steps
        return

    if ros_container.get("running") is True:
        ros_container["remediation_steps"] = steps
        return

    steps.append(f"docker logs --tail 200 {name}    # recent errors (on the Pi over SSH)")
    st = str(ros_container.get("docker_state") or "").lower()
    if "restarting" in st:
        steps.append(
            "Container is in a restart loop — inspect logs for missing USB devices, "
            "bad bind mounts, or ROS launch failures."
        )
    elif "exited" in st or st.strip() == "dead":
        steps.append(f"docker start {name}    # after you fix what the logs show")
        ec = ros_container.get("exit_code")
        if ec == 137 or ros_container.get("oom_killed"):
            steps.insert(
                1,
                "Exit 137 / OOMKilled: free RAM on the Pi or reboot before starting again.",
            )
        elif ec not in (None, 0):
            steps.append(f"Non-zero exit {ec}: check the image entrypoint and ROS bringup in that container.")
    else:
        steps.append(f"docker start {name}    # if this service should be running")

    ros_container["remediation_steps"] = steps


async def _stack_overview_uncached(
    ssh,
    bridge,
    video,
    robot_host: str,
    bridge_port: int,
) -> dict[str, Any]:
    """Run all probes (expensive — call through cached wrapper)."""
    container = (os.environ.get("YAHBOOM_ROS2_CONTAINER") or "yahboom_ros2_final").strip()
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    t_ssh, t_br = await asyncio.gather(
        _tcp_port_open(robot_host, 22),
        _tcp_port_open(robot_host, bridge_port),
    )

    goliath = {
        "robot_ip": robot_host,
        "rosbridge_tcp_port": bridge_port,
        "tcp_ssh_port_22": t_ssh,
        "tcp_rosbridge_port": t_br,
        "summary": (
            "SSH and rosbridge ports reachable from this PC."
            if t_ssh["ok"] and t_br["ok"]
            else (
                "Cannot reach robot TCP endpoints from this PC — check Wi‑Fi / Ethernet / YAHBOOM_IP."
                if not t_ssh["ok"] and not t_br["ok"]
                else (
                    "SSH port closed from here; rosbridge port open."
                    if not t_ssh["ok"] and t_br["ok"]
                    else "SSH open; rosbridge TCP port not accepting (rosbridge down or wrong port)."
                )
            )
        ),
    }

    ros_ws = bool(bridge and getattr(bridge, "ros", None) and bridge.ros.is_connected)
    cmd_vel_ready = bool(bridge and ros_ws and getattr(bridge, "cmd_vel_topic", None) is not None)

    rosbridge_pc = {
        "websocket_to_rosbridge": "connected" if ros_ws else "disconnected",
        "cmd_vel_advertised_on_bridge": cmd_vel_ready,
        "summary": (
            "This app has a live roslibpy session to rosbridge."
            if ros_ws
            else "No WebSocket session — start rosbridge on the robot or fix YAHBOOM_BRIDGE_PORT."
        ),
    }

    video_state = {
        "video_bridge_active": bool(video and getattr(video, "active", False)),
        "summary": (
            "VideoBridge is capturing (ROS topic or local fallback)."
            if video and getattr(video, "active", False)
            else "No active VideoBridge (ROS not up yet or stream not started)."
        ),
    }

    ssh_layer = {
        "paramiko_session": "connected" if ssh and getattr(ssh, "connected", False) else "disconnected",
        "target_host": robot_host,
        "summary": (
            "MCP has an interactive SSH session to the Pi."
            if ssh and getattr(ssh, "connected", False)
            else "SSH not logged in — OLED / docker exec probes from MCP will not run.",
        ),
    }

    pi_host: dict[str, Any] = {
        "hostname": None,
        "primary_ip": None,
        "interfaces_preview": None,
        "wifi": {"state": "unknown", "ssid": None, "raw_preview": None},
        "summary": "Need SSH to read Pi hostname, IPs, and Wi‑Fi.",
    }

    docker_engine: dict[str, Any] = {
        "systemd_active": "unknown",
        "server_version": None,
        "summary": "Need SSH to inspect Docker on the Pi.",
    }

    ros_container: dict[str, Any] = {
        "name": container,
        "running": None,
        "docker_state": "unknown",
        "started_at": None,
        "finished_at": None,
        "exit_code": None,
        "oom_killed": None,
        "error": None,
        "docker_ps_preview": None,
        "remediation_steps": [],
        "alternate_running_container": None,
        "restart_loop": False,
        "docker_logs_preview": None,
        "docker_logs_error": None,
        "docker_logs_truncated": False,
        "docker_logs_lines_fetched": 0,
        "lifecycle": {
            "phase": "no_ssh",
            "label": "SSH offline",
            "detail": "Connect SSH to infer whether the container ever ran on the Pi.",
        },
        "summary": "Need SSH to docker inspect the ROS container.",
    }

    if ssh and getattr(ssh, "connected", False):
        try:
            hn, _, _ = await ssh.execute("hostname 2>/dev/null")
            pi_host["hostname"] = (hn or "").strip() or None
        except Exception as e:
            pi_host["hostname"] = None
            pi_host["hostname_error"] = str(e)

        try:
            ips, _, _ = await ssh.execute("hostname -I 2>/dev/null")
            parts = (ips or "").split()
            pi_host["primary_ip"] = parts[0] if parts else None
            pi_host["all_ips"] = parts[:8] if parts else []
        except Exception:
            pass

        try:
            br, _, _ = await ssh.execute("ip -br addr show 2>/dev/null | head -16")
            pi_host["interfaces_preview"] = (br or "").strip() or None
        except Exception:
            pass

        try:
            iw, _, _ = await ssh.execute("iw dev wlan0 link 2>/dev/null | head -16")
            pi_host["wifi"] = _wifi_parse(iw)
        except Exception:
            pi_host["wifi"] = {"state": "unknown", "ssid": None, "raw_preview": None}

        if pi_host.get("primary_ip") or pi_host.get("hostname"):
            pi_host["summary"] = (
                f"Pi reports hostname {pi_host.get('hostname') or '—'} "
                f"and primary IP {pi_host.get('primary_ip') or '—'}."
            )

        try:
            dact, _, _dcode = await ssh.execute("systemctl is-active docker 2>/dev/null")
            act = (dact or "").strip()
            docker_engine["systemd_active"] = (
                "active" if act == "active" else ("inactive" if act == "inactive" else act or "unknown")
            )
        except Exception:
            docker_engine["systemd_active"] = "unknown"

        try:
            dv, _, _ = await ssh.execute("docker info --format '{{.ServerVersion}}' 2>/dev/null")
            docker_engine["server_version"] = (dv or "").strip() or None
        except Exception:
            pass

        docker_engine["summary"] = f"Docker daemon systemd state: {docker_engine['systemd_active']}" + (
            f", engine {docker_engine['server_version']}." if docker_engine["server_version"] else "."
        )

        try:
            ps_out, _, _ = await ssh.execute("docker ps -a --format '{{.Names}}\t{{.Status}}' 2>/dev/null | head -28")
            preview = (ps_out or "").strip()
            if preview:
                ros_container["docker_ps_preview"] = preview
                alt = _find_alternate_yahboom_container(preview, container)
                if alt:
                    ros_container["alternate_running_container"] = alt

            insp, _, _ = await ssh.execute("docker inspect " + container + " --format '{{json .State}}' 2>&1")
            line = (insp or "").strip()
            if "no such object" in line.lower() or "error: no such object" in line.lower():
                ros_container["docker_state"] = "not_found"
                ros_container["running"] = False
                ros_container["summary"] = f"Container `{container}` not found on this Pi."
                _attach_container_remediation(ros_container, not_found=True)
            elif line.startswith("{"):
                try:
                    st = json.loads(line)
                except json.JSONDecodeError:
                    ros_container["docker_state"] = "inspect_parse_error"
                    ros_container["running"] = False
                    ros_container["summary"] = f"docker inspect returned non-JSON: {line[:120]}"
                else:
                    ros_container["running"] = bool(st.get("Running"))
                    ros_container["docker_state"] = (st.get("Status") or "unknown").lower()
                    ros_container["started_at"] = st.get("StartedAt")
                    ros_container["finished_at"] = st.get("FinishedAt")
                    ros_container["exit_code"] = st.get("ExitCode")
                    ros_container["oom_killed"] = st.get("OOMKilled")
                    err = (st.get("Error") or "").strip()
                    ros_container["error"] = err or None
                    ros_container["summary"] = _container_state_summary(
                        container,
                        ros_container["docker_state"],
                        ros_container.get("exit_code"),
                        ros_container.get("oom_killed"),
                        err,
                    )
                    if not ros_container["running"]:
                        _attach_container_remediation(ros_container, not_found=False)
            else:
                if "error" in line.lower():
                    ros_container["docker_state"] = "inspect_error"
                    ros_container["running"] = False
                    ros_container["summary"] = line[:200]
                else:
                    bits = line.split(None, 2)
                    if len(bits) >= 2:
                        ros_container["running"] = bits[0].lower() == "true"
                        ros_container["docker_state"] = bits[1].strip().lower()
                        ros_container["started_at"] = bits[2] if len(bits) > 2 else None
                    ros_container["summary"] = (
                        f"Container `{container}` is {ros_container.get('docker_state', 'unknown')} "
                        f"(running={ros_container.get('running')})."
                    )
                    if not ros_container.get("running"):
                        _attach_container_remediation(ros_container, not_found=False)
        except Exception as e:
            ros_container["summary"] = f"docker inspect failed: {e}"

        _apply_container_lifecycle(
            ros_container,
            ssh_connected=True,
        )
        await _maybe_attach_docker_logs_preview(ssh, ros_container, container)
    else:
        _apply_container_lifecycle(
            ros_container,
            ssh_connected=False,
        )

    _sync_restart_loop_flag(ros_container)

    driver = await driver_stack_snapshot(ssh)
    driver_public = {k: v for k, v in driver.items() if k != "node_lines"}

    lf = ros_container.get("lifecycle") or {}
    lf_line = ""
    if lf.get("label"):
        lf_line = f"{lf['label']} — {lf.get('detail', '')}"
    ctr_detail = ros_container["summary"]
    if lf_line:
        ctr_detail = f"{lf_line}\n{ctr_detail}"
    if ros_container.get("alternate_running_container"):
        ctr_detail += (
            f" Note: `{ros_container['alternate_running_container']}` is Up — "
            "verify YAHBOOM_ROS2_CONTAINER matches the container you actually run."
        )

    layers = [
        {
            "id": "goliath_tcp",
            "title": "This PC → robot (TCP)",
            "ok": bool(t_ssh["ok"] and t_br["ok"]),
            "detail": goliath["summary"],
        },
        {
            "id": "ssh_session",
            "title": "SSH control session",
            "ok": bool(ssh and ssh.connected),
            "detail": ssh_layer["summary"],
        },
        {
            "id": "pi_network",
            "title": "Pi: hostname, IP, Wi‑Fi",
            "ok": bool(ssh and ssh.connected and (pi_host.get("primary_ip") or pi_host.get("hostname"))),
            "detail": pi_host["summary"],
        },
        {
            "id": "docker_engine",
            "title": "Pi: Docker engine",
            "ok": docker_engine.get("systemd_active") == "active",
            "detail": docker_engine["summary"],
        },
        {
            "id": "ros_container",
            "title": (
                f"Pi: ROS container ({container}) — RESTART LOOP"
                if ros_container.get("restart_loop")
                else f"Pi: ROS container ({container})"
            ),
            "ok": ros_container.get("running") is True,
            "detail": ctr_detail,
        },
        {
            "id": "ros_graph_docker",
            "title": "Inside container: ROS 2 graph",
            "ok": driver_public.get("status") == "running",
            "detail": driver_public.get("detail") or "",
        },
        {
            "id": "rosbridge_graph",
            "title": "Inside container: rosbridge node",
            "ok": driver_public.get("rosbridge_node_seen") is True,
            "detail": (
                "rosbridge_websocket appears in `ros2 node list` inside the container."
                if driver_public.get("rosbridge_node_seen")
                else "No rosbridge_websocket in that graph (rosbridge may run on host or another compose service)."
            ),
        },
        {
            "id": "rosbridge_pc",
            "title": "This PC → rosbridge (WebSocket)",
            "ok": ros_ws,
            "detail": rosbridge_pc["summary"],
        },
        {
            "id": "cmd_vel",
            "title": "Bridge: /cmd_vel advertised",
            "ok": cmd_vel_ready,
            "detail": (
                "cmd_vel topic ready for motion."
                if cmd_vel_ready
                else "Connect and wait for topic setup, or tap Re-Sync."
            ),
        },
        {
            "id": "video",
            "title": "Video pipeline (VideoBridge)",
            "ok": bool(video and getattr(video, "active", False)),
            "detail": video_state["summary"],
        },
    ]

    return {
        "probed_at": now_iso,
        "cache_ttl_sec": max(1.0, float(os.environ.get("YAHBOOM_STACK_PROBE_SECS", "5"))),
        "goliath_to_robot": goliath,
        "ssh_session": ssh_layer,
        "pi_host": pi_host,
        "docker_engine": docker_engine,
        "ros_container": ros_container,
        "ros_graph_in_container": driver_public,
        "rosbridge_from_pc": rosbridge_pc,
        "video": video_state,
        "layers": layers,
    }


async def build_stack_overview(
    ssh,
    bridge,
    video,
    robot_host: str,
    bridge_port: int,
) -> dict[str, Any]:
    """TTL-cached full stack snapshot for Dashboard / health."""
    global _stack_overview_cache, _stack_overview_cache_until
    ttl = max(1.0, float(os.environ.get("YAHBOOM_STACK_PROBE_SECS", "5")))
    now = time.time()
    async with _stack_overview_lock:
        if _stack_overview_cache is not None and now < _stack_overview_cache_until:
            return _stack_overview_cache
        snap = await _stack_overview_uncached(ssh, bridge, video, robot_host, bridge_port)
        _stack_overview_cache = snap
        _stack_overview_cache_until = time.time() + ttl
        return snap
