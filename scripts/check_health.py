#!/usr/bin/env python3
"""
Call Yahboom MCP REST API for health and telemetry (no MCP client required).
Usage: python scripts/check_health.py [--base http://localhost:10792]
"""

import argparse
import json
import sys

try:
    import httpx
except ImportError:
    print("pip install httpx", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    p = argparse.ArgumentParser(description="Check Yahboom MCP server health and telemetry")
    p.add_argument("--base", default="http://localhost:10792", help="API base URL")
    args = p.parse_args()
    base = args.base.rstrip("/")

    with httpx.Client(timeout=5.0) as client:
        try:
            r = client.get(f"{base}/api/v1/health")
            r.raise_for_status()
            health = r.json()
            print("Health:", json.dumps(health, indent=2))
        except Exception as e:
            print(f"Health failed: {e}", file=sys.stderr)
            sys.exit(1)

        try:
            r = client.get(f"{base}/api/v1/telemetry")
            r.raise_for_status()
            telemetry = r.json()
            print("Telemetry:", json.dumps(telemetry, indent=2))
        except Exception as e:
            print(f"Telemetry failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
