import { Activity, Circle, Pause, Play, Trash2, Wifi, WifiOff } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api, type Health } from "../../lib/api";

const MAX_LINES = 2000;

export default function Logger() {
  const [lines, setLines] = useState<string[]>([]);
  const [paused, setPaused] = useState(false);
  const [sseState, setSseState] = useState<"connecting" | "open" | "error">("connecting");
  const [health, setHealth] = useState<Health | null>(null);
  const pausedRef = useRef(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    pausedRef.current = paused;
  }, [paused]);

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
      es.onerror = () => {
        setSseState("error");
        es?.close();
      };
    };

    connect();

    return () => {
      es?.close();
      es = null;
    };
  }, [appendLine]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const h = await api.getHealth();
        if (!cancelled) setHealth(h);
      } catch {
        if (!cancelled) setHealth(null);
      }
    })();
    const t = setInterval(async () => {
      try {
        const h = await api.getHealth();
        if (!cancelled) setHealth(h);
      } catch {
        if (!cancelled) setHealth(null);
      }
    }, 8000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  useEffect(() => {
    if (paused) return;
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines, paused]);

  const clear = () => setLines([]);

  const copyAll = async () => {
    const text = lines.join("\n");
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      /* ignore */
    }
  };

  const ros = health?.robot_connection?.ros;
  const ip = health?.robot_connection?.ip ?? "—";

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Activity className="w-8 h-8 text-emerald-500" />
            Server logs
          </h1>
          <p className="text-gray-400 mt-1 text-sm max-w-2xl">
            Live tail of the <span className="font-mono text-gray-300">yahboom-mcp</span> in-process
            ring buffer (same process as REST and MCP). Use this when ROS or SSH fails and you need
            the host-side story.
          </p>
          {health && (
            <p className="text-xs font-mono text-slate-500 mt-2">
              Bridge target <span className="text-indigo-400">{ip}</span>
              <span className="mx-2 text-slate-600">|</span>
              ROS <span className={ros === "connected" ? "text-emerald-400" : "text-amber-400"}>{ros}</span>
            </p>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-mono ${
              sseState === "open"
                ? "border-emerald-500/30 text-emerald-400 bg-emerald-500/5"
                : sseState === "connecting"
                  ? "border-amber-500/30 text-amber-400 bg-amber-500/5"
                  : "border-red-500/30 text-red-400 bg-red-500/5"
            }`}
          >
            {sseState === "open" ? <Wifi className="w-3.5 h-3.5" /> : <WifiOff className="w-3.5 h-3.5" />}
            SSE {sseState}
          </div>
          <button
            type="button"
            onClick={() => setPaused((p) => !p)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/10 text-xs font-semibold text-slate-200 hover:bg-white/5"
          >
            {paused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
            {paused ? "Resume" : "Pause"}
          </button>
          <button
            type="button"
            onClick={clear}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-white/10 text-xs font-semibold text-slate-200 hover:bg-white/5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear
          </button>
          <button
            type="button"
            onClick={copyAll}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-indigo-500/30 text-xs font-semibold text-indigo-300 hover:bg-indigo-500/10"
          >
            Copy all
          </button>
        </div>
      </div>

      <div
        ref={scrollRef}
        className="bg-[#0a0a0c] border border-gray-800 rounded-xl overflow-hidden font-mono text-[11px] leading-relaxed"
      >
        <div className="px-4 py-2 border-b border-gray-800 flex items-center justify-between text-[10px] uppercase tracking-wider text-gray-500">
          <span className="flex items-center gap-2">
            <Circle className="w-2 h-2 fill-emerald-500 text-emerald-500" />
            /api/v1/logs/stream
          </span>
          <span>{lines.length} lines (max {MAX_LINES})</span>
        </div>
        <div className="h-[min(70vh,720px)] overflow-y-auto p-4 text-emerald-600/90 whitespace-pre-wrap break-all custom-scrollbar">
          {lines.length === 0 ? (
            <span className="text-gray-600 italic">
              {sseState === "connecting"
                ? "Waiting for log lines…"
                : sseState === "error"
                  ? "Stream error — is the backend on :10892 running? Reload the page after starting webapp/start.ps1."
                  : "No log lines yet (try an action in the app to generate traffic)."}
            </span>
          ) : (
            lines.map((line, i) => (
              <div key={i} className="hover:bg-white/[0.02]">
                {line}
              </div>
            ))
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <p className="text-xs text-slate-500">
        Uvicorn HTTP access lines are filtered for noisy poll routes; this view is application logs
        only. For ROS topic introspection when connected, see{" "}
        <Link to="/diagnostics" className="text-indigo-400 hover:underline">
          Diagnostic Hub
        </Link>
        .
      </p>
    </div>
  );
}
