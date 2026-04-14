import { motion } from "framer-motion";
import { AlertCircle, Cpu, Loader2, MessageSquare, Send, User } from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { api, type ChatMessage } from "../../lib/api";

interface Message {
  role: "user" | "ai";
  content: string;
}

const INITIAL_AI =
  "Greetings. G1 Substrate Link sequence complete. I am ready for manual or autonomous directives. What is our objective?";

const Chat: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([{ role: "ai", content: INITIAL_AI }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [modelHint, setModelHint] = useState<string | null>(null);

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

  const handleSubmit = async (e?: React.FormEvent) => {
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
  };

  return (
    <div className="h-full flex flex-col py-4 px-4 sm:px-6 max-w-5xl mx-auto">
      <div className="flex items-center gap-4 mb-8">
        <MessageSquare className="text-indigo-400 w-8 h-8" />
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">AI Companion</h1>
          <p className="text-slate-400 text-sm">
            Natural language interface for Yahboom Raspbot v2.{" "}
            {modelHint ? `Model: ${modelHint}` : "Select a model in Settings."}
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-4 flex items-center gap-2 bg-red-500/10 border border-red-500/20 rounded-xl px-4 py-2 text-red-400 text-sm">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          {error}
        </div>
      )}

      <div className="flex-1 bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 flex flex-col min-h-0 shadow-2xl backdrop-blur-xl">
        <div className="flex-1 overflow-y-auto space-y-6 mb-8 pr-4 scrollbar-thin">
          {messages.map((msg, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: msg.role === "ai" ? -10 : 10 }}
              animate={{ opacity: 1, x: 0 }}
              className={`flex gap-4 ${msg.role === "user" ? "flex-row-reverse text-right" : ""}`}
            >
              <div
                className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  msg.role === "ai"
                    ? "bg-indigo-500/20 text-indigo-400"
                    : "bg-slate-700/50 text-slate-300"
                }`}
              >
                {msg.role === "ai" ? <Cpu size={20} /> : <User size={20} />}
              </div>
              <div
                className={`p-5 rounded-2xl text-sm leading-relaxed max-w-[80%] ${
                  msg.role === "ai"
                    ? "bg-white/5 text-slate-200 border border-white/5"
                    : "bg-indigo-600 text-white"
                }`}
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
              <div className="p-5 rounded-2xl text-sm text-slate-500">Thinking…</div>
            </motion.div>
          )}
        </div>

        <form onSubmit={handleSubmit} className="relative group">
          <input
            type="text"
            placeholder="Command robot or ask about system status..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={loading}
            className="w-full bg-white/5 border border-white/10 rounded-2xl px-6 py-4 pr-16 text-sm text-slate-200 focus:outline-none focus:border-indigo-500/50 transition-all group-focus-within:bg-white/[0.08] disabled:opacity-50"
          />
          <button
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
