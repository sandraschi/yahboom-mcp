import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import StackStatusTable from "../../components/StackStatusTable";
import { api, isBridgeLiveTelemetry, type Health } from "../../lib/api";

const STREAM_URL = "/stream";

import {
  Activity,
  AlertTriangle,
  Camera,
  CameraOff,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Compass,
  Keyboard,
  Loader2,
  MessageSquare,
  Monitor,
  Radio,
  Navigation,
  Shield,
  Square,
  Unplug,
  Volume2,
  Zap,
} from "lucide-react";

// --- Types ---
interface ImuData {
  heading: number;
  pitch: number;
  roll: number;
  yaw: number;
  angular_velocity?: { x: number; y: number; z: number };
  linear_acceleration?: { x: number; y: number; z: number };
}

interface ScanData {
  nearest_m: number | null;
  obstacles: Record<string, number | null>;
}

interface Telemetry {
  battery: number | null;
  voltage: number | null;
  imu: ImuData | null;
  velocity: { linear: number; angular: number };
  position: { x: number; y: number; z: number } | null;
  scan: ScanData | null;
  sonar_m: number | null;
  line_sensors: number[] | null;
  button_pressed: boolean;
  source?: "live" | "simulated";
  status?: string;
}

export default function Dashboard() {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [connected, setConnected] = useState(false);
  const [keysHeld, setKeysHeld] = useState<Record<string, boolean>>({});
  const [wasdActive, setWasdActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isReconnecting, setIsReconnecting] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [llmResponse, setLlmResponse] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  // Voice Intelligence Logic — defined before the useEffect that references it
  const processVoiceCommand = useCallback(async (text: string) => {
    if (!text.trim()) return;
    try {
      // Pipe text to robot for "chat_and_say" (Gemma 3 on Pi)
      const res = await api.postTool("chat_and_say", text);
      if (res?.result?.response) {
        setLlmResponse(res.result.response);
        // Clear response after 10 seconds
        setTimeout(() => setLlmResponse(null), 10000);
      }
    } catch (err) {
      console.error("Voice pipe failed:", err);
    }
  }, []);

  useEffect(() => {
    const SpeechRecognition =
      (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    if (!SpeechRecognition) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onresult = (event: any) => {
      let current = "";
      for (let i = event.resultIndex; i < event.results.length; ++i) {
        current += event.results[i][0].transcript;
      }
      setTranscript(current);

      // Final result detected
      if (event.results[event.results.length - 1].isFinal) {
        const final = event.results[event.results.length - 1][0].transcript;
        processVoiceCommand(final);
      }
    };

    recognition.onend = () => {
      if (isListening) recognition.start();
    };

    recognitionRef.current = recognition;
  }, [isListening, processVoiceCommand]);

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      setTranscript("");
    } else {
      setLlmResponse(null);
      recognitionRef.current?.start();
      setIsListening(true);
    }
  };

  // REST telemetry + health (robot ROS / SSH / video vs configured IP)
  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const [t, h] = await Promise.all([api.getTelemetry(), api.getHealth()]);
        if (!alive) return;
        setTelemetry(t as Telemetry);
        setConnected(isBridgeLiveTelemetry(t));
        setHealth(h);
        setError(null);
        setIsReconnecting(false);
      } catch {
        if (!alive) return;
        setConnected(false);
        setTelemetry(null);
        setHealth(null);
        setError(
          "Control gateway unreachable — start yahboom-mcp on this PC (dashboard proxies to port 10892).",
        );
      }
    };
    poll();
    const id = setInterval(poll, 500);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  // Drive keyboard handler
  useEffect(() => {
    if (!wasdActive) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      if (["w", "a", "s", "d"].includes(key)) {
        setKeysHeld((prev) => ({ ...prev, [key]: true }));
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      const key = e.key.toLowerCase();
      if (["w", "a", "s", "d"].includes(key)) {
        setKeysHeld((prev) => ({ ...prev, [key]: false }));
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    window.addEventListener("keyup", handleKeyUp);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      window.removeEventListener("keyup", handleKeyUp);
    };
  }, [wasdActive]);

  // Directional control loop
  useEffect(() => {
    if (!wasdActive || !connected) return;

    const interval = setInterval(() => {
      let lin_x = 0;
      let ang_z = 0;
      const speed = 0.5;
      const turnSpeed = 1.0;

      if (keysHeld.w) lin_x += speed;
      if (keysHeld.s) lin_x -= speed;
      if (keysHeld.a) ang_z += turnSpeed;
      if (keysHeld.d) ang_z -= turnSpeed;

      if (lin_x !== 0 || ang_z !== 0) {
        api.postMove(lin_x, ang_z);
      }
    }, 100);

    return () => clearInterval(interval);
  }, [wasdActive, keysHeld, connected]);

  const handleReconnect = async () => {
    setIsReconnecting(true);
    try {
      await api.postReconnect();
    } catch (err) {
      console.error("Manual reconnect failed:", err);
    } finally {
      setIsReconnecting(false);
    }
  };

  const rc = health?.robot_connection;
  const gatewayDown = !!error;
  const waitingHealth = !gatewayDown && !health;
  const allGood = !gatewayDown && !!health && connected;
  const partialRobot = !gatewayDown && !!health && !connected && rc?.ssh === "connected";
  const noRobotPath = !gatewayDown && !!health && !connected && rc?.ssh !== "connected";
  const robotIp = rc?.ip ?? "—";

  return (
    <div className="flex flex-col gap-6 p-4 lg:p-8 animate-in fade-in duration-700">
      {/* Robot link — first thing on the dashboard (Goliath ↔ Pi) */}
      <motion.section
        layout
        className={`rounded-3xl border p-5 lg:p-6 ${
          gatewayDown
            ? "border-red-500/35 bg-red-950/45"
            : waitingHealth
              ? "border-slate-600/40 bg-slate-900/50"
              : allGood
                ? "border-emerald-500/30 bg-emerald-950/35"
                : partialRobot
                  ? "border-amber-500/35 bg-amber-950/40"
                  : "border-red-500/35 bg-red-950/45"
        }`}
      >
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div className="space-y-3 min-w-0">
            <div className="flex items-center gap-3">
              {gatewayDown ? (
                <AlertTriangle className="w-8 h-8 text-red-400 shrink-0" />
              ) : waitingHealth ? (
                <Loader2 className="w-8 h-8 text-slate-400 shrink-0 animate-spin" />
              ) : allGood ? (
                <CheckCircle2 className="w-8 h-8 text-emerald-400 shrink-0" />
              ) : partialRobot ? (
                <Radio className="w-8 h-8 text-amber-400 shrink-0" />
              ) : (
                <Unplug className="w-8 h-8 text-red-400 shrink-0" />
              )}
              <div>
                <h2 className="text-lg font-black text-white tracking-tight">
                  {gatewayDown
                    ? "No link to control gateway"
                    : waitingHealth
                      ? "Checking robot link…"
                      : allGood
                        ? "Robot connected"
                        : partialRobot
                          ? "Pi reachable — ROS bridge down"
                          : "No connection to robot"}
                </h2>
                <p className="text-[11px] font-mono text-slate-500 mt-0.5">
                  Target <span className="text-indigo-300">{robotIp}</span>
                  {health && (
                    <>
                      {" · "}
                      <span className={rc?.ros === "connected" ? "text-emerald-400" : "text-slate-500"}>
                        ROS {rc?.ros ?? "—"}
                      </span>
                      {" · "}
                      <span className={rc?.ssh === "connected" ? "text-emerald-400" : "text-slate-500"}>
                        SSH {rc?.ssh ?? "—"}
                      </span>
                      {" · "}
                      <span className={rc?.video === "active" ? "text-emerald-400" : "text-slate-500"}>
                        Video {rc?.video ?? "—"}
                      </span>
                      {typeof rc?.cmd_vel_ready === "boolean" && (
                        <>
                          {" · "}
                          <span className={rc.cmd_vel_ready ? "text-emerald-400" : "text-amber-400"}>
                            cmd_vel {rc.cmd_vel_ready ? "ready" : "not ready"}
                          </span>
                        </>
                      )}
                    </>
                  )}
                </p>
              </div>
            </div>

            {rc?.hint && (
              <p className="text-[10px] text-amber-200/85 max-w-3xl leading-relaxed">{rc.hint}</p>
            )}

            {health?.stack && (
              <div className="max-w-4xl">
                <h3 className="text-[11px] font-black text-slate-400 uppercase tracking-widest mb-2">
                  Full stack status
                </h3>
                <StackStatusTable stack={health.stack} />
              </div>
            )}

            {gatewayDown && (
              <p className="text-sm text-red-200/90 leading-relaxed max-w-3xl">{error}</p>
            )}

            {waitingHealth && (
              <p className="text-sm text-slate-400 leading-relaxed max-w-3xl">
                Contacting this PC&apos;s yahboom-mcp gateway and reading robot health…
              </p>
            )}

            {allGood && (
              <p className="text-sm text-emerald-100/80 leading-relaxed max-w-3xl">
                ROS bridge is live — driving, telemetry, and stream use the Raspbot at{" "}
                <span className="font-mono text-white">{robotIp}</span>.
              </p>
            )}

            {partialRobot && (
              <div className="text-sm text-amber-100/85 leading-relaxed max-w-3xl space-y-2">
                <p>
                  SSH reaches the Pi, but the WebSocket ROS bridge is not connected (rosbridge not
                  running, wrong <span className="font-mono">YAHBOOM_BRIDGE_PORT</span>, or ROS still
                  starting).
                </p>
                <p className="text-xs text-amber-200/70">
                  On the robot: launch rosbridge (e.g.{" "}
                  <span className="font-mono text-amber-200/90">
                    ros2 launch rosbridge_server rosbridge_websocket_launch.xml
                  </span>
                  ).
                </p>
              </div>
            )}

            {noRobotPath && (
              <div className="text-sm text-red-100/85 leading-relaxed max-w-3xl space-y-3">
                <p className="rounded-xl border border-red-500/25 bg-red-950/50 p-3 text-red-50/95 text-sm">
                  <span className="font-semibold text-white">Hey — start with the robot and the link.</span>{" "}
                  Turn the Raspbot on and wait for it to boot. Join the Raspbot Wi‑Fi access point on
                  this PC, <span className="font-semibold">or</span> connect an Ethernet cable between
                  Goliath and the Pi. Until that path exists, Docker, systemd, and Yahboom bringup on
                  the Pi are not in play for this dashboard — there is nothing here to &quot;wake&quot;
                  the robot remotely. After power + network are good, use{" "}
                  <span className="font-mono text-red-100/90">Reconnect</span> (header) or Diagnostics{" "}
                  <span className="font-mono text-red-100/90">Hard Reset</span> if ROS still does not attach.
                </p>
                <p>
                  This PC cannot reach the configured robot address — both{" "}
                  <span className="font-mono">ROS</span> (rosbridge) and <span className="font-mono">SSH</span>{" "}
                  are down. The gateway on Goliath is running; the Pi is not participating.
                </p>
                <ul className="list-disc list-inside text-xs text-red-200/80 space-y-1.5">
                  <li>
                    <span className="font-semibold text-red-100/90">Robot off or booting</span> — Raspbot
                    power / SD / wait for AP or Ethernet to come up.
                  </li>
                  <li>
                    <span className="font-semibold text-red-100/90">Goliath not on the robot network</span>{" "}
                    — join Wi‑Fi to the <span className="font-mono">Raspbot</span> access point{" "}
                    <span className="inline-flex items-center gap-1">
                      <Radio className="w-3 h-3 inline" />
                    </span>{" "}
                    <span className="font-semibold text-red-100/90">and</span> no Ethernet cable is
                    plugged between Goliath and the Raspberry Pi.
                  </li>
                  <li>
                    Wrong <span className="font-mono">YAHBOOM_IP</span> in{" "}
                    <span className="font-mono">webapp/start.ps1</span> (or env) — must match the Pi
                    on the link you use (AP vs home LAN vs Ethernet).
                  </li>
                </ul>
              </div>
            )}
          </div>

          <div className="flex flex-col sm:flex-row lg:flex-col gap-2 shrink-0">
            <Link
              to="/logs"
              className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-center text-xs font-bold text-slate-200 hover:bg-white/10 transition-colors"
            >
              Server logs
            </Link>
            <Link
              to="/diagnostics"
              className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-center text-xs font-bold text-slate-200 hover:bg-white/10 transition-colors"
            >
              Diagnostics
            </Link>
            <Link
              to="/help"
              className="px-4 py-2.5 rounded-xl bg-white/5 border border-white/10 text-center text-xs font-bold text-slate-200 hover:bg-white/10 transition-colors"
            >
              Help
            </Link>
          </div>
        </div>
      </motion.section>

      {/* Header / Status Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-black text-white tracking-tighter flex items-center gap-3">
            <Activity className="text-indigo-500 animate-pulse" />
            CONTROL CENTER
          </h1>
          <p className="text-slate-500 text-xs font-medium tracking-[0.2em] mt-1 ml-9">
            SOTA v1.20 | ROS 2 HUMBLE | VIENNA_ALSERGRUND
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div
            className={`px-4 py-2 rounded-2xl border flex items-center gap-2 transition-all ${
              connected
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                : "bg-red-500/10 border-red-500/20 text-red-400"
            }`}
          >
            <div
              className={`w-2 h-2 rounded-full ${connected ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`}
            />
            <span className="text-[10px] font-black uppercase tracking-widest">
              {connected ? "ROS bridge live" : "ROS bridge offline"}
            </span>
          </div>

          {!connected && (
            <button
              onClick={handleReconnect}
              disabled={isReconnecting}
              className="p-2 aspect-square bg-white/5 border border-white/10 rounded-2xl text-slate-400 hover:text-white hover:bg-white/10 transition-all disabled:opacity-50"
            >
              <Loader2 className={`w-5 h-5 ${isReconnecting ? "animate-spin" : ""}`} />
            </button>
          )}
        </div>
      </div>

      {/* Error Alert */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="bg-red-500/10 border border-red-500/20 rounded-3xl p-4 flex items-center gap-3 text-red-400 text-sm">
              <AlertTriangle size={18} />
              <span className="font-medium">{error}</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Left Column: Visual Feedback & Map */}
        <div className="xl:col-span-2 space-y-6">
          {/* Primary Camera / Visual Feed */}
          <div className="relative aspect-video bg-black rounded-[2.5rem] border border-white/5 overflow-hidden shadow-2xl group">
            {connected ? (
              <img
                src={STREAM_URL}
                className="w-full h-full object-cover min-h-[200px]"
                alt="Robot Camera Feed"
              />
            ) : (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-slate-900/50">
                <CameraOff className="text-slate-700 w-16 h-16 animate-pulse" />
                <p className="text-slate-500 text-xs font-bold uppercase tracking-widest">
                  Visual Stream Offline — connect ROS bridge first
                </p>
              </div>
            )}

            {/* Stream Overlay Details */}
            <div className="absolute top-6 left-6 flex flex-col gap-2">
              <div className="px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-xl border border-white/10 flex items-center gap-2">
                <div
                  className={`w-1.5 h-1.5 rounded-full ${connected ? "bg-emerald-500 animate-pulse" : "bg-red-500"}`}
                />
                <span className="text-[9px] font-bold text-white uppercase tracking-widest">
                  Live Feed
                </span>
              </div>
              <div className="px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-xl border border-white/10 flex items-center gap-2">
                <Volume2 size={12} className="text-slate-400" />
                <span className="text-[9px] font-bold text-slate-300 uppercase tracking-widest">
                  Mic Idle
                </span>
              </div>
            </div>

            {/* Control Hud Overlay */}
            <div className="absolute inset-0 pointer-events-none border-[20px] border-transparent group-hover:border-indigo-500/5 transition-all duration-700" />

            <div className="absolute bottom-8 right-8 pointer-events-auto">
              <button
                onClick={() => api.postTool("stop_all")}
                className="w-16 h-16 rounded-full bg-red-600/90 hover:bg-red-500 shadow-2xl shadow-red-500/40 flex items-center justify-center text-white transition-all hover:scale-110 active:scale-95 group"
                title="Emergency Stop"
              >
                <Square size={24} className="group-hover:scale-110 transition-transform" />
              </button>
            </div>

            {/* Orientation Indicator */}
            <div className="absolute bottom-8 left-8 flex items-center gap-4 bg-black/40 backdrop-blur-lg p-4 rounded-3xl border border-white/10">
              <div className="relative w-12 h-12 flex items-center justify-center">
                <div className="absolute inset-0 rounded-full border-2 border-dashed border-white/10" />
                <Compass
                  className="text-indigo-400 w-8 h-8 transition-transform duration-300"
                  style={{ transform: `rotate(${telemetry?.imu?.heading || 0}deg)` }}
                />
              </div>
              <div>
                <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">
                  Heading
                </p>
                <p className="text-lg font-black text-white leading-none">
                  {(telemetry?.imu?.heading || 0).toFixed(1)}°
                </p>
              </div>
            </div>
          </div>

          {/* Sensor Overlay Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <TelemetryCard
              icon={<Zap className="text-amber-500" />}
              label="Core Energy"
              value={telemetry?.battery ? `${telemetry.battery}%` : "--"}
              subValue={telemetry?.voltage ? `${telemetry.voltage}v` : "--"}
              trend={telemetry?.battery ? (telemetry.battery > 20 ? "stable" : "warning") : "idle"}
            />
            <TelemetryCard
              icon={<Compass className="text-indigo-500" />}
              label="Tilt/Trim"
              value={`${telemetry?.imu?.pitch?.toFixed(1) || 0}°`}
              subValue={`P: ${telemetry?.imu?.roll?.toFixed(1) || 0}°`}
            />
            <TelemetryCard
              icon={<Navigation className="text-cyan-500" />}
              label="Speed"
              value={`${telemetry?.velocity?.linear?.toFixed(2) || 0} m/s`}
              subValue={`Rot: ${telemetry?.velocity?.angular?.toFixed(2) || 0}`}
            />
            <TelemetryCard
              icon={<Shield className="text-emerald-500" />}
              label="Obstacles"
              value={telemetry?.scan?.nearest_m ? `${telemetry.scan.nearest_m}m` : "Clear"}
              subValue="LIDAR Active"
              trend={
                telemetry?.scan?.nearest_m && telemetry.scan.nearest_m < 0.5 ? "danger" : "stable"
              }
            />
          </div>
        </div>

        {/* Right Column: Control & Missions */}
        <div className="space-y-6">
          {/* Control Panel Section */}
          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-2 px-2">
              <div className="w-1 h-4 bg-indigo-500 rounded-full" />
              <h2 className="text-sm font-black text-white uppercase tracking-[0.2em]">
                Deployment System
              </h2>
            </div>

            {/* Camera PTZ Control */}
            <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Camera className="text-cyan-500 w-5 h-5" />
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                    Camera PTZ
                  </h3>
                </div>
                <button
                  onClick={() => api.postTool("camera_reset")}
                  className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-[10px] font-bold text-slate-400 uppercase tracking-widest hover:text-white transition-all"
                  title="Center Camera"
                >
                  Center
                </button>
              </div>

              <div className="grid grid-cols-3 gap-2 max-w-[140px] mx-auto">
                <div />
                <button
                  onClick={() => api.postTool("camera_move", "up")}
                  className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                  title="Tilt Up"
                >
                  <ChevronUp size={20} />
                </button>
                <div />

                <button
                  onClick={() => api.postTool("camera_move", "left")}
                  className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                  title="Pan Left"
                >
                  <ChevronLeft size={20} />
                </button>
                <div className="w-10 h-10 flex items-center justify-center">
                  <div className="w-1.5 h-1.5 rounded-full bg-cyan-500/50 shadow-[0_0_8px_rgba(6,182,212,0.5)]" />
                </div>
                <button
                  onClick={() => api.postTool("camera_move", "right")}
                  className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                  title="Pan Right"
                >
                  <ChevronRight size={20} />
                </button>

                <div />
                <button
                  onClick={() => api.postTool("camera_move", "down")}
                  className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                  title="Tilt Down"
                >
                  <ChevronDown size={20} />
                </button>
                <div />
              </div>

              <p className="text-[10px] text-slate-600 text-center mt-4 uppercase tracking-tighter">
                Pan: ID 1 | Tilt: ID 2
              </p>
            </div>

            {/* Keyboard visual mockup (Simplified) */}
            <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Keyboard className="text-indigo-500 w-5 h-5" />
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                    Keyboard
                  </h3>
                </div>
                <button
                  onClick={() => setWasdActive((v) => !v)}
                  className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${
                    wasdActive
                      ? "bg-emerald-500/20 border border-emerald-500/40 text-emerald-400"
                      : "bg-white/5 border border-white/10 text-slate-500 hover:text-slate-300"
                  }`}
                >
                  {wasdActive ? "Active" : "Enable"}
                </button>
              </div>
              <p className="text-[10px] text-slate-500 text-center font-mono">
                Use WASD keys to drive
              </p>
            </div>

            {/* Lightstrip Control Matrix */}
            <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Zap className="text-amber-500 w-5 h-5" />
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                    Light Control
                  </h3>
                </div>
                <button
                  onClick={() => api.postLightstrip("off")}
                  className="px-3 py-1 bg-red-500/10 border border-red-500/20 rounded-lg text-[10px] font-bold text-red-400 uppercase tracking-widest hover:bg-red-500/20 transition-all"
                >
                  Stop
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => api.postLightstrip("pattern")}
                  className="col-span-2 h-12 rounded-2xl bg-gradient-to-r from-blue-600/20 to-red-600/20 border border-white/10 flex items-center justify-center text-xs font-black text-white uppercase tracking-widest"
                >
                  Patrol Car Pattern
                </button>
                <button
                  onClick={() => api.postLightstrip("set", 255, 0, 0)}
                  className="h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-[10px] font-bold uppercase"
                >
                  Danger Red
                </button>
                <button
                  onClick={() => api.postLightstrip("set", 0, 255, 0)}
                  className="h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase"
                >
                  Safe Green
                </button>
              </div>
            </div>

            {/* Voice & Media Hub (SOTA v16.0) */}
            <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <MessageSquare className="text-indigo-400 w-5 h-5" />
                  <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                    Voice & Media Hub
                  </h3>
                </div>
                <div className="flex items-center gap-2">
                  <div
                    className={`w-2 h-2 rounded-full ${isListening ? "bg-red-500 animate-ping" : "bg-slate-700"}`}
                  />
                  <span className="text-[10px] font-bold text-slate-500 uppercase tracking-tighter">
                    {isListening ? "Listening" : "Ready"}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                {/* Transcription Log */}
                <div className="h-20 bg-black/40 rounded-2xl border border-white/5 p-3 overflow-y-auto overflow-x-hidden scrollbar-hide">
                  <AnimatePresence mode="wait">
                    {llmResponse ? (
                      <motion.div
                        initial={{ opacity: 0, y: 5 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-[10px] text-indigo-300 font-medium leading-relaxed italic"
                      >
                        " {llmResponse} "
                      </motion.div>
                    ) : transcript ? (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-[11px] text-slate-400 font-mono"
                      >
                        {transcript}...
                      </motion.div>
                    ) : (
                      <div className="text-[9px] text-slate-600 uppercase tracking-widest text-center mt-4">
                        Awaiting instructions
                      </div>
                    )}
                  </AnimatePresence>
                </div>

                {/* Controls */}
                <div className="grid grid-cols-2 gap-2">
                  <button
                    onClick={toggleListening}
                    disabled={!connected}
                    className={`flex flex-col items-center justify-center gap-2 h-20 rounded-2xl border transition-all ${
                      isListening
                        ? "bg-red-500/20 border-red-500/40 text-red-400"
                        : "bg-indigo-500/5 border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/10"
                    } disabled:opacity-30`}
                  >
                    <Volume2 className={isListening ? "animate-pulse" : ""} />
                    <span className="text-[9px] font-black uppercase tracking-widest">
                      {isListening ? "Stop" : "Talk To Boomy"}
                    </span>
                  </button>

                  <div className="grid grid-rows-2 gap-2">
                    <button
                    onClick={() => api.postTool("play_beep")}
                      disabled={!connected}
                      className="bg-white/5 border border-white/10 rounded-xl text-[9px] font-bold text-slate-400 uppercase tracking-widest hover:text-white hover:bg-white/10 transition-all flex items-center justify-center gap-2 group"
                    >
                      <Zap size={12} className="group-hover:text-amber-500" />
                      Sound Check
                    </button>
                    <button
                      onClick={() =>
                        api.postVoice(
                          "play_file",
                          "E:\\Multimedia Files\\Music - Blues\\James, Etta\\Her Best (1997)\\James, Etta - Her Best (1997) - 16 - I'd Rather Go Blind.mp3",
                        )
                      }
                      disabled={!connected}
                      className="bg-white/5 border border-white/10 rounded-xl text-[9px] font-bold text-slate-400 uppercase tracking-widest hover:text-indigo-300 hover:bg-indigo-500/10 transition-all flex items-center justify-center gap-2 group"
                    >
                      <Monitor size={12} className="group-hover:text-indigo-400" />
                      Play Blues
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function TelemetryCard({
  icon,
  label,
  value,
  subValue,
  trend,
}: {
  icon: any;
  label: string;
  value: string;
  subValue: string;
  trend?: "stable" | "warning" | "danger" | "idle";
}) {
  const trendColors = {
    stable: "bg-emerald-500",
    warning: "bg-amber-500",
    danger: "bg-red-500 animate-pulse",
    idle: "bg-slate-700",
  };

  return (
    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-5 backdrop-blur-xl shadow-xl">
      <div className="flex items-center justify-between mb-4">
        <div className="w-10 h-10 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
          {icon}
        </div>
        {trend && <div className={`w-1.5 h-1.5 rounded-full ${trendColors[trend]}`} />}
      </div>
      <p className="text-[8px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">
        {label}
      </p>
      <p className="text-xl font-black text-white tracking-tight">{value}</p>
      <p className="text-[10px] text-slate-600 font-medium mt-1">{subValue}</p>
    </div>
  );
}
