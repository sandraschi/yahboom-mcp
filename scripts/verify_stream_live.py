import requests


def verify_stream_live():
    url = "http://localhost:10792/stream"
    print(f"[*] Verifying MJPEG Stream at {url}...")

    try:
        # We use stream=True to read just a few chunks
        with requests.get(url, stream=True, timeout=10) as r:
            if r.status_code == 200:
                print("[SUCCESS] MJPEG stream endpoint is LIVE.")
                # Read first few chunks to confirm data flow
                chunk_count = 0
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        chunk_count += 1
                        if chunk_count > 5:
                            print(
                                f"[SUCCESS] Stream is active (received {chunk_count * 1024} bytes)."
                            )
                            break
            else:
                print(f"[FAIL] Stream returned {r.status_code}")
    except Exception as e:
        print(f"[FAIL] Stream connection failed: {e}")


if __name__ == "__main__":
    verify_stream_live()
