import { AnimatePresence, motion } from "framer-motion";
import { Bot, Loader2, Play, RefreshCw, Send, Target } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

const SAMPLE_MISSIONS = [
  { label: "Square Patrol", goal: "Patrol in a square: move forward 2 seconds, turn left 90 degrees, repeat 4 times, then stop and report battery." },
  { label: "Spin Scan", goal: "Do a full 360 spin scan: turn right slowly for 5 seconds to look around, then stop and report what you see." },
  { label: "Forward Recon", goal: "Move forward 3 seconds slowly, scanning for obstacles. If clear, report success. If blocked, stop and report." },
  { label: "Room Search", goal: "Search the room in a sinusoidal pattern: move forward while weaving left and right. Stop if you detect an object." },
];

export default function Missions() {
  const [goal, setGoal] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ plan?: Record<string, unknown>; message?: string; error?: string } | null>(null);
  const [status, setStatus] = useState<string | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const poll = async () => {
      try {
        const h = await api.getHealth();
        setConnected(h.robot_connection.ros === "connected");
      } catch { setConnected(false); }
    };
    poll();
    const id = setInterval(poll, 5000);
    return () => clearInterval(id);
  }, []);

  const sendMission = async (missionGoal: string) => {
    setLoading(true);
    setResult(null);
    setStatus("Planning mission via Ollama on the robot...");
    try {
      const res = await api.postAgentMission({ goal: missionGoal });
      setResult(res);
      if (res.success) {
        setStatus(res.message || "Mission sent to robot.");
      } else {
        setStatus(`Failed: ${res.error || "unknown"}`);
      }
    } catch (e: unknown) {
      setStatus(`Error: ${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 p-4 lg:p-8 animate-in fade-in">
      <div className="flex items-center gap-3">
        <Bot className="text-indigo-400 w-7 h-7" />
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Autonomous Missions</h1>
          <p className="text-sm text-slate-400">Send natural-language goals to the robot. The onboard LLM plans and the mission executor runs them.</p>
        </div>
      </div>

      {/* Connection status */}
      <div className={`rounded-xl border px-4 py-3 text-sm ${connected ? "border-emerald-500/30 bg-emerald-950/35 text-emerald-400" : "border-amber-500/30 bg-amber-950/35 text-amber-400"}`}>
        {connected ? "ROS connected — robot is ready for missions." : "ROS disconnected — robot cannot receive missions."}
      </div>

      {/* Mission input */}
      <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl">
        <div className="flex items-center gap-2 mb-4">
          <Target className="text-indigo-400 w-4 h-4" />
          <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Mission Prompt</h3>
        </div>
        <textarea
          value={goal}
          onChange={(e) => setGoal(e.target.value)}
          placeholder="Describe what you want the robot to do... e.g. 'patrol the room in a square and report battery when done'"
          rows={3}
          className="w-full bg-black/40 border border-white/5 rounded-2xl p-4 text-sm text-slate-200 placeholder-slate-600 outline-none focus:border-indigo-500/30 resize-none"
          disabled={!connected || loading}
        />
        <div className="flex items-center justify-between mt-3">
          <span className="text-xs text-slate-600">Uses Ollama (Gemma3:1b) on the Pi to generate a structured mission plan.</span>
          <button
            onClick={() => sendMission(goal)}
            disabled={!connected || loading || !goal.trim()}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-sm font-bold text-white transition-all"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
            {loading ? "Planning..." : "Send Mission"}
          </button>
        </div>
      </div>

      {/* Sample missions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {SAMPLE_MISSIONS.map((m) => (
          <button
            key={m.label}
            onClick={() => { setGoal(m.goal); }}
            disabled={!connected || loading}
            className="text-left bg-[#0f0f12]/80 border border-white/5 rounded-2xl p-4 hover:border-indigo-500/20 hover:bg-indigo-500/5 transition-all disabled:opacity-40"
          >
            <div className="flex items-center gap-2 mb-1">
              <Play className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-sm font-bold text-white">{m.label}</span>
            </div>
            <p className="text-xs text-slate-500 line-clamp-2">{m.goal}</p>
          </button>
        ))}
      </div>

      {/* Status & Report Back */}
      <AnimatePresence>
        {(status || result) && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl"
          >
            <div className="flex items-center gap-2 mb-4">
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin text-indigo-400" : "text-emerald-400"}`} />
              <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider">Report Back</h3>
            </div>
            {status && (
              <div className="mb-3 p-3 rounded-xl bg-white/5 border border-white/5">
                <p className="text-sm text-slate-300">{status}</p>
              </div>
            )}
            {result?.plan && (
              <div className="p-3 rounded-xl bg-black/40 border border-white/5">
                <p className="text-xs text-slate-500 mb-2 uppercase tracking-wider">Mission Plan</p>
                <pre className="text-xs text-slate-300 font-mono whitespace-pre-wrap overflow-x-auto">
                  {JSON.stringify(result.plan, null, 2)}
                </pre>
              </div>
            )}
            {result?.error && (
              <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/20">
                <p className="text-sm text-red-400">{result.error}</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
