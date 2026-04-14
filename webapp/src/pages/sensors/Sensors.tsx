import { Gauge, RefreshCw, WifiOff } from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { api, isBridgeLiveTelemetry, type SensorsResponse } from "../../lib/api";

const POLL_MS = 500;

const IR_LABELS = ["FL", "F", "FR", "R", "BR", "B", "BL", "L"];

/** Labels for line array length (Yahboom drivers often use 3 or 4 channels) */
function lineChannelLabels(n: number): string[] {
  if (n === 3) return ["L", "C", "R"];
  if (n === 4) return ["L", "ML", "MR", "R"];
  if (n === 5) return ["L", "ML", "C", "MR", "R"];
  return Array.from({ length: n }, (_, i) => `Ch${i + 1}`);
}

function formatLineCell(v: number | null): string {
  if (v == null || Number.isNaN(v)) return "—";
  if (v === 0 || v === 1) return v === 1 ? "LINE" : "off";
  if (Number.isInteger(v)) return String(v);
  return v.toFixed(2);
}

const SensorsPage: React.FC = () => {
  const [data, setData] = useState<SensorsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSensors = useCallback(async () => {
    try {
      const res = await api.getSensors();
      setData(res);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sensors");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSensors();
    const id = setInterval(fetchSensors, POLL_MS);
    return () => clearInterval(id);
  }, [fetchSensors]);

  const irValues: (number | null)[] = Array.isArray(data?.ir_proximity)
    ? (data.ir_proximity as (number | null)[]).map((v) =>
        typeof v === "number" && !Number.isNaN(v) ? v : null,
      )
    : typeof data?.sonar_m === "number"
      ? [null, data.sonar_m, ...Array(6).fill(null)]
      : [];
  const lineValues: (number | null)[] = Array.isArray(data?.line_sensors)
    ? (data.line_sensors as unknown[]).map((v) => {
        if (typeof v === "number" && !Number.isNaN(v)) return v;
        if (typeof v === "string" && v.trim() !== "") {
          const n = parseInt(v, 10);
          return Number.isNaN(n) ? null : n;
        }
        return null;
      })
    : [];
  const lineSlotCount = lineValues.length > 0 ? lineValues.length : 5;
  const displayLine: (number | null)[] =
    lineValues.length > 0 ? lineValues : Array.from({ length: lineSlotCount }, () => null);
  const lineLabels = lineChannelLabels(lineSlotCount);

  if (loading && !data) {
    return (
      <div className="flex items-center justify-center py-24 text-slate-500">
        <RefreshCw className="w-8 h-8 animate-spin mr-2" />
        Loading sensors…
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full py-4 px-4 sm:px-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Gauge className="text-indigo-400 w-8 h-8" />
          <div>
            <h1 className="text-2xl font-bold text-white tracking-tight">Sensors</h1>
            <p className="text-slate-400 text-sm">IR proximity and line-following front sensors.</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {isBridgeLiveTelemetry(data) ? (
            <span className="px-3 py-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 text-xs font-bold uppercase">
              Live
            </span>
          ) : (
            <span className="px-3 py-1.5 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-400 text-xs font-bold uppercase flex items-center gap-1.5">
              <WifiOff size={12} />
              Offline
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-200 text-sm">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* IR proximity sensors */}
        <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">
            IR proximity sensors
          </h2>
          <p className="text-xs text-slate-500 mb-4">
            Distance readings (m). Configure ROS topic on robot to see live values.
          </p>
          <div className="flex flex-wrap gap-3">
            {(irValues.length ? irValues : Array.from({ length: 8 }, () => null)).map((val, i) => (
              <div
                key={i}
                className="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10 min-w-[3.5rem]"
              >
                <span className="text-[10px] text-slate-500 uppercase font-mono">
                  {IR_LABELS[i] ?? `IR${i}`}
                </span>
                <span className="text-sm font-mono text-slate-200 mt-1">
                  {val != null ? val.toFixed(2) : "—"}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Line-following front sensors */}
        <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">
            Line-following front sensors
          </h2>
          <p className="text-xs text-slate-500 mb-4">
            Binary IR line sensors (0 = floor, 1 = line). Topic{" "}
            <code className="text-indigo-400">/line_sensor</code>, type{" "}
            <code className="text-indigo-400">std_msgs/msg/Int32MultiArray</code>. Override with{" "}
            <code className="text-indigo-400">YAHBOOM_LINE_TOPIC</code> /{" "}
            <code className="text-indigo-400">YAHBOOM_LINE_MSG_TYPE</code> if remapped.
          </p>
          <div className="flex justify-center gap-2 flex-wrap">
            {displayLine.map((val, i) => (
              <div
                key={i}
                className="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10 flex-1 max-w-[4.5rem] min-w-[3rem]"
              >
                <span className="text-[10px] text-slate-500 uppercase font-mono">
                  {lineLabels[i]!}
                </span>
                <span
                  className={`text-sm font-mono mt-1 ${
                    val === 1 ? "text-emerald-400 font-bold" : "text-slate-300"
                  }`}
                >
                  {formatLineCell(val)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SensorsPage;
