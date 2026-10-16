import { BookOpen, Loader2, Search } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";

interface SkillEntry {
  name: string;
  uri: string;
}

const Skills: React.FC = () => {
  const [skills, setSkills] = useState<SkillEntry[]>([]);
  const [prompts, setPrompts] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.getSkills(), api.getCapabilities()])
      .then(([s, c]) => {
        if (cancelled) return;
        setSkills(s?.skills ?? []);
        const inv = (c as { inventory?: { prompt_names?: string[] } })?.inventory;
        setPrompts(inv?.prompt_names ?? []);
        setError(null);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Skill fetch failed");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const q = query.trim().toLowerCase();
  const filtered = skills.filter(
    (s) => q === "" || s.name.toLowerCase().includes(q) || s.uri.toLowerCase().includes(q),
  );

  return (
    <div data-testid="skills-page" className="space-y-8 py-4 px-4 sm:px-6">
      <div className="flex items-center gap-4">
        <BookOpen className="text-indigo-400 w-8 h-8" />
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-white tracking-tight">Skills</h1>
          <p className="text-slate-300 text-sm">
            Registered skill prompts — the same texts merged into the chat system prompt.
          </p>
        </div>
        <div className="relative hidden md:block">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
          <input
            data-testid="skills-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search skills..."
            className="bg-white/5 border border-white/10 rounded-xl pl-11 pr-6 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/30 transition-all"
          />
        </div>
      </div>

      {loading && (
        <div className="flex items-center gap-2 text-slate-300 text-sm">
          <Loader2 className="w-4 h-4 animate-spin" /> Loading skills...
        </div>
      )}
      {error && !loading && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          Skill fetch failed: {error}{" "}
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
          {skills.length === 0 ? "No skills registered." : `No skills match "${query}".`}
        </p>
      )}

      <div data-testid="skills-list" className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {filtered.map((s) => (
          <div
            key={s.name}
            className="bg-[#0f0f12]/80 border border-white/5 p-6 rounded-3xl hover:border-indigo-500/20 transition-all backdrop-blur-xl"
          >
            <h3 className="text-lg font-bold text-white">{s.name}</h3>
            <p className="text-sm text-slate-300 mt-2 font-mono break-all">{s.uri}</p>
          </div>
        ))}
      </div>

      {prompts.length > 0 && (
        <div className="pt-4 border-t border-white/5">
          <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wide mb-2">
            Mission prompts
          </h2>
          <div className="flex flex-wrap gap-2">
            {prompts.map((p) => (
              <span
                key={p}
                className="px-3 py-1.5 rounded-lg bg-white/5 border border-white/5 text-[11px] font-mono text-indigo-200/80"
              >
                {p}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default Skills;
