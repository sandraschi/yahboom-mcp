import { motion } from "framer-motion";
import { Box, ExternalLink, Globe, Loader2, Search, ShieldCheck, WifiOff } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { API_BASE, api } from "../../lib/api";

interface FleetApp {
  name: string;
  desc: string;
  url: string | null;
  primary: boolean;
  detected: boolean;
}

const Apps: React.FC = () => {
  const [apps, setApps] = useState<FleetApp[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    api
      .getFleetApps()
      .then((d) => {
        if (!cancelled) {
          setApps(d?.apps ?? []);
          setError(null);
        }
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Discovery failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = apps.filter(
    (a) =>
      query.trim() === "" ||
      a.name.toLowerCase().includes(query.toLowerCase()) ||
      a.desc.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div data-testid="apps-page" className="space-y-8 py-4 px-4 sm:px-6">
      <div className="flex items-center gap-4">
        <Box className="text-indigo-400 w-8 h-8" />
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-white tracking-tight">Apps Hub</h1>
          <p className="text-slate-300 text-sm">
            Live fleet discovery: every badge below was probed on mount, not hardcoded.
          </p>
        </div>
        <div className="relative hidden md:block">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
          <input
            data-testid="apps-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search apps..."
            className="bg-white/5 border border-white/10 rounded-xl pl-11 pr-6 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/30 transition-all"
          />
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-300 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Probing companions...
        </div>
      )}
      {error && !loading && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          Discovery failed: {error}{" "}
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
        <p className="text-slate-300 text-sm">
          {apps.length === 0
            ? "No companions answered. This console works standalone."
            : `No apps match "${query}".`}
        </p>
      )}

      <div data-testid="apps-list" className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((app, i) => (
          <motion.div
            key={app.name}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            className={`p-6 rounded-3xl border transition-all group flex flex-col justify-between h-48 ${app.primary ? "bg-indigo-600 border-indigo-500 shadow-xl" : "bg-[#0f0f12]/80 border-white/5 hover:border-white/10 hover:bg-white/[0.04]"}`}
          >
            <div>
              <div className="flex items-center justify-between mb-4">
                <Globe className={`${app.primary ? "text-white" : "text-slate-500"} w-5 h-5`} />
                {app.primary ? (
                  <span className="text-[10px] font-bold text-white/50 uppercase tracking-widest">
                    Active System
                  </span>
                ) : app.detected ? (
                  <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-emerald-400">
                    <ShieldCheck className="w-4 h-4" /> Detected
                  </span>
                ) : (
                  <span className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-widest text-slate-300">
                    <WifiOff className="w-4 h-4" /> Offline
                  </span>
                )}
              </div>
              <h3 className={`text-lg font-bold ${app.primary ? "text-white" : "text-slate-100"}`}>
                {app.name}
              </h3>
              <p
                className={`text-sm font-medium leading-relaxed mt-2 ${app.primary ? "text-indigo-100/70" : "text-slate-300"}`}
              >
                {app.desc}
              </p>
            </div>
            {app.url && (
              <a
                href={app.url.startsWith("http") ? app.url : `${API_BASE}${app.url}`}
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1 text-[10px] font-bold text-indigo-300 opacity-0 group-hover:opacity-100 transition-opacity uppercase tracking-widest"
              >
                External Launch <ExternalLink size={10} />
              </a>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  );
};

export default Apps;
