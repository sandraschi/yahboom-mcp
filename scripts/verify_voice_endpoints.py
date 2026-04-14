import time

import requests


def verify_voice_endpoints():
    base_url = "http://localhost:10792"
    endpoints = [
        ("/api/v1/voice/say", {"text": "Voice module restored. System online."}),
        ("/api/v1/voice/play", {"sound_id": 1}),
        ("/api/v1/display/clear", None),
    ]

    print(f"[*] Verifying Voice & Display endpoints at {base_url}...")

    for path, payload in endpoints:
        url = f"{base_url}{path}"
        try:
            if payload:
                r = requests.post(url, json=payload, timeout=5)
            else:
                r = requests.post(url, timeout=5)

            if r.status_code == 200:
                print(f"[SUCCESS] {path} is LIVE. (Response: {r.json()})")
            else:
                print(f"[FAIL] {path} returned {r.status_code}: {r.text}")
        except Exception as e:
            print(f"[FAIL] {path} connection failed: {e}")


if __name__ == "__main__":
    time.sleep(2)  # Give server a moment to start
    verify_voice_endpoints()
