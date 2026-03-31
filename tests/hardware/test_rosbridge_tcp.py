"""
Optional smoke tests against a real robot on the LAN.

Requires:
  YAHBOOM_E2E=1
  YAHBOOM_IP (default 192.168.0.250)
  YAHBOOM_BRIDGE_PORT (default 9090)

Skipped in GitHub Actions unless you add a self-hosted runner with a bot.
"""

from __future__ import annotations

import os
import socket

import pytest


@pytest.mark.real_robot
@pytest.mark.slow
def test_tcp_rosbridge_port_open() -> None:
    host = os.environ.get("YAHBOOM_IP", "192.168.0.250")
    port = int(os.environ.get("YAHBOOM_BRIDGE_PORT", "9090"))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)
        err = s.connect_ex((host, port))
    assert err == 0, f"Cannot reach rosbridge at {host}:{port} (errno={err})"
