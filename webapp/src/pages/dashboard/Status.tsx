import { motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Battery,
  CheckCircle2,
  Compass,
  Gauge,
  Loader2,
  Navigation,
  Radio,
  Unplug,
} from "lucide-react";
import { useEffect, useState } from "react";
import StackStatusTable from "../../components/StackStatusTable";
import { type Health, type Telemetry, api, isBridgeLiveTelemetry } from "../../lib/api";

export default function Status() {
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let alive = true;
    const poll = async () => {
      try {
        const [t, h] = await Promise.all([api.getTelemetry(), api.getHealth()]);
        if (!alive) return;
        setTelemetry(t);
        setConnected(isBridgeLiveTelemetry(t));
        setHealth(h);
      } catch {
        if (!alive) return;
        setConnected(false);
        setTelemetry(null);
      }
    };
    poll();
    const id = setInterval(poll, 2000);
    return () => { alive = false; clearInterval(id); };
  }, []);

  const rc = health?.robot_connection;
  const robotIp = rc?.ip ?? "—";
  const allGood = !!health && connected;
  const partialRobot = !!health && !connected && rc?.ssh === "connected";
  const noRobotPath = !!health && !connected && rc?.ssh !== "connected";

  return (
    <div className="flex flex-col gap-6 p-4 lg:p-8 animate-in fade-in">
      <div className="flex items-center gap-3">
        <Activity className="text-indigo-400 w-7 h-7" />
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">System Status</h1>
          <p className="text-sm text-slate-400">Connection health, telemetry, and stack diagnostics.</p>
        </div>
      </div>

      {/* Connection Banner */}
      <motion.section
        layout
        className={`rounded-3xl border p-5 lg:p-6 ${
          allGood ? "border-emerald-500/30 bg-emerald-950/35"
            : partialRobot ? "border-amber-500/35 bg-amber-950/40"
            : "border-red-500/35 bg-red-950/45"
        }`}
      >
        <div className="flex items-start gap-4">
          {allGood ? <CheckCircle2 className="w-9 h-9 text-emerald-400 shrink-0 mt-0.5" />
            : partialRobot ? <Radio className="w-9 h-9 text-amber-400 shrink-0 mt-0.5" />
            : <AlertTriangle className="w-9 h-9 text-red-400 shrink-0 mt-0.5" />}
          <div className="min-w-0">
            <h2 className="text-lg font-bold text-white">
              {allGood ? "Robot connected" : partialRobot ? "Pi reachable — ROS bridge down" : "No connection"}
            </h2>
            <p className="text-sm text-slate-400 mt-1 font-mono">
              Target <span className="text-indigo-300">{robotIp}</span>
              {health && (
                <>
                  {" · "}ROS <span className={rc?.ros === "connected" ? "text-emerald-400" : "text-slate-500"}>{rc?.ros ?? "—"}</span>
                  {" · "}SSH <span className={rc?.ssh === "connected" ? "text-emerald-400" : "text-slate-500"}>{rc?.ssh ?? "—"}</span>
                  {" · "}Video <span className={rc?.video === "active" ? "text-emerald-400" : "text-slate-500"}>{rc?.video ?? "—"}</span>
                  {typeof rc?.cmd_vel_ready === "boolean" && (
                    <>{" · "}cmd_vel <span className={rc.cmd_vel_ready ? "text-emerald-400" : "text-amber-400"}>{rc.cmd_vel_ready ? "ready" : "n/a"}</span></>
                  )}
                </>
              )}
            </p>
            {rc?.hint && <p className="text-sm text-amber-200/85 mt-2">{rc.hint}</p>}
          </div>
        </div>
      </motion.section>

      {/* Telemetry Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard icon={<Battery className="w-5 h-5 text-emerald-400" />} label="Battery" value={telemetry?.battery != null ? `${telemetry.battery}%` : "—"} sub={`${telemetry?.voltage ?? "—"}V`} />
        <StatCard icon={<Compass className="w-5 h-5 text-indigo-400" />} label="Heading" value={telemetry?.imu?.heading != null ? `${telemetry.imu.heading}°` : "—"} sub={`yaw ${telemetry?.imu?.yaw ?? "—"}°`} />
        <StatCard icon={<Navigation className="w-5 h-5 text-cyan-400" />} label="Velocity" value={`${(telemetry?.velocity?.linear ?? 0).toFixed(2)} m/s`} sub={`${(telemetry?.velocity?.angular ?? 0).toFixed(2)} rad/s`} />
        <StatCard icon={<Gauge className="w-5 h-5 text-amber-400" />} label="Sonar" value={telemetry?.sonar_m != null ? `${telemetry.sonar_m}m` : "—"} sub={telemetry?.scan?.nearest_m != null ? `lidar ${telemetry.scan.nearest_m}m` : "no lidar"} />
      </div>

      {/* Stack Health Table */}
      {health?.stack && (
        <motion.section layout className="rounded-3xl border border-white/10 bg-[#0f0f12]/80 p-5 lg:p-6 backdrop-blur-xl">
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-4">Stack Health</h3>
          <StackStatusTable stack={health.stack} />
        </motion.section>
      )}

      {/* Server Info */}
      {health?.system && (
        <div className="rounded-3xl border border-white/5 bg-[#0f0f12]/80 p-5 backdrop-blur-xl">
          <div className="flex items-center gap-3 text-sm text-slate-400">
            <span>Server uptime: <span className="text-white font-mono">{(health.system.uptime / 60).toFixed(0)} min</span></span>
            <span className="text-slate-600">|</span>
            <span>Version: <span className="text-white font-mono">{health.system.version}</span></span>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, sub }: { icon: React.ReactNode; label: string; value: string; sub: string }) {
  return (
    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-2xl p-4 backdrop-blur-xl">
      <div className="flex items-center justify-between mb-3">
        <div className="w-9 h-9 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">{icon}</div>
      </div>
      <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">{label}</p>
      <p className="text-xl font-bold text-white tracking-tight">{value}</p>
      <p className="text-xs text-slate-500 mt-1">{sub}</p>
    </div>
  );
}
