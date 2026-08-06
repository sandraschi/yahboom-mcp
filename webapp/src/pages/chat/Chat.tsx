import { motion } from "framer-motion";
import {
  AlertCircle,
  Cpu,
  Download,
  Eraser,
  Loader2,
  MessageSquare,
  Send,
  Sparkles,
  User,
  Wifi,
  WifiOff,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { type ChatMessage, api } from "../../lib/api";

const LS_HISTORY = "yahboom-chat-history";
const LS_PERSONALITY = "yahboom-chat-personality";
const MAX_HISTORY = 100;

interface Message {
  role: "user" | "ai";
  content: string;
}

const INITIAL_AI =
  "Greetings. G1 Substrate Link sequence complete. I am ready for manual or autonomous directives. What is our objective?";

const PERSONALITIES = [
  {
    id: "operator",
    label: "Robot Operator",
    prompt:
      "You are a robot operator. Be precise, safety-conscious, and authoritative in controlling hardware.",
  },
  {
    id: "engineer",
    label: "Robotics Engineer",
    prompt:
      "You are a robotics engineer. Focus on motor control, sensor fusion, and autonomous navigation.",
  },
  {
    id: "teacher",
    label: "STEM Educator",
    prompt: "You are a STEM educator. Explain robotics concepts clearly with practical examples.",
  },
  { id: "custom", label: "Custom", prompt: "" },
];

const EXAMPLE_PROMPTS = [
  "Move forward 0.5 meters",
  "Rotate 90 degrees left",
  "Show camera feed",
  "Read ultrasonic sensor",
  "Follow the line",
  "Emergency stop",
  "Battery status check",
  "Execute autonomous patrol",
  "Calibrate motors",
];

function loadHistory(): Message[] {
  try {
    const s = localStorage.getItem(LS_HISTORY);
    if (s) return JSON.parse(s);
  } catch {
    return [];
  }
  return [];
}

const Chat: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [messages, setMessages] = useState<Message[]>(() => {
    const saved = loadHistory();
    if (saved.length > 0) return saved;
    return [{ role: "ai", content: INITIAL_AI }];
  });
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelHint, setModelHint] = useState<string | null>(null);
  const [personality, setPersonality] = useState(
    () => localStorage.getItem(LS_PERSONALITY) || "operator",
  );
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    try {
      localStorage.setItem(LS_HISTORY, JSON.stringify(messages.slice(-MAX_HISTORY)));
    } catch {
      /* ignore */
    }
  }, [messages]);

  useEffect(() => {
    localStorage.setItem(LS_PERSONALITY, personality);
  }, [personality]);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => setBackendOk(r.ok))
      .catch(() => setBackendOk(false));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const prompt = searchParams.get("prompt");
    if (prompt) {
      setInput(decodeURIComponent(prompt));
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const loadLlmHint = useCallback(async () => {
    try {
      const llm = await api.getLlmSettings();
      if (llm?.model) setModelHint(llm.model);
    } catch {
      setModelHint(null);
    }
  }, []);

  useEffect(() => {
    loadLlmHint();
  }, [loadLlmHint]);

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      const text = input.trim();
      if (!text || loading) return;
      setInput("");
      setError(null);
      const userMessage: Message = { role: "user", content: text };
      setMessages((prev) => [...prev, userMessage]);
      setLoading(true);

      try {
        const history: ChatMessage[] = [
          ...messages.map((m) => ({
            role: m.role === "ai" ? ("assistant" as const) : "user",
            content: m.content,
          })),
          { role: "user", content: text },
        ];
        const res = await api.postChat(history);
        const content = res?.message?.content ?? "No response.";
        setMessages((prev) => [...prev, { role: "ai", content }]);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Request failed";
        setError(msg);
        setMessages((prev) => [...prev, { role: "ai", content: `Error: ${msg}` }]);
      } finally {
        setLoading(false);
      }
    },
    [input, loading, messages],
  );

  const handleClear = useCallback(() => {
    setMessages([]);
    setError(null);
    try {
      localStorage.removeItem(LS_HISTORY);
    } catch {
      /* ignore */
    }
  }, []);

  const handleExport = useCallback(() => {
    const text = messages.map((m) => `[${m.role.toUpperCase()}] ${m.content}`).join("\n\n");
    const blob = new Blob([text], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `yahboom-chat-${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }, [messages]);

  return (
    <div
      data-testid="chat-page"
      className="h-full flex flex-col py-4 px-4 sm:px-6 max-w-5xl mx-auto"
    >
      <div className="flex items-center gap-4 mb-4">
        <MessageSquare className="text-indigo-400 w-8 h-8" />
        <div className="flex-1">
          <h1 className="text-3xl font-bold text-white tracking-tight">AI Companion</h1>
          <p className="text-slate-400 text-sm">
            Natural language interface for Yahboom Raspbot v2.{" "}
            {modelHint ? `Model: ${modelHint}` : "Select a model in Settings."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-wider text-slate-500 font-mono bg-slate-800 px-2 py-0.5 rounded">
            skill:robot-operator
          </span>
          <select
            data-testid="personality-select"
            value={personality}
            onChange={(e) => setPersonality(e.target.value)}
            className="bg-slate-800 text-xs text-slate-300 border border-slate-700 rounded px-2 py-1"
          >
            {PERSONALITIES.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          {backendOk === true && (
            <span className="flex items-center gap-1 text-xs text-emerald-400">
              <Wifi className="w-3 h-3" />
              Online
            </span>
          )}
          {backendOk === false && (
            <span className="flex items-center gap-1 text-xs text-red-400">
              <WifiOff className="w-3 h-3" />
              Offline
            </span>
          )}
          {backendOk === null && (
            <span className="flex items-center gap-1 text-xs text-slate-500">
              <Loader2 className="w-3 h-3 animate-spin" />
              ...
            </span>
          )}
        </div>
      </div>

      <div data-testid="example-prompts" className="flex flex-wrap gap-1.5 mb-3">
        {EXAMPLE_PROMPTS.map((p) => (
          <button
            key={p}
            onClick={() => setInput(p)}
            className="flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] border border-slate-700 text-slate-400 hover:text-white hover:border-indigo-500/40 transition-colors bg-slate-900/50"
          >
            <Sparkles className="w-2.5 h-2.5" />
            {p}
          </button>
        ))}
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="flex-1 bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 flex flex-col min-h-0 shadow-2xl backdrop-blur-xl">
        <div
          data-testid="chat-messages"
          className="flex-1 overflow-y-auto space-y-6 mb-8 pr-4 scrollbar-thin"
        >
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: msg.role === "ai" ? -10 : 10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse text-right" : ""}`}
            >
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${msg.role === "ai" ? "bg-indigo-500/20 text-indigo-400" : "bg-slate-700/50 text-slate-300"}`}
              >
                {msg.role === "ai" ? <Cpu size={20} /> : <User size={20} />}
              </div>
              <div
                className={`p-5 rounded-2xl text-sm leading-relaxed max-w-[80%] ${msg.role === "ai" ? "bg-white/5 text-slate-200 border border-white/5" : "bg-indigo-600 text-white"}`}
              >
                {msg.content}
              </div>
            </motion.div>
          ))}
          {loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-4">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 bg-indigo-500/20 text-indigo-400">
                <Loader2 size={20} className="animate-spin" />
              </div>
              <div className="p-5 rounded-2xl text-sm text-slate-500">Thinking\u2026</div>
            </motion.div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="flex gap-1 mb-2">
          <button
            data-testid="chat-export"
            onClick={handleExport}
            disabled={messages.length === 0}
            className="p-1.5 rounded text-slate-500 hover:text-slate-300 disabled:opacity-30"
            title="Export"
          >
            <Download className="w-3.5 h-3.5" />
          </button>
          <button
            data-testid="chat-clear"
            onClick={handleClear}
            disabled={messages.length === 0}
            className="p-1.5 rounded text-slate-500 hover:text-slate-300 disabled:opacity-30"
            title="Clear"
          >
            <Eraser className="w-3.5 h-3.5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="relative group">
          <input
            data-testid="chat-input"
            type="text"
            placeholder="Command robot or ask about system status..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 pr-16 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 transition-all group-focus-within:bg-white/[0.08] disabled:opacity-50"
          />
          <button
            data-testid="chat-send"
            type="submit"
            disabled={loading || !input.trim()}
            className="absolute right-3 top-1/2 -translate-y-1/2 w-10 h-10 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white flex items-center justify-center transition-all shadow-lg shadow-indigo-600/20 group-focus-within:scale-105 active:scale-95 disabled:opacity-50 disabled:pointer-events-none"
          >
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
};

export default Chat;
