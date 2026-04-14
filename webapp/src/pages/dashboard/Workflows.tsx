import { AnimatePresence, motion } from "framer-motion";
import {
  Activity,
  AlertTriangle,
  Clock,
  Coffee,
  Play,
  ShieldAlert,
  Square,
  Sun,
  Terminal as TerminalIcon,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api, type MissionStatus } from "../../lib/api";

const MISSION_METADATA = [
  {
    id: "patrol",
    title: "Patrol Car",
    description:
      "Engage police strobe and siren while patrolling the perimeter in a tactical square pattern.",
    icon: ShieldAlert,
    color: "from-blue-600 to-red-600",
    tags: ["Motion", "Siren", "LEDs"],
  },
  {
    id: "alarm",
    title: "Smart Alarm",
    description: "Slow sunrise LED sequence followed by a gentle voice greeting to start your day.",
    icon: Sun,
    color: "from-orange-500 to-yellow-400",
    tags: ["Lighting", "Voice"],
  },
  {
    id: "briefing",
    title: "Morning Briefing",
    description: "Fetch sensor data and status briefing followed by a morning stretch routine.",
    icon: Coffee,
    color: "from-emerald-500 to-teal-600",
    tags: ["Sensors", "Motion", "Speech"],
  },
];

export default function Workflows() {
  const [status, setStatus] = useState<MissionStatus | null>(null);
  const [loading, setLoading] = useState<string | null>(null);

  // Polling for mission status
  useEffect(() => {
    const poll = async () => {
      try {
        const data = await api.getMissionStatus();
        setStatus(data);
      } catch (err) {
        console.error("Failed to fetch mission status:", err);
      }
    };

    poll();
    const interval = setInterval(poll, 1000);
    return () => clearInterval(interval);
  }, []);

  const runMission = async (id: string) => {
    setLoading(id);
    try {
      await api.postMissionRun(id);
    } catch (err) {
      console.error("Failed to run mission:", err);
    } finally {
      setLoading(null);
    }
  };

  const stopMission = async () => {
    try {
      await api.postMissionStop();
    } catch (err) {
      console.error("Failed to stop mission:", err);
    }
  };

  const isActive = status?.status === "running";

  return (
    <div className="space-y-8 pb-12">
      {/* Header & Global Status */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Mission Control</h1>
          <p className="text-slate-400 mt-1">
            Orchestrate agentic workflows and automated behaviors.
          </p>
        </div>

        <AnimatePresence>
          {isActive && (
            <motion.button
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={stopMission}
              className="flex items-center gap-2 px-6 py-3 bg-red-500/20 text-red-400 border border-red-500/30 rounded-xl hover:bg-red-500/30 transition-colors font-medium shadow-lg shadow-red-500/10"
            >
              <Square size={20} fill="currentColor" />
              ABORT MISSION
            </motion.button>
          )}
        </AnimatePresence>
      </div>

      {/* Primary Mission Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {MISSION_METADATA.map((mission) => {
          const isThisRunning = status?.mission_id === mission.id && isActive;
          const Icon = mission.icon;

          return (
            <motion.div
              key={mission.id}
              whileHover={{ y: -5 }}
              className={`relative overflow-hidden group bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 transition-all duration-300 ${
                isThisRunning
                  ? "ring-2 ring-blue-500/50 border-blue-500/50"
                  : "hover:border-slate-700"
              }`}
            >
              <div
                className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${mission.color} opacity-5 blur-3xl group-hover:opacity-10 transition-opacity`}
              />

              <div className="relative z-10">
                <div
                  className={`w-12 h-12 rounded-xl bg-gradient-to-br ${mission.color} flex items-center justify-center text-white shadow-lg mb-4`}
                >
                  <Icon size={24} />
                </div>

                <h3 className="text-xl font-bold text-white mb-2">{mission.title}</h3>
                <p className="text-slate-400 text-sm leading-relaxed mb-6">{mission.description}</p>

                <div className="flex flex-wrap gap-2 mb-8">
                  {mission.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2 py-1 bg-slate-800/50 text-slate-500 text-[10px] font-bold uppercase tracking-wider rounded-md border border-slate-700/50"
                    >
                      {tag}
                    </span>
                  ))}
                </div>

                <button
                  disabled={isActive || loading === mission.id}
                  onClick={() => runMission(mission.id)}
                  className={`w-full flex items-center justify-center gap-2 py-3 rounded-xl font-bold transition-all ${
                    isThisRunning
                      ? "bg-blue-500/20 text-blue-400 cursor-default"
                      : "bg-slate-800 text-white hover:bg-slate-750 disabled:opacity-50 disabled:cursor-not-allowed active:scale-95"
                  }`}
                >
                  {isThisRunning ? (
                    <>
                      <Activity size={18} className="animate-pulse" />
                      EXECUTING...
                    </>
                  ) : (
                    <>
                      <Play size={18} fill="currentColor" />
                      DEPLOY MISSION
                    </>
                  )}
                </button>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Progress & Logs (Only visible if status exists) */}
      <AnimatePresence>
        {status?.status !== "idle" && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="grid grid-cols-1 lg:grid-cols-3 gap-6"
          >
            {/* Status Panel */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 h-full">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-500/10 text-blue-400 rounded-lg">
                  <Activity size={20} />
                </div>
                <h3 className="text-lg font-bold text-white uppercase tracking-tight">
                  Active State
                </h3>
              </div>

              <div className="space-y-6">
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-slate-400">Mission Progress</span>
                    <span className="text-blue-400 font-mono font-bold">{status?.progress}%</span>
                  </div>
                  <div className="h-3 w-full bg-slate-800 rounded-full overflow-hidden p-0.5 border border-slate-700/50">
                    <motion.div
                      className="h-full bg-gradient-to-r from-blue-600 to-blue-400 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${status?.progress}%` }}
                      transition={{ duration: 0.5 }}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                    <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">
                      Status
                    </div>
                    <div
                      className={`text-sm font-bold uppercase tracking-wide ${
                        status?.status === "running"
                          ? "text-blue-400"
                          : status?.status === "completed"
                            ? "text-emerald-400"
                            : "text-red-400"
                      }`}
                    >
                      {status?.status}
                    </div>
                  </div>
                  <div className="bg-slate-800/30 rounded-xl p-4 border border-slate-700/30">
                    <div className="text-[10px] text-slate-500 uppercase font-bold mb-1">
                      Uptime
                    </div>
                    <div className="text-sm font-mono text-white flex items-center gap-1.5">
                      <Clock size={12} className="text-slate-400" />
                      {status?.uptime}s
                    </div>
                  </div>
                </div>

                {status?.last_error && (
                  <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs">
                    <AlertTriangle size={16} className="shrink-0" />
                    <p>{status.last_error}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Mission Log */}
            <div className="lg:col-span-2 bg-slate-950 border border-slate-800 rounded-2xl overflow-hidden flex flex-col shadow-2xl">
              <div className="px-6 py-4 border-bottom border-slate-800 bg-slate-900/80 backdrop-blur-md flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <TerminalIcon size={18} className="text-blue-400" />
                  <span className="text-sm font-bold text-white uppercase tracking-widest opacity-80 underline underline-offset-4 decoration-blue-500/40">
                    Autonomous Link Stream
                  </span>
                </div>
                <div className="flex gap-1.5">
                  <div className="w-2 h-2 rounded-full bg-slate-700" />
                  <div className="w-2 h-2 rounded-full bg-slate-700" />
                  <div className="w-2 h-2 rounded-full bg-slate-700" />
                </div>
              </div>

              <div className="flex-1 p-6 overflow-y-auto max-h-[320px] font-mono text-xs space-y-3 custom-scrollbar">
                {status?.logs.length === 0 ? (
                  <div className="h-full flex items-center justify-center text-slate-600 italic">
                    Waiting for mission telemetry...
                  </div>
                ) : (
                  status?.logs.map((log, i) => (
                    <motion.div
                      key={i}
                      initial={{ x: -10, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      className="flex items-start gap-3 border-l border-slate-800/50 pl-3 py-0.5"
                    >
                      <span className="text-slate-500 flex-shrink-0">›</span>
                      <span className="text-slate-300 leading-relaxed">{log}</span>
                    </motion.div>
                  ))
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
