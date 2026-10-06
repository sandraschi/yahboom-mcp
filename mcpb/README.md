# yahboom-mcp (MCPB Bundle)

SOTA 2026 Yahboom Raspbot v2 ROS 2 MCP Server

## Usage

Add to \claude_desktop_config.json\:
\\\json
{
  "mcpServers": {
    "yahboom-mcp": {
      "command": "uv",
      "args": ["run", "--directory", "\D:\Dev\repos", "python", "-m", "yahboom_mcp"],
      "env": { "PYTHONPATH": "\D:\Dev\repos/src" }
    }
  }
}
\\\

## Tools

- **yahboom_tool**: yahboom_tool
- **yahboom_demo**: yahboom_demo
- **yahboom_agentic_workflow**: yahboom_agentic_workflow
- **yahboom_help_tool**: yahboom_help_tool
- **ros_topic_list**: ros_topic_list
- **ros_node_info**: ros_node_info
- **ros_resync**: ros_resync
- **ros_restart_bringup**: ros_restart_bringup
- **lidar**: lidar
- **yahboom_agent_mission**: yahboom_agent_mission
- **audio**: audio
- **query_logs**: query_logs
- **yahboom_shutdown**: yahboom_shutdown
- **get_diagnostics**: CUA-NSIS smoke test diagnostics endpoint.
- **get_health**: Industrial-grade health diagnostics for the robot connection.
- **get_ros_topics**: Endpoint for webapp Topic Explorer.
- **post_ros_resync**: post_ros_resync
- **upload_file**: upload_file
- **post_tool_execution**: Bridge for the web Dashboard to trigger yahboom_tool operations.
- **restart_ros_bringup**: Endpoint for webapp 'Restart Bringup' action.
- **video_feed**: MJPEG stream endpoint for Dashboard visualization with SOTA Fallback.
- **snapshot**: Single JPEG frame for embodied AI / VLM. Returns 204 if no frame yet.
- **gpio_set**: Set a GPIO pin on the Raspberry Pi (e.g. headlight LED).
- **gpio_status**: Get all GPIO pin states.
- **get_diag_stack**: ROS 2 node list + I2C/service status via SSH. Returns partial on failure.
- **get_diag_logs**: Return recent in-process log lines from the ring buffer.
- **exec_command**: Execute a shell command on the robot via SSH. Sandboxed to read-mostly ops.
- **stream_logs**: Server-Sent Events stream of live log output from the ring buffer.
- **telemetry**: Real-time telemetry from all connected ROS 2 sensors.
- **get_slam_map**: Return the SLAM occupancy grid as a PNG image.     Requires slam_toolbox async running on the rob...
- **api_lidar_dreame_map**: Proxy the Dreame D20 Pro floorplan map from dreame-mcp (DREAME_MAP_URL).      The standalone drea...
- **get_slam_data**: Return SLAM map metadata + robot pose + LIDAR scan points for frontend overlay.      Returns JSON...
- **legacy_sensors**: Legacy alias for /api/v1/telemetry.
- **write_display**: Write text to the OLED/LCD display (Closed-Loop).
- **clear_display**: Clear the OLED display.
- **scroll_display**: Start background scrolling on the OLED display.
- **run_mission**: Start an automated mission.
- **get_mission_status**: Get the status of the current or last mission.
- **stop_mission**: Abort the current mission.
- **demo_describe**: demo_describe
- **demo_draw**: demo_draw
- **demo_draw_status**: demo_draw_status
- **demo_draw_stop**: demo_draw_stop
- **demo_talkbot**: demo_talkbot
- **demo_talkbot_status**: demo_talkbot_status
- **demo_talkbot_stop**: demo_talkbot_stop
- **speak**: Speak text via the Voice Module.
- **play_voice**: Play a built-in sound ID via the Voice Module.
- **legacy_voice_say**: Legacy alias for /api/v1/voice.
- **tapo_audio_listen**: Capture audio from Tapo's RTSP mic and transcribe via faster-whisper.
- **tapo_audio_speak**: Convert text to speech and play through Pi audio output.
- **tapo_audio_status**: Check Tapo camera connectivity and audio capabilities.
- **set_led**: Set Lightstrip RGB values.
- **control_lightstrip**: Lightstrip control: static colour, off, or named autochange pattern.
- **control_buzzer**: Buzz the onboard piezo buzzer via I2C.
- **control_voice**: Voice module: say text, play sound ID, set volume, or probe status.
- **get_voice_status**: Probe voice module USB device.
- **get_display_status**: Probe OLED display via I2C.
- **post_display_status_control_alias**: POST alias (Dashboard used to call POST here; GET is preferred).
- **post_display_status**: Probe OLED display via I2C (POST alias for webapp).
- **display_write_v2**: Write text to OLED (line param supported).
- **legacy_backlight**: Legacy alias mapping back_light (bool) to Lightstrip RGB.
- **toggle_emergency**: Toggle the Emergency Mode background sequence.
- **reconnect_hardware**: Manually trigger a ROS 2 bridge handshake.
- **post_stop_all**: Global emergency stop: halts all robot activity.
- **control_move**: Direct motion control endpoint for Dashboard UI and embodied loop.
- **ollama_status**: Check if Ollama is reachable (for Settings page).
- **ollama_models**: List models discovered from Ollama (for Settings page dropdown).
- **get_llm_settings**: Current LLM provider and selected model (for chat/settings).
- **update_llm_settings**: Set LLM provider and model (persists in process memory).
- **lmstudio_status**: Check if LM Studio is reachable.
- **lmstudio_models**: List models from LM Studio (for Settings page dropdown).
- **get_gpu_status**: Best-effort GPU detection (nvidia-smi on Windows or Linux). Returns VRAM, temp, utilization if av...
- **chat_completion**: chat_completion
- **agent_mission_plan**: agent_mission_plan
- **api_shutdown**: REST alias for the self-termination tool (POST /api/shutdown).
- **get_skills**: List registered Yahboom skills (skill-first chat preprompt source).
- **get_bridge_proxies**: List active MCP bridge proxy providers and their status.
- **get_capabilities**: Runtime source of truth for server capabilities (WEBAPP_STANDARDS §1.4).

## Requirements

- Python 3.12+
- uv
