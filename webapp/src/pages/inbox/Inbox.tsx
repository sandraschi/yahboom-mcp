import { Inbox as InboxIcon, Loader2, Search } from "lucide-react";
import type React from "react";
import { useEffect, useRef, useState } from "react";
import { API_BASE, api } from "../../lib/api";

const MAX_LINES = 200;

const Inbox: React.FC = () => {
  const [lines, setLines] = useState<string[]>([]);
  const [live, setLive] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [level, setLevel] = useState<"ALL" | "ERROR" | "WARN">("ALL");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let stopped = false;
    let es: EventSource | null = null;
    // Live event inbox: server-sent log stream (same channel as /logs).
    try {
      es = new EventSource(`${API_BASE}/api/v1/logs/stream`);
      es.onopen = () => {
        if (!stopped) {
          setLive(true);
          setError(null);
        }
      };
      es.onmessage = (ev) => {
        if (stopped) return;
        setLines((prev) => [...prev.slice(-MAX_LINES + 1), ev.data]);
      };
      es.onerror = () => {
        if (stopped) return;
        setLive(false);
        // Fallback: one-shot ring-buffer poll so the inbox never goes blank.
        api
          .getDiagLogs(80)
          .then((d) => {
            if (!stopped && d?.logs) setLines(d.logs.split("\n").slice(-MAX_LINES));
          })
          .catch((e) => {
            if (!stopped) setError(e instanceof Error ? e.message : "Stream failed");
          });
      };
    } catch (e) {
      setLive(false);
      setError(e instanceof Error ? e.message : "Stream failed");
    }
    return () => {
      stopped = true;
      es?.close();
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  const q = query.trim().toLowerCase();
  const filtered = lines.filter((l) => {
    if (level === "ERROR" && !/error|critical|fail/i.test(l)) return false;
    if (level === "WARN" && !/warn|error|critical|fail/i.test(l)) return false;
    return q === "" || l.toLowerCase().includes(q);
  });

  return (
    <div data-testid="inbox-page" className="space-y-6 py-4 px-4 sm:px-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-4">
        <InboxIcon className="text-indigo-400 w-8 h-8" />
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-white tracking-tight">Event Inbox</h1>
          <p className="text-slate-300 text-sm">
            Live server events (SSE)
            {live === true ? " — streaming" : live === false ? " — poll fallback" : ""}
          </p>
        </div>
        <select
          data-testid="inbox-filter"
          value={level}
          onChange={(e) => setLevel(e.target.value as "ALL" | "ERROR" | "WARN")}
          className="bg-slate-800 text-xs text-slate-200 border border-slate-700 rounded px-2 py-1"
        >
          <option value="ALL">All</option>
          <option value="ERROR">Errors</option>
          <option value="WARN">Warnings+</option>
        </select>
        <div className="relative hidden md:block">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 w-4 h-4" />
          <input
            data-testid="inbox-search"
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Filter events..."
            className="bg-white/5 border border-white/10 rounded-xl pl-11 pr-6 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/30 transition-all"
          />
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-950/40 px-4 py-3 text-sm text-red-200">
          Stream error: {error}
        </div>
      )}

      <div
        data-testid="inbox-list"
        className="rounded-3xl border border-white/5 bg-[#0f0f12]/80 p-6 max-h-[60vh] overflow-y-auto font-mono text-xs leading-relaxed"
      >
        {filtered.length === 0 ? (
          <p className="text-slate-300 font-sans text-sm">
            No events yet. Drive the robot or run a mission to generate traffic.
          </p>
        ) : (
          filtered.map((l, i) => (
            <div
              key={i}
              className={
                /error|critical|fail/i.test(l)
                  ? "text-red-300"
                  : /warn/i.test(l)
                    ? "text-amber-200"
                    : "text-slate-300"
              }
            >
              {l}
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
};

export default Inbox;
