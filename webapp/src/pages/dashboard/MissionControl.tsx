import { motion } from "framer-motion";
import {
  Activity,
  Battery,
  Bot,
  Camera,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Compass,
  Crosshair,
  Navigation,
  Server,
  Video,
  WifiOff,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

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
  sonar_m?: number | null;
  ir_proximity?: (number | null)[] | null;
  source: "live" | "simulated";
}

type ConnState = "loading" | "server_down" | "bot_offline" | "connected";

export default function MissionControl() {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [connState, setConnState] = useState<ConnState>("loading");
  const [reconnecting, setReconnecting] = useState(false);
  const [cameraConnected, setCameraConnected] = useState(true);

  // --- Unified Gateway (via api client; stream via Vite proxy) ---
  const STREAM_URL = "/stream";

  useEffect(() => {
    if (connState === "connected") setCameraConnected(true);
  }, [connState]);

  useEffect(() => {
    const poll = async () => {
      try {
        const hData = await api.getHealth();
        if (hData.status) {
          setConnState(hData.robot_connection.ros === "connected" ? "connected" : "bot_offline");
        }
        const tData = await api.getTelemetry();
        if (tData.battery !== undefined) setTelemetry(tData);
      } catch (_err) {
        setConnState("server_down");
      }
    };
    poll();
    const interval = setInterval(poll, 1500);
    return () => clearInterval(interval);
  }, []);

  const handleReconnect = async () => {
    setReconnecting(true);
    try {
      await api.postReconnect();
      // Poll immediately after reconnect attempt
      const hData = await api.getHealth();
      setConnState(hData.robot_connection.ros === "connected" ? "connected" : "bot_offline");
    } catch (err) {
      console.error("Reconnect failed:", err);
    } finally {
      setReconnecting(false);
    }
  };

  return (
    <div className="p-8 pb-32 w-full animate-fade-in text-white min-h-screen relative">
      <div className="sota-bg" />
      <div className="sota-glow top-0 left-0" />

      <div className="flex items-center justify-between mb-8 relative z-10">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2 flex items-center gap-3">
            <Bot className="w-8 h-8 text-indigo-400" />
            Yahboom Control Center
          </h1>
          <p className="text-slate-400">
            Unified Gateway Interface • ROS 2 Foxy/Humble • SOTA 2026 Reference Implementation
          </p>
        </div>

        <div
          className={`flex items-center gap-3 px-4 py-2 rounded-full border backdrop-blur-md transition-all ${
            connState === "connected"
              ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
              : connState === "server_down"
                ? "bg-red-500/10 text-red-400 border-red-500/20"
                : "bg-amber-500/10 text-amber-400 border-amber-500/20"
          }`}
        >
          <div
            className={`w-2 h-2 rounded-full animate-pulse ${
              connState === "connected" ? "bg-emerald-500" : "bg-red-500"
            }`}
          />
          <span className="text-sm font-semibold uppercase tracking-wider">
            {reconnecting ? "RECONNECTING..." : connState.replace("_", " ")}
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 relative z-10">
        {/* Camera Feed Section — real stream when connected, placeholder when offline */}
        <div className="lg:col-span-2 glass-card rounded-2xl overflow-hidden flex flex-col group">
          <div className="p-4 border-b border-white/5 flex justify-between items-center bg-slate-900/40">
            <h3 className="font-medium flex items-center gap-2 text-slate-200">
              <Video className="w-4 h-4 text-indigo-400" />
              {connState === "connected" ? "Live Forward Chassis Camera" : "Chassis Camera"}
            </h3>
            <div className="flex gap-2">
              <span className="text-[10px] uppercase tracking-widest bg-slate-800/80 px-2 py-1 rounded text-slate-400 border border-white/5">
                {connState === "connected" ? "HARDWARE" : "OFFLINE"}
              </span>
              {connState === "connected" && cameraConnected && (
                <span className="text-[10px] uppercase tracking-widest bg-indigo-500/20 px-2 py-1 rounded text-indigo-400 border border-indigo-500/20">
                  MJPEG
                </span>
              )}
            </div>
          </div>

          <div className="flex-1 bg-black/40 relative min-h-[480px] flex items-center justify-center">
            {connState !== "connected" ? (
              <div className="flex flex-col items-center gap-4 text-slate-500">
                <WifiOff className="w-12 h-12 opacity-20" />
                <p className="text-sm font-mono tracking-tight">Connect robot for live stream</p>
                <p className="text-xs text-slate-600">
                  ROSBridge must be running on the robot; stream from /camera/image_raw
                </p>
              </div>
            ) : cameraConnected ? (
              <img
                src={STREAM_URL}
                alt="Robot stream"
                className="w-full h-full object-cover transition-opacity duration-700 ease-in-out"
                onError={() => setCameraConnected(false)}
              />
            ) : (
              <div className="flex flex-col items-center gap-4 text-slate-500">
                <Video className="w-12 h-12 opacity-20" />
                <p className="text-sm font-mono tracking-tight">Camera feed unavailable</p>
                <p className="text-xs text-slate-600">
                  Robot connected; ensure /camera/image_raw is published
                </p>
              </div>
            )}

            <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent pointer-events-none opacity-60" />

            {/* Sensor Overlay */}
            <div className="absolute inset-0 pointer-events-none p-8">
              <div className="w-16 h-16 border-l-2 border-t-2 border-indigo-500/30 absolute top-8 left-8" />
              <div className="w-16 h-16 border-r-2 border-t-2 border-indigo-500/30 absolute top-8 right-8" />
              <div className="w-16 h-16 border-l-2 border-b-2 border-indigo-500/30 absolute bottom-8 left-8" />
              <div className="w-16 h-16 border-r-2 border-b-2 border-indigo-500/30 absolute bottom-8 right-8" />

              <Crosshair className="w-10 h-10 text-white/10 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />

              <div className="absolute bottom-10 left-10 right-10 flex justify-between items-end font-mono">
                <div className="space-y-1 text-emerald-400/80 drop-shadow-md text-xs">
                  <p>
                    YAW:{" "}
                    {connState === "connected" ? (telemetry?.imu?.yaw?.toFixed(1) ?? "0.0") : "—"}°
                  </p>
                  <p>
                    PITCH:{" "}
                    {connState === "connected" ? (telemetry?.imu?.pitch?.toFixed(1) ?? "0.0") : "—"}
                    °
                  </p>
                  <p>
                    ROLL:{" "}
                    {connState === "connected" ? (telemetry?.imu?.roll?.toFixed(1) ?? "0.0") : "—"}°
                  </p>
                  <p className="pt-2 text-indigo-400">
                    VEL_L:{" "}
                    {connState === "connected"
                      ? (telemetry?.velocity?.linear.toFixed(2) ?? "0.00")
                      : "—"}{" "}
                    m/s
                  </p>
                </div>
                <div className="text-right space-y-1 text-slate-400 text-[10px] tracking-widest uppercase">
                  <p>SOTA_CORE: v1.3.0</p>
                  <p>ROS_DOMAIN_ID: 30</p>
                  <p className="text-emerald-500/60 transition-all hover:text-emerald-400 cursor-pointer pointer-events-auto">
                    SYSTEM_ENHANCED_MODE: ON
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar Controls & Stats */}
        <div className="flex flex-col gap-6">
          {/* Chassis Navigation Status */}
          <div className="glass-card p-6 rounded-2xl">
            <h3 className="text-sm uppercase tracking-[0.2em] font-bold text-slate-400 mb-6 flex items-center gap-2">
              <Navigation className="w-4 h-4 text-indigo-400" /> Chassis Status
            </h3>

            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                <span className="text-[10px] text-slate-500 uppercase block mb-1">Heading</span>
                <span className="text-xl font-bold font-mono text-indigo-300">
                  {connState === "connected" ? (telemetry?.imu?.heading?.toFixed(0) ?? "0") : "—"}°
                </span>
              </div>
              <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                <span className="text-[10px] text-slate-500 uppercase block mb-1">Battery</span>
                <span className="text-xl font-bold font-mono text-emerald-400">
                  {connState === "connected" ? (telemetry?.voltage?.toFixed(1) ?? "0.0") : "—"}V
                </span>
              </div>
            </div>

            {/* Sonar Proximity Widget */}
            <div className="mb-6 p-4 rounded-xl bg-indigo-500/5 border border-indigo-500/10 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                  <Zap className="w-4 h-4 text-indigo-400" />
                </div>
                <div>
                  <span className="text-[10px] text-slate-500 uppercase block leading-none mb-1">
                    Sonar Proximity
                  </span>
                  <span className="text-lg font-bold font-mono text-slate-200">
                    {connState === "connected" ? ((telemetry?.sonar_m ?? 0) * 100).toFixed(1) : "—"}{" "}
                    cm
                  </span>
                </div>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-emerald-400 uppercase tracking-widest block font-bold">
                  {connState === "connected" && (telemetry?.sonar_m ?? 0) < 0.3
                    ? "OBSTACLE"
                    : "CLEAR"}
                </span>
              </div>
            </div>
            {connState !== "connected" && (
              <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-4">
                Connect robot for live chassis data
              </p>
            )}

            <div className="flex flex-col items-center gap-3 p-6 bg-black/30 rounded-2xl border border-white/5 overflow-hidden relative">
              <div className="absolute inset-0 bg-indigo-500/5 blur-3xl" />
              <div className="relative z-10 flex flex-col items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-slate-800/80 border border-white/10 flex items-center justify-center font-bold text-slate-200">
                  W
                </div>
                <div className="flex gap-3">
                  <div className="w-10 h-10 rounded-lg bg-slate-800/80 border border-white/10 flex items-center justify-center font-bold text-slate-200">
                    A
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-slate-800/80 border border-white/10 flex items-center justify-center font-bold text-slate-200">
                    S
                  </div>
                  <div className="w-10 h-10 rounded-lg bg-slate-800/80 border border-white/10 flex items-center justify-center font-bold text-slate-200">
                    D
                  </div>
                </div>
                <p className="text-[10px] text-slate-500 uppercase tracking-widest mt-2 font-mono">
                  Drive Override
                </p>
              </div>
            </div>

            {/* Camera PTZ Control */}
            <div className="glass-card p-6 rounded-2xl">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Camera className="text-cyan-500 w-5 h-5" />
                  <h3 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                    Camera PTZ
                  </h3>
                </div>
                <button
                  onClick={() => api.postTool("camera_center")}
                  className="px-2 py-1 bg-white/5 border border-white/10 rounded-lg text-[8px] font-bold text-slate-400 uppercase tracking-widest hover:text-white transition-all"
                >
                  Center
                </button>
              </div>

              <div className="grid grid-cols-3 gap-2 max-w-[100px] mx-auto scale-90">
                <div />
                <button
                  title="Tilt up"
                  onClick={() => api.postTool("camera_move", "up")}
                  className="w-8 h-8 rounded-lg bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 active:scale-95 transition-all"
                >
                  <ChevronUp size={16} />
                </button>
                <div />
                <button
                  title="Pan left"
                  onClick={() => api.postTool("camera_move", "left")}
                  className="w-8 h-8 rounded-lg bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 active:scale-95 transition-all"
                >
                  <ChevronLeft size={16} />
                </button>
                <div className="flex items-center justify-center">
                  <div className="w-1 h-1 rounded-full bg-cyan-500/50" />
                </div>
                <button
                  title="Pan right"
                  onClick={() => api.postTool("camera_move", "right")}
                  className="w-8 h-8 rounded-lg bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 active:scale-95 transition-all"
                >
                  <ChevronRight size={16} />
                </button>
                <div />
                <button
                  title="Tilt down"
                  onClick={() => api.postTool("camera_move", "down")}
                  className="w-8 h-8 rounded-lg bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 active:scale-95 transition-all"
                >
                  <ChevronDown size={16} />
                </button>
                <div />
              </div>
            </div>
          </div>

          {/* Compute Infrastructure */}
          <div className="glass-card p-6 rounded-2xl flex-1">
            <h3 className="text-sm uppercase tracking-[0.2em] font-bold text-slate-400 mb-6 flex items-center gap-2">
              <Zap className="w-4 h-4 text-yellow-400" /> Embedded Payload
            </h3>

            <div className="space-y-5">
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] uppercase font-mono text-slate-400">
                  <span>Raspi 5 SoC Temp</span>
                  <span className="text-slate-200">45°C</span>
                </div>
                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "45%" }}
                    className="h-full bg-indigo-500"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex justify-between text-[10px] uppercase font-mono text-slate-400">
                  <span>Voltage Stability</span>
                  <span className="text-emerald-400">STABLE</span>
                </div>
                <div className="h-1 bg-slate-800 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: "92%" }}
                    className="h-full bg-emerald-500"
                  />
                </div>
              </div>

              <div className="mt-8 pt-6 border-t border-white/5 space-y-4">
                <div className="flex items-start gap-3">
                  <Server className="w-4 h-4 text-slate-500 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-[10px] text-slate-500 uppercase tracking-tight font-mono">
                      Unified Gateway
                    </p>
                    <p className="text-xs text-slate-300 font-mono">localhost:10892</p>
                  </div>
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-2" />
                </div>
                <div className="flex items-start gap-3">
                  <Activity className="w-4 h-4 text-slate-500 mt-0.5" />
                  <div className="flex-1">
                    <p className="text-[10px] text-slate-500 uppercase tracking-tight font-mono">
                      ROS 2 Bridge
                    </p>
                    <p className="text-xs text-slate-300 font-mono">
                      {connState === "connected" ? "/telemetry [active]" : "[offline]"}
                    </p>
                  </div>
                  <div
                    className={`w-1.5 h-1.5 rounded-full mt-2 ${connState === "connected" ? "bg-emerald-500" : "bg-slate-500"}`}
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Global status elements */}
      <div className="fixed bottom-8 left-1/2 -translate-x-1/2 z-20">
        <div className="px-6 py-3 rounded-2xl glass-card backdrop-blur-xl flex items-center gap-8 border-white/5">
          <div className="flex items-center gap-3">
            <Battery className="w-4 h-4 text-emerald-400" />
            <div className="text-left">
              <p className="text-[9px] text-slate-500 uppercase font-mono leading-none">Power</p>
              <p className="text-sm font-bold font-mono text-slate-200">
                {connState === "connected" ? (telemetry?.battery?.toFixed(0) ?? "0") : "—"}%
              </p>
            </div>
          </div>
          <div className="w-px h-8 bg-white/5" />
          <div className="flex items-center gap-3">
            <Compass className="w-4 h-4 text-indigo-400" />
            <div className="text-left">
              <p className="text-[9px] text-slate-500 uppercase font-mono leading-none">Yaw Rate</p>
              <p className="text-sm font-bold font-mono text-slate-200">
                {connState === "connected"
                  ? (telemetry?.velocity?.angular.toFixed(2) ?? "0.00")
                  : "—"}{" "}
                rad/s
              </p>
            </div>
          </div>
          <div className="w-px h-8 bg-white/5" />
          <div className="flex items-center gap-3">
            {connState === "connected" && cameraConnected ? (
              <>
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span className="text-[10px] uppercase tracking-[0.2em] font-bold text-emerald-500/80">
                  Stream Live
                </span>
              </>
            ) : (
              <span className="text-[10px] uppercase tracking-[0.2em] font-bold text-slate-500">
                Stream offline
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Non-Blocking Reconnect Banner */}
      {connState !== "connected" && (
        <div className="fixed top-8 left-1/2 -translate-x-1/2 z-[100] w-[90%] max-w-xl animate-in slide-in-from-top-4 duration-500">
          <div className="glass-card p-4 rounded-2xl border-red-500/20 bg-red-950/20 backdrop-blur-2xl flex items-center justify-between gap-4 shadow-2xl">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-red-500/20 rounded-xl flex items-center justify-center border border-red-500/20">
                <WifiOff className="text-red-500 shrink-0" size={20} />
              </div>
              <div>
                <p className="text-sm font-bold text-white leading-none mb-1">Robot Offline</p>
                <p className="text-[10px] text-slate-400 font-mono tracking-tight">
                  Handshake failed @ 192.168.1.11
                </p>
              </div>
            </div>
            <button
              onClick={handleReconnect}
              disabled={reconnecting}
              className={`px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${
                reconnecting
                  ? "bg-slate-800 text-slate-500 cursor-not-allowed"
                  : "bg-red-600 hover:bg-red-500 text-white shadow-lg shadow-red-600/20"
              }`}
            >
              {reconnecting ? "Handshaking..." : "Reconnect"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
