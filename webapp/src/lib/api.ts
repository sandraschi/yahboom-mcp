/**
 * Yahboom webapp API client. Uses relative URLs so Vite proxy (/api -> backend) works.
 * Backend: http://localhost:10892 (start.ps1).
 */

const API_BASE = "";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = path.startsWith("http") ? path : `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/** On-robot `ros2 node list` inside docker (from SSH), cached on server */
export interface DriverStackSnapshot {
  status: "running" | "absent" | "ssh_offline" | "probe_failed" | "unknown";
  container: string;
  matched_nodes: string[];
  rosbridge_node_seen: boolean | null;
  ros_node_line_count: number;
  detail: string;
}

export interface TcpPortProbe {
  ok: boolean;
  error?: string | null;
}

export interface StackLayerRow {
  id: string;
  title: string;
  ok: boolean;
  detail: string;
}

/** Full layered stack from GET /api/v1/health `stack` (TTL-cached SSH + TCP probes) */
export interface StackOverview {
  probed_at: string;
  cache_ttl_sec: number;
  goliath_to_robot: {
    robot_ip: string;
    rosbridge_tcp_port: number;
    tcp_ssh_port_22: TcpPortProbe;
    tcp_rosbridge_port: TcpPortProbe;
    summary: string;
  };
  ssh_session: {
    paramiko_session: string;
    target_host: string;
    summary: string;
  };
  pi_host: {
    hostname?: string | null;
    primary_ip?: string | null;
    all_ips?: string[];
    interfaces_preview?: string | null;
    wifi?: {
      state: string;
      ssid?: string | null;
      raw_preview?: string | null;
    };
    summary: string;
  };
  docker_engine: {
    systemd_active: string;
    server_version?: string | null;
    summary: string;
  };
  ros_container: {
    name: string;
    running?: boolean | null;
    docker_state?: string;
    started_at?: string | null;
    finished_at?: string | null;
    exit_code?: number | null;
    oom_killed?: boolean | null;
    error?: string | null;
    docker_ps_preview?: string | null;
    remediation_steps?: string[];
    alternate_running_container?: string | null;
    /** True when Docker reports a restart loop (State contains `restarting`). */
    restart_loop?: boolean;
    /** Last N lines from `docker logs` when container unhealthy (server-side redaction + size cap). */
    docker_logs_preview?: string | null;
    docker_logs_error?: string | null;
    docker_logs_truncated?: boolean;
    docker_logs_lines_fetched?: number;
    /** Derived: never_started vs ran_then_stopped vs running, etc. */
    lifecycle?: {
      phase: string;
      label: string;
      detail: string;
    };
    summary: string;
  };
  ros_graph_in_container: DriverStackSnapshot;
  rosbridge_from_pc: {
    websocket_to_rosbridge: string;
    cmd_vel_advertised_on_bridge: boolean;
    summary: string;
  };
  video: {
    video_bridge_active: boolean;
    summary: string;
  };
  layers: StackLayerRow[];
}

/** Structured mission from POST /api/v1/agent/mission */
export interface MissionPlanV1 {
  version: number;
  intent: string;
  target_description: string;
  behavior: string;
  /** Optional Nav2 pose when behavior is go_to_waypoint */
  nav2_goal?: Record<string, unknown> | null;
  suggested_ros_topics: string[];
  voice_feedback: string;
  safety_notes: string;
  estimated_duration_sec: number;
}

export interface AgentMissionResponse {
  success: boolean;
  provider: string;
  plan: MissionPlanV1;
  published_to_ros: boolean;
  mission_topic: string;
  publish_error?: string | null;
  spoke?: boolean;
}

export interface Health {
  status: string;
  stack?: StackOverview;
  robot_connection: {
    ros: "connected" | "disconnected";
    video: "active" | "inactive";
    ssh: "connected" | "disconnected";
    ip: string;
    /** False if rosbridge is up but /cmd_vel was not advertised yet */
    cmd_vel_ready?: boolean;
    /** Mcnamu_driver / driver_node inside YAHBOOM_ROS2_CONTAINER */
    driver_stack?: DriverStackSnapshot;
    hint?: string | null;
  };
  /** Legacy / optional; server returns `system.uptime` */
  uptime?: number;
  system?: { uptime: number; version?: string };
}

export interface ImuData {
  heading: number;
  pitch: number;
  roll: number;
  yaw: number;
  angular_velocity?: { x: number; y: number; z: number };
  linear_acceleration?: { x: number; y: number; z: number };
}

export interface ScanData {
  nearest_m: number | null;
  obstacles: Record<string, number | null>;
}

export interface Telemetry {
  battery: number | null;
  voltage: number | null;
  imu: ImuData | null;
  velocity: { linear: number; angular: number };
  position: { x: number; y: number; z: number } | null;
  scan: ScanData | null;
  /** Single forward ultrasonic (m) */
  sonar_m?: number | null;
  /** Eight values (m), order FL,F,FR,... */
  ir_proximity?: (number | null)[] | null;
  /** Present from Unified Gateway: live when ROS bridge is connected */
  source?: "live" | "simulated";
  status?: string;
  timestamp?: string;
}

export interface OllamaStatus {
  connected: boolean;
  base_url: string;
}

export interface OllamaModel {
  name: string;
  size?: number;
  modified_at?: string;
}

export interface OllamaModelsResponse {
  models: OllamaModel[];
  error?: string;
}

export interface LLMSettings {
  provider: string;
  model: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

export interface ChatResponse {
  message: ChatMessage;
}

/** True when GET /api/v1/telemetry reports a live ROS bridge (webapp uses this vs `status`). */
export function isBridgeLiveTelemetry(t: unknown): boolean {
  if (!t || typeof t !== "object") return false;
  const o = t as { source?: string; status?: string };
  return o.source === "live" || o.status === "live";
}

/** Sensors payload: telemetry + ir_proximity, line_sensors, back_light */
export interface SensorsResponse {
  battery?: number | null;
  voltage?: number | null;
  imu?: ImuData | null;
  velocity?: { linear: number; angular: number };
  position?: { x: number; y: number; z: number } | null;
  scan?: ScanData | null;
  source?: "live" | "simulated";
  status?: string;
  /** Eight values (m), order FL,F,FR,… — null if sector unknown */
  ir_proximity?: (number | null)[] | null;
  /** Single forward ultrasonic (m) when ring not built */
  sonar_m?: number | null;
  line_sensors?: number[] | null;
  back_light?: { on: boolean; brightness: number };
  timestamp?: string;
}

/** Dreame hoover bot map (from DREAME_MAP_URL). Shape depends on upstream (image URL, base64, or JSON grid). */
export type DreameMapResponse = Record<string, unknown> & {
  image?: string;
  image_url?: string;
  map_data?: unknown;
  layers?: unknown;
};

export interface DiagStackResponse {
  success: boolean;
  ros_nodes: string[];
  service_status: string;
  driver_stack?: DriverStackSnapshot;
  i2c_bus_state: string;
  voice_module_state: string;
  recent_kernel_i2c_logs: string;
  timestamp: string;
  error?: string;
}

export interface DiagLogsResponse {
  success: boolean;
  logs: string;
  error?: string;
}

export interface CommandResponse {
  success: boolean;
  stdout: string;
  stderr: string;
  exit_code: number;
  error?: string;
}

/** Hardware op JSON from POST /api/v1/display/*, /api/v1/voice/*, /api/v1/control/voice */
export interface HardwareOpResponse {
  success: boolean;
  error?: string;
  log?: string;
  status?: string;
  result?: {
    success?: boolean;
    log?: string;
    error?: string;
    hint?: string;
    [k: string]: unknown;
  };
}

export interface MissionStatus {
  mission_id: string | null;
  status: string;
  progress: number;
  logs: string[];
  uptime: number;
  last_error: string | null;
}

export const api = {
  getHealth: () => request<Health>("/api/v1/health"),
  getTelemetry: () => request<Telemetry>("/api/v1/telemetry"),
  getDreameMap: () => request<DreameMapResponse>("/api/v1/lidar/dreame-map"),
  getSensors: () => request<SensorsResponse>("/api/v1/sensors"),
  setBackLight: (on: boolean, brightness?: number) =>
    request<{ on: boolean; brightness: number }>("/api/v1/sensors/back_light", {
      method: "POST",
      body: JSON.stringify({ on, brightness: brightness ?? 100 }),
    }),
  postMove: (linear: number, angular: number, linearY?: number) =>
    request<{ status: string; command: { linear: number; angular: number; linear_y?: number } }>(
      `/api/v1/control/move?linear=${encodeURIComponent(linear)}&angular=${encodeURIComponent(angular)}${linearY !== undefined ? `&linear_y=${encodeURIComponent(linearY)}` : ""}`,
      { method: "POST" },
    ),
  setLed: (r: number, g: number, b: number) =>
    request<{ success: boolean }>("/api/v1/led", {
      method: "POST",
      body: JSON.stringify({ r, g, b }),
    }),
  setEmergency: (active: boolean) =>
    request<{ active: boolean }>("/api/v1/emergency", {
      method: "POST",
      body: JSON.stringify({ active }),
    }),
  getOllamaStatus: () => request<OllamaStatus>("/api/v1/settings/ollama/status"),
  getOllamaModels: () => request<OllamaModelsResponse>("/api/v1/settings/ollama/models"),
  getLlmSettings: () => request<LLMSettings>("/api/v1/settings/llm"),
  putLlmSettings: (model: string) =>
    request<LLMSettings>("/api/v1/settings/llm", {
      method: "PUT",
      body: JSON.stringify({ model }),
    }),
  postChat: (messages: ChatMessage[]) =>
    request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ messages }),
    }),
  /** Voice Module */
  postVoiceSay: (text: string) =>
    request<{ success: boolean }>("/api/v1/voice/say", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),
  postVoicePlay: (sound_id: number) =>
    request<HardwareOpResponse>("/api/v1/control/voice", {
      method: "POST",
      body: JSON.stringify({ operation: "play", id: sound_id }),
    }),
  /** OLED Display */
  postDisplayWrite: (text: string, line: number = 1) =>
    request<HardwareOpResponse>("/api/v1/display/write", {
      method: "POST",
      body: JSON.stringify({ text, line }),
    }),
  postDisplayClear: () =>
    request<HardwareOpResponse>("/api/v1/display/clear", {
      method: "POST",
    }),
  postReconnect: () =>
    request<{ success: boolean; status: string }>("/api/v1/reconnect", {
      method: "POST",
    }),

  // Consolidated Peripheral Controls (Peripherals 2.0)
  postLightstripControl: (r: number, g: number, b: number, mode: number = 0) =>
    request<{ success: boolean }>("/api/v1/led", {
      method: "POST",
      body: JSON.stringify({ r, g, b, mode }),
    }),
  postDisplayControl: (action: "write" | "scroll" | "clear", text?: string, line?: number) => {
    if (action === "clear")
      return request<HardwareOpResponse>("/api/v1/display/clear", { method: "POST" });
    if (action === "scroll")
      return request<HardwareOpResponse>("/api/v1/display/scroll", {
        method: "POST",
        body: JSON.stringify({ text }),
      });
    return request<HardwareOpResponse>("/api/v1/display/write", {
      method: "POST",
      body: JSON.stringify({ text, line: line ?? 1 }),
    });
  },
  postVoiceControl: (text: string) =>
    request<HardwareOpResponse>("/api/v1/voice/say", {
      method: "POST",
      body: JSON.stringify({ text }),
    }),

  /** Missions 1.0 */
  postMissionRun: (missionId: string) =>
    request<{ success: boolean; mission: string }>(`/api/v1/missions/run/${missionId}`, {
      method: "POST",
    }),
  getMissionStatus: () => request<MissionStatus>("/api/v1/missions/status"),
  postMissionStop: () =>
    request<{ success: boolean }>("/api/v1/missions/stop", {
      method: "POST",
    }),
  postStopAll: () =>
    request<{ success: boolean; actions: string[] }>("/api/v1/stop_all", {
      method: "POST",
    }),
  /** ROS 2 Diagnostics */
  getRosTopics: () =>
    request<{ success: boolean; topics?: any[]; error?: string }>(
      "/api/v1/diagnostics/ros/topics",
    ),
  postResyncRos: () =>
    request<{ success: boolean }>("/api/v1/diagnostics/ros/resync", {
      method: "POST",
    }),
  postRestartRos: () =>
    request<{ success: boolean; message: string }>("/api/v1/diagnostics/ros/restart", {
      method: "POST",
    }),
  /** Peripheral status probes */
  getVoiceStatus: () =>
    request<{
      success: boolean;
      result: { detected: boolean; device: string | null; note: string };
    }>("/api/v1/control/voice/status"),
  getDisplayStatus: () =>
    request<{
      success: boolean;
      result: { active: boolean; driver_responding: boolean; note: string };
    }>("/api/v1/control/display/status"),
  /** Lightstrip patterns */
  postLightstripPattern: (pattern: "patrol" | "rainbow" | "breathe" | "fire") =>
    request<{ success: boolean }>("/api/v1/control/lightstrip", {
      method: "POST",
      body: JSON.stringify({ operation: "pattern", pattern }),
    }),
  postLightstripOff: () =>
    request<{ success: boolean }>("/api/v1/control/lightstrip", {
      method: "POST",
      body: JSON.stringify({ operation: "off" }),
    }),

  /** Convenience alias used by Dashboard: postLightstrip("off") | postLightstrip("pattern", 10) | postLightstrip("set", r, g, b) */
  postLightstrip: (operation: string, r?: number, g?: number, b?: number) => {
    if (operation === "off")
      return request<{ success: boolean }>("/api/v1/control/lightstrip", {
        method: "POST",
        body: JSON.stringify({ operation: "off" }),
      });
    if (operation === "pattern")
      return request<{ success: boolean }>("/api/v1/control/lightstrip", {
        method: "POST",
        body: JSON.stringify({ operation: "pattern", pattern: "patrol" }),
      });
    return request<{ success: boolean }>("/api/v1/control/lightstrip", {
      method: "POST",
      body: JSON.stringify({ operation: "set", r: r ?? 0, g: g ?? 0, b: b ?? 0 }),
    });
  },

  postVoice: (operation: "say" | "play" | "volume", text?: string, volume?: number, id?: number) =>
    request<{ success: boolean }>("/api/v1/control/voice", {
      method: "POST",
      body: JSON.stringify({ operation, text, volume, id }),
    }),
  postTool: (operation: string, param1?: any, param2?: any, param3?: any, payload?: any) =>
    request<any>("/api/v1/control/tool", {
      method: "POST",
      body: JSON.stringify({ operation, param1, param2, param3, payload }),
    }),
  getDiagLogs: (lines: number = 80) =>
    request<{ success: boolean; logs: string }>(`/api/v1/diagnostics/logs?lines=${lines}`),
  getDiagStack: () =>
    request<DiagStackResponse>("/api/v1/diagnostics/stack"),
  postExecCommand: (command: string) =>
    request<CommandResponse>("/api/v1/diagnostics/exec", {
      method: "POST",
      body: JSON.stringify({ command }),
    }),
  /** Returns the URL for the SSE log stream — use with EventSource */
  logsStreamUrl: () => "/api/v1/logs/stream",

  /** LLM mission planner: natural language → JSON; optional ROS String publish + voice */
  postAgentMission: (body: {
    goal: string;
    provider?: "auto" | "ollama" | "gemini";
    publish_to_ros?: boolean;
    speak?: boolean;
  }) =>
    request<AgentMissionResponse>("/api/v1/agent/mission", {
      method: "POST",
      body: JSON.stringify({
        goal: body.goal,
        provider: body.provider ?? "auto",
        publish_to_ros: body.publish_to_ros ?? true,
        speak: body.speak ?? false,
      }),
    }),
};
