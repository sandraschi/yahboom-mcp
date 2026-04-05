#!/usr/bin/env python3
import subprocess
import sys


def run_cmd(cmd, check=True):
    print(f"Executing: {cmd}")
    try:
        subprocess.run(cmd, shell=True, check=check)
    except subprocess.CalledProcessError as e:
        print(f"Command failed: {e}")
        if check:
            sys.exit(1)


def install_code_server():
    print("--- Installing Code-Server ---")
    run_cmd("curl -fsSL https://code-server.dev/install.sh | sh")
    run_cmd("sudo systemctl enable --now code-server@pi")
    print("Code-Server active at port 8080 (default).")


def install_piper():
    print("--- Installing Piper TTS ---")
    run_cmd("mkdir -p ~/piper && cd ~/piper")
    # Download ARM64 binary (Substantiated URL)
    run_cmd(
        "wget -q https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_arm64.tar.gz -O ~/piper/piper.tar.gz"
    )
    run_cmd("tar -xf ~/piper/piper.tar.gz -C ~/piper")
    # Download Voice Model
    run_cmd(
        "wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx -O ~/piper/voice.onnx"
    )
    run_cmd(
        "wget -q https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json -O ~/piper/voice.onnx.json"
    )
    print("Piper TTS ready in ~/piper")


def install_ollama():
    print("--- Installing Ollama ---")
    run_cmd("curl -fsSL https://ollama.com/install.sh | sh")
    print("Pulling Gemma 3 1B...")
    run_cmd("ollama pull gemma3:1b")
    print("Ollama engine and Gemma 3 ready.")


def main():
    print("BOOMY COGNITIVE UPGRADE: Initiating Pack...")
    install_code_server()
    install_piper()
    install_ollama()
    print("UPGRADE COMPLETE. Monitor thermals on the dashboard.")


if __name__ == "__main__":
    main()
