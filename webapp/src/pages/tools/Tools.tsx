import { motion } from "framer-motion";
import { Check, Code, Search, Wrench } from "lucide-react";
import type React from "react";

const Tools: React.FC = () => {
  const tools = [
    {
      name: "move",
      description: "Primary vector control for omnidirectional wheels.",
      params: ["linear", "angular"],
    },
    {
      name: "stream",
      description: "Enable MJPEG feed from Raspberry Pi camera.",
      params: ["resolution", "fps"],
    },
    {
      name: "trajectory",
      description: "Execute predefined pathing patterns.",
      params: ["path_id"],
    },
    { name: "telemetry", description: "Inspect IMU and battery state.", params: [] },
  ];

  return (
    <div className="space-y-8 py-4 px-4 sm:px-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Wrench className="text-indigo-400 w-8 h-8" />
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">MCP Toolroom</h1>
            <p className="text-slate-400 text-sm">
              Dynamic tool inspection and GrokTools schema discovery.
            </p>
          </div>
        </div>

        <div className="relative hidden md:block">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
          <input
            type="text"
            placeholder="Search tool signature..."
            className="bg-white/5 border border-white/10 rounded-xl pl-11 pr-6 py-2.5 text-sm text-slate-300 focus:outline-none focus:border-indigo-500/30 transition-all"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {tools.map((tool, i) => (
          <motion.div
            key={tool.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="bg-[#0f0f12]/80 border border-white/5 p-6 rounded-3xl hover:border-indigo-500/20 transition-all group backdrop-blur-xl"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/20">
                  <Code className="text-indigo-400 w-5 h-5" />
                </div>
                <h3 className="text-lg font-bold text-white">{tool.name}</h3>
              </div>
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-green-500/10 text-green-400 text-[10px] font-bold uppercase tracking-widest border border-green-500/20">
                <Check size={10} /> Active
              </span>
            </div>
            <p className="text-sm text-slate-400 mb-6 leading-relaxed font-medium">
              {tool.description}
            </p>
            <div className="pt-4 border-t border-white/5">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-3">
                Parameters
              </span>
              <div className="flex flex-wrap gap-2">
                {tool.params.length > 0 ? (
                  tool.params.map((p) => (
                    <span
                      key={p}
                      className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-[11px] font-mono text-indigo-300/80"
                    >
                      {p}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-600 font-medium italic">
                    No interactive parameters
                  </span>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Tools;
