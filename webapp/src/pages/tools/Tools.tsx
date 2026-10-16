import { motion } from "framer-motion";
import { Check, Code, Loader2, Search, Wrench } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface ToolEntry {
  name: string;
  kind: "portmanteau" | "atomic";
  detail: string;
}

const OP_GROUPS: { title: string; prefix: string[] }[] = [
  {
    title: "Motion + safety",
    prefix: ["health_check", "forward", "backward", "turn", "strafe", "stop"],
  },
  { title: "Sensors", prefix: ["read_"] },
  { title: "Voice + audio", prefix: ["say", "play", "chat_and_say", "audio_"] },
  {
    title: "Display + light",
    prefix: ["display", "clear_display", "led", "light_effect", "patrol_car"],
  },
  { title: "Camera", prefix: ["camera_"] },
  {
    title: "Paths + missions",
    prefix: ["start_recording", "stop_recording", "list_trajectories", "explore"],
  },
  { title: "Robot programs", prefix: ["gripper_"] },
  { title: "Diagnostics", prefix: ["config_show", "inspect_stack", "execute_command"] },
];

const Tools: React.FC = () => {
  const [tools, setTools] = useState<ToolEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .getCapabilities()
      .then((d) => {
        if (cancelled) return;
        const entries: ToolEntry[] = [
          ...(d?.tool_surface?.portmanteau_tools ?? []).map((name) => ({
            name,
            kind: "portmanteau" as const,
            detail: `${d?.features?.available_operations?.length ?? 0} operations via operation= (see groups below)`,
          })),
          ...(d?.tool_surface?.atomic_tools ?? []).map((name) => ({
            name,
            kind: "atomic" as const,
            detail: "Single-purpose MCP tool",
          })),
        ];
        setTools(entries);
        setError(null);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Capability fetch failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const q = query.trim().toLowerCase();
  const filtered = tools.filter(
    (t) => q === "" || t.name.toLowerCase().includes(q) || t.detail.toLowerCase().includes(q),
  );

  return (
    <div data-testid="tools-page" className="space-y-8 py-4 px-4 sm:px-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Wrench className="text-indigo-400 w-8 h-8" />
          <div>
            <h1 className="text-3xl font-bold text-white tracking-tight">MCP Toolroom</h1>
            <p className="text-slate-300 text-sm">
              Live tool surface from GET /api/capabilities — no hardcoded entries.
            </p>
          </div>
        </div>

        <div className="relative hidden md:block">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
          <input
            data-testid="tools-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search tools..."
            className="bg-white/5 border border-white/10 rounded-xl pl-11 pr-6 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/30 transition-all"
          />
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-300 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading tool surface...
        </div>
      )}
      {error && !loading && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          Capability fetch failed: {error}{" "}
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="underline hover:text-white"
          >
            Retry
          </button>
        </div>
      )}
      {!loading && !error && filtered.length === 0 && (
        <p data-testid="tools-empty" className="text-slate-300 text-sm">
          {tools.length === 0
            ? "Backend reported no tools. Is the gateway running?"
            : `No tools match "${query}".`}
        </p>
      )}

      <div data-testid="tools-list" className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filtered.map((tool, i) => (
          <motion.div
            key={tool.name}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(i * 0.05, 0.5) }}
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
                <Check size={10} /> {tool.kind}
              </span>
            </div>
            <p className="text-sm text-slate-300 mb-6 leading-relaxed font-medium">{tool.detail}</p>
            {tool.kind === "portmanteau" && (
              <div className="pt-4 border-t border-white/5">
                <span className="text-[10px] font-bold text-slate-300 uppercase tracking-widest block mb-3">
                  Operation groups
                </span>
                <div className="flex flex-wrap gap-2">
                  {OP_GROUPS.map((g) => (
                    <span
                      key={g.title}
                      className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-[11px] font-mono text-indigo-200/80"
                    >
                      {g.title}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Tools;
