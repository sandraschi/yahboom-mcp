import { Activity, ArrowDown, ArrowUp, Circle, Copy, Download, Filter, Pause, Play, Trash2, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { type Health, api } from "../../lib/api";

const MAX_LINES = 2000;

export default function Logger() {
  const [lines, setLines] = useState<string[]>([]);
  const [paused, setPaused] = useState(false);
  const [sseState, setSseState] = useState<"connecting" | "open" | "error">("connecting");
  const [health, setHealth] = useState<Health | null>(null);
  const [filter, setFilter] = useState("");
  const [sortAsc, setSortAsc] = useState(false);
  const pausedRef = useRef(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => { pausedRef.current = paused; }, [paused]);

  const appendLine = useCallback((raw: string) => {
    if (pausedRef.current) return;
    setLines((prev) => {
      const next = [...prev, raw];
      if (next.length > MAX_LINES) return next.slice(-MAX_LINES);
      return next;
    });
  }, []);

  useEffect(() => {
    let es: EventSource | null = null;
    setSseState("connecting");
    const connect = () => {
      es?.close();
      es = new EventSource("/api/v1/logs/stream");
      es.onopen = () => setSseState("open");
      es.onmessage = (ev) => {
        const text = typeof ev.data === "string" ? ev.data : String(ev.data);
        if (text) appendLine(text);
      };
      es.onerror = () => { setSseState("error"); es?.close(); };
    };
    connect();
    return () => { es?.close(); };
  }, [appendLine]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try { const h = await api.getHealth(); if (!cancelled) setHealth(h); } catch { if (!cancelled) setHealth(null); }
    })();
    const t = setInterval(async () => {
      try { const h = await api.getHealth(); if (!cancelled) setHealth(h); } catch { if (!cancelled) setHealth(null); }
    }, 8000);
    return () => { cancelled = true; clearInterval(t); };
  }, []);

  useEffect(() => {
    if (paused || sortAsc) return;
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines, paused, sortAsc]);

  const filteredLines = useMemo(() => {
    if (!filter.trim()) return lines;
    const q = filter.toLowerCase();
    return lines.filter((l) => l.toLowerCase().includes(q));
  }, [lines, filter]);

  const displayLines = useMemo(() => {
    return sortAsc ? [...filteredLines].reverse() : filteredLines;
  }, [filteredLines, sortAsc]);

  const clear = () => setLines([]);

  const copyAll = async () => {
    const text = displayLines.join("\n");
    if (!text) return;
    try { await navigator.clipboard.writeText(text); } catch {}
  };

  const exportLog = () => {
    const text = displayLines.join("\n");
    if (!text) return;
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `yahboom-mcp-${new Date().toISOString().slice(0, 19).replace(/:/g, "-")}.log`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const ros = health?.robot_connection?.ros;
  const ip = health?.robot_connection?.ip ?? "—";

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-4 animate-in fade-in duration-500">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Activity className="w-7 h-7 text-emerald-500" />
            Server logs
          </h1>
          <p className="text-slate-400 mt-1 text-sm">
            Live tail of <span className="font-mono text-slate-300">yahboom-mcp</span> in-process ring buffer.
          </p>
          {health && (
            <p className="text-sm font-mono text-slate-500 mt-1.5">
              Target <span className="text-indigo-400">{ip}</span> · ROS{" "}
              <span className={ros === "connected" ? "text-emerald-400" : "text-amber-400"}>{ros}</span>
            </p>
          )}
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/10 bg-[#0f0f12] flex-1 min-w-[200px] max-w-md">
          <Filter className="w-3.5 h-3.5 text-slate-500 shrink-0" />
          <input
            type="text"
            placeholder="Filter…"
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-transparent text-sm text-slate-200 placeholder-slate-600 outline-none w-full"
          />
          {filter && (
            <button onClick={() => setFilter("")} className="text-slate-500 hover:text-slate-300 text-xs">clear</button>
          )}
        </div>

        <span className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-mono ${
          sseState === "open" ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/5"
            : sseState === "connecting" ? "border-amber-500/30 text-amber-400 bg-amber-500/5"
            : "border-red-500/30 text-red-400 bg-red-500/5"
        }`}>
          {sseState === "open" ? <Wifi className="w-3 h-3" /> : <WifiOff className="w-3 h-3" />}
          {sseState}
        </span>

        <button onClick={() => setPaused((p) => !p)}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/10 text-xs font-medium text-slate-300 hover:bg-white/5"
          title={paused ? "Resume tail" : "Pause tail"}>
          {paused ? <Play className="w-3 h-3" /> : <Pause className="w-3 h-3" />}
          {paused ? "Tail off" : "Tail on"}
        </button>

        <button onClick={() => setSortAsc((s) => !s)}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-white/10 text-xs font-medium text-slate-300 hover:bg-white/5"
          title={sortAsc ? "Newest first" : "Oldest first"}>
          {sortAsc ? <ArrowDown className="w-3 h-3" /> : <ArrowUp className="w-3 h-3" />}
          {sortAsc ? "Newest" : "Oldest"}
        </button>

        <button onClick={exportLog}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-emerald-500/20 text-xs font-medium text-emerald-300 hover:bg-emerald-500/10">
          <Download className="w-3 h-3" /> Export
        </button>

        <button onClick={copyAll}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-indigo-500/20 text-xs font-medium text-indigo-300 hover:bg-indigo-500/10">
          <Copy className="w-3 h-3" /> Copy
        </button>

        <button onClick={clear}
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-red-500/20 text-xs font-medium text-red-300 hover:bg-red-500/10">
          <Trash2 className="w-3 h-3" /> Clear
        </button>
      </div>

      {/* Log lines */}
      <div className="bg-[#0a0a0c] border border-white/5 rounded-xl overflow-hidden">
        <div className="px-4 py-2 border-b border-white/5 flex items-center justify-between text-xs text-slate-500">
          <span className="flex items-center gap-2">
            <Circle className="w-1.5 h-1.5 fill-emerald-500 text-emerald-500" />
            /api/v1/logs/stream
          </span>
          <span>{filteredLines.length} of {lines.length} lines (max {MAX_LINES})</span>
        </div>
        <div className="h-[min(70vh,720px)] overflow-y-auto p-4 font-mono text-sm leading-relaxed text-slate-300 whitespace-pre-wrap break-all">
          {displayLines.length === 0 ? (
            <span className="text-slate-600 italic">
              {sseState === "connecting" ? "Waiting for log lines..." : sseState === "error" ? "Stream error — is the backend running?" : "No log lines yet."}
            </span>
          ) : (
            displayLines.map((line, i) => (
              <div key={i} className="hover:bg-white/[0.03] py-px">{line}</div>
            ))
          )}
          {!sortAsc && <div ref={bottomRef} />}
        </div>
      </div>

      <p className="text-xs text-slate-600">
        Application logs only (Uvicorn access filtered). For ROS introspection see{" "}
        <Link to="/diagnostics" className="text-indigo-400 hover:underline">Diagnostic Hub</Link>.
      </p>
    </div>
  );
}
