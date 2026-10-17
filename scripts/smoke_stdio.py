#!/usr/bin/env python3
"""Minimal MCP stdio smoke: spawn command, send initialize, expect JSON-RPC response.

Vendored from mcp-central-docs/scripts/stdio_mcp_smoke.py (canonical copy);
one line adjusted for this repo's ruff gate (RUF005 unpack instead of concat).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Any


def run_smoke(
    command: str,
    args: list[str],
    timeout_sec: float = 10.0,
    *,
    env: dict[str, str] | None = None,
    cwd: str | None = None,
) -> dict[str, Any]:
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "fleet-cold-install-smoke", "version": "0.1.0"},
        },
    }
    child_env = os.environ.copy()
    if env:
        child_env.update(env)
    proc = subprocess.Popen(
        [command, *args],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=child_env,
        cwd=cwd or None,
    )
    assert proc.stdin is not None
    assert proc.stdout is not None
    proc.stdin.write(json.dumps(init_msg) + "\n")
    proc.stdin.flush()

    deadline = time.time() + timeout_sec
    lines: list[str] = []
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            if proc.poll() is not None:
                break
            time.sleep(0.1)
            continue
        lines.append(line.strip())
        try:
            payload = json.loads(line)
            if isinstance(payload, dict) and payload.get("jsonrpc") == "2.0":
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill()
                return {
                    "ok": True,
                    "response": payload,
                    "log": "\n".join(lines[-20:]),
                }
        except json.JSONDecodeError:
            continue

    try:
        proc.terminate()
        proc.wait(timeout=2)
    except Exception:
        proc.kill()
    err = proc.stderr.read() if proc.stderr else ""
    return {
        "ok": False,
        "error": "No valid JSON-RPC response within timeout",
        "log": "\n".join([*lines, err][-30:]),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP stdio initialize smoke test")
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--cwd", default="")
    parser.add_argument("--env", action="append", default=[], help="KEY=VALUE (repeatable)")
    parser.add_argument(
        "remainder",
        nargs=argparse.REMAINDER,
        help="Server command after optional '--' (e.g. -- uv run my-mcp)",
    )
    ns = parser.parse_args()
    tokens = list(ns.remainder or [])
    if tokens and tokens[0] == "--":
        tokens = tokens[1:]
    if not tokens:
        parser.error("missing server command (use -- before command if it starts with -)")
    command = tokens[0]
    args = tokens[1:]
    env_map: dict[str, str] = {}
    for item in ns.env:
        if "=" in item:
            k, v = item.split("=", 1)
            env_map[k] = v
    result = run_smoke(
        command,
        args,
        ns.timeout,
        env=env_map or None,
        cwd=ns.cwd or None,
    )
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
