import { motion } from "framer-motion";
import { Box, ExternalLink, Globe, ShieldCheck } from "lucide-react";
import type React from "react";

const Apps: React.FC = () => {
  const apps = [
    {
      name: "Advanced Memory",
      desc: "Neural knowledge graph and long-term storage.",
      status: "Active",
    },
    { name: "Devices MCP", desc: "Fleet-wide Tapo camera orchestration.", status: "Offline" },
    { name: "Games Dash", desc: "AI-Orchestrated game analysis platform.", status: "Active" },
    { name: "Yahboom Console", desc: "You are currently here.", status: "Primary" },
  ];

  return (
    <div className="space-y-8 py-4 px-4 sm:px-6">
      <div className="flex items-center gap-4">
        <Box className="text-indigo-400 w-8 h-8" />
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Apps Hub</h1>
          <p className="text-slate-400 text-sm">
            Real-time Fleet Discovery and navigation for MCP services.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {apps.map((app, i) => (
          <motion.div
            key={app.name}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            className={`p-6 rounded-3xl border transition-all cursor-pointer group flex flex-col justify-between h-48 ${app.status === "Primary" ? "bg-indigo-600 border-indigo-500 shadow-xl" : "bg-[#0f0f12]/80 border-white/5 hover:border-white/10 hover:bg-white/[0.04]"}`}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <Globe
                  className={`${app.status === "Primary" ? "text-white" : "text-slate-500"} w-5 h-5`}
                />
                {app.status === "Active" && <ShieldCheck className="text-green-400 w-4 h-4" />}
                {app.status === "Primary" && (
                  <span className="text-[10px] font-bold text-white/50 uppercase tracking-widest">
                    Active System
                  </span>
                )}
              </div>
              <h3
                className={`text-lg font-bold ${app.status === "Primary" ? "text-white" : "text-slate-200"}`}
              >
                {app.name}
              </h3>
              <p
                className={`text-xs font-medium leading-relaxed mt-2 ${app.status === "Primary" ? "text-indigo-100/70" : "text-slate-500"}`}
              >
                {app.desc}
              </p>
            </div>
            {app.status !== "Primary" && (
              <div className="flex items-center gap-1 text-[10px] font-bold text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest">
                External Launch <ExternalLink size={10} />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Apps;
