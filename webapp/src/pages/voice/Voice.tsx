/**
 * Voice.tsx — Boomy Voice & Audio Control
 *
 * Covers current hardware: Yahboom CSK4002 AI Voice Module (USB serial)
 *
 * What this page does:
 *   - Probe voice module status (get_status)
 *   - Trigger preset phrases by ID 1–85 via binary serial protocol
 *   - espeak-ng arbitrary TTS via SSH
 *   - ALSA volume control
 *   - Listen for recognition events (non-blocking, 5s timeout)
 *
 * All calls go through POST /api/v1/control/tool (portmanteau).
 * See: docs/hardware/VOICE_AUDIO.md for protocol reference.
 */

import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Loader2,
  Mic,
  MicOff,
  Radio,
  RefreshCw,
  Send,
  Speaker,
  Volume2,
  VolumeX,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

// ── Types ────────────────────────────────────────────────────────────────────

interface VoiceStatus {
  device: string | null;
  device_found: boolean;
  pyserial_ok: boolean;
  espeak_ok: boolean;
  baud: number;
  note: string;
}

interface ListenResult {
  command_id: number | null;
  status: "recognised" | "timeout" | "error";
}

// ── Preset phrase map — discovered by running listen() while speaking commands
// IDs are firmware-dependent; update these after running the discovery script
// described in docs/hardware/VOICE_AUDIO.md §4 (Preset Phrase Vocabulary)
const PRESET_PHRASES: { id: number; label: string; category: string }[] = [
  { id: 1,  label: "Greeting / Beep",    category: "System"  },
  { id: 2,  label: "Ready",              category: "System"  },
  { id: 3,  label: "OK / Confirmed",     category: "System"  },
  { id: 4,  label: "Go Forward",         category: "Motion"  },
  { id: 5,  label: "Go Backward",        category: "Motion"  },
  { id: 6,  label: "Turn Left",          category: "Motion"  },
  { id: 7,  label: "Turn Right",         category: "Motion"  },
  { id: 8,  label: "Stop",               category: "Motion"  },
  { id: 9,  label: "Speed Up",           category: "Motion"  },
  { id: 10, label: "Slow Down",          category: "Motion"  },
  { id: 11, label: "Obstacle Avoid ON",  category: "Mode"    },
  { id: 12, label: "Obstacle Avoid OFF", category: "Mode"    },
  { id: 13, label: "Follow Me ON",       category: "Mode"    },
  { id: 14, label: "Follow Me OFF",      category: "Mode"    },
  { id: 15, label: "Patrol ON",          category: "Mode"    },
  { id: 16, label: "Patrol OFF",         category: "Mode"    },
  { id: 17, label: "Lights ON",          category: "Light"   },
  { id: 18, label: "Lights OFF",         category: "Light"   },
  { id: 19, label: "Battery Report",     category: "System"  },
  { id: 20, label: "Low Battery",        category: "System"  },
];

const CATEGORY_COLORS: Record<string, string> = {
  System: "indigo",
  Motion: "emerald",
  Mode:   "amber",
  Light:  "yellow",
};

// ── API helpers ───────────────────────────────────────────────────────────────

async function voiceTool(operation: string, param1?: string | number, param2?: string | number) {
  const res = await fetch("/api/v1/control/tool", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ operation, param1, param2 }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Sub-components ────────────────────────────────────────────────────────────

function HardwareStatus({ status, loading, onRefresh }: {
  status: VoiceStatus | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  const ok = status?.device_found && status?.pyserial_ok;
  return (
    <div className="flex items-center gap-3">
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin text-zinc-500" />
      ) : ok ? (
        <CheckCircle2 className="w-4 h-4 text-emerald-500" />
      ) : (
        <AlertTriangle className="w-4 h-4 text-amber-500" />
      )}
      <div>
        <p className="text-[10px] font-black uppercase tracking-widest text-zinc-400">
          {loading ? "Probing..." : ok ? status?.device ?? "CSK4002 OK" : "Module Offline"}
        </p>
        {status && !loading && (
          <p className="text-[9px] text-zinc-600 font-mono">
            {status.baud} baud · {status.pyserial_ok ? "pyserial ✓" : "pyserial ✗"} · {status.espeak_ok ? "espeak ✓" : "espeak ✗"}
          </p>
        )}
      </div>
      <button
        onClick={onRefresh}
        className="ml-1 p-1.5 rounded-lg bg-white/5 text-zinc-600 hover:text-zinc-300 hover:bg-white/10 transition-all"
      >
        <RefreshCw className="w-3.5 h-3.5" />
      </button>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function Voice() {
  // Status
  const [status, setStatus] = useState<VoiceStatus | null>(null);
  const [statusLoading, setStatusLoading] = useState(true);

  // Preset playback
  const [playingId, setPlayingId] = useState<number | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  // espeak TTS
  const [ttsText, setTtsText] = useState("");
  const [ttsBusy, setTtsBusy] = useState(false);
  const [ttsResult, setTtsResult] = useState<"ok" | "error" | null>(null);

  // Volume
  const [volume, setVolume] = useState(75);
  const [volumeBusy, setVolumeBusy] = useState(false);
  const volumeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Listen
  const [listening, setListening] = useState(false);
  const [lastRecognition, setLastRecognition] = useState<ListenResult | null>(null);

  // Log of last events
  const [eventLog, setEventLog] = useState<{ time: string; msg: string; type: "info" | "ok" | "warn" }[]>([]);

  const pushLog = useCallback((msg: string, type: "info" | "ok" | "warn" = "info") => {
    setEventLog(prev => [
      { time: new Date().toLocaleTimeString("de-AT", { hour: "2-digit", minute: "2-digit", second: "2-digit" }), msg, type },
      ...prev.slice(0, 19),
    ]);
  }, []);

  const refreshStatus = useCallback(async () => {
    setStatusLoading(true);
    try {
      const res = await voiceTool("get_status");
      setStatus(res.result as VoiceStatus);
      pushLog(res.result?.device_found ? `Device found: ${res.result.device}` : "Voice module not detected", res.result?.device_found ? "ok" : "warn");
    } catch (e) {
      pushLog("Status probe failed — is backend running?", "warn");
    } finally {
      setStatusLoading(false);
    }
  }, [pushLog]);

  useEffect(() => { refreshStatus(); }, [refreshStatus]);

  // ── Preset play ─────────────────────────────────────────────────────────────
  const handlePlay = async (phraseId: number, label: string) => {
    setPlayingId(phraseId);
    pushLog(`Playing preset #${phraseId}: ${label}`);
    try {
      await voiceTool("play", phraseId);
      pushLog(`Preset #${phraseId} sent → [0xA5, 0x${phraseId.toString(16).padStart(2,"0").toUpperCase()}, 0x${(~phraseId & 0xFF).toString(16).padStart(2,"0").toUpperCase()}]`, "ok");
    } catch (e) {
      pushLog(`Play #${phraseId} failed`, "warn");
    } finally {
      setTimeout(() => setPlayingId(null), 800);
    }
  };

  // ── TTS ─────────────────────────────────────────────────────────────────────
  const handleTts = async () => {
    if (!ttsText.trim()) return;
    setTtsBusy(true);
    setTtsResult(null);
    pushLog(`espeak-ng: "${ttsText.slice(0, 40)}${ttsText.length > 40 ? "…" : ""}"`);
    try {
      await voiceTool("say", ttsText);
      setTtsResult("ok");
      pushLog("TTS spoken via espeak-ng", "ok");
    } catch {
      setTtsResult("error");
      pushLog("TTS failed — check espeak-ng on Pi", "warn");
    } finally {
      setTtsBusy(false);
      setTimeout(() => setTtsResult(null), 2500);
    }
  };

  // ── Volume ──────────────────────────────────────────────────────────────────
  const handleVolumeChange = (val: number) => {
    setVolume(val);
    if (volumeTimer.current) clearTimeout(volumeTimer.current);
    volumeTimer.current = setTimeout(async () => {
      setVolumeBusy(true);
      try {
        await voiceTool("volume", val);
        pushLog(`ALSA volume → ${val}%`, "ok");
      } catch {
        pushLog("Volume set failed", "warn");
      } finally {
        setVolumeBusy(false);
      }
    }, 400);
  };

  // ── Listen ──────────────────────────────────────────────────────────────────
  const handleListen = async () => {
    if (listening) return;
    setListening(true);
    setLastRecognition(null);
    pushLog("Listening for wake/recognition event (5s timeout)…");
    try {
      const res = await voiceTool("listen", 5);
      const result = res.result as ListenResult;
      setLastRecognition(result);
      if (result.command_id !== null) {
        const phrase = PRESET_PHRASES.find(p => p.id === result.command_id);
        pushLog(`Recognised ID ${result.command_id}${phrase ? ` → ${phrase.label}` : ""}`, "ok");
      } else {
        pushLog("Listen timeout — no event received", "warn");
      }
    } catch {
      pushLog("Listen failed", "warn");
    } finally {
      setListening(false);
    }
  };

  const categories = ["all", ...Array.from(new Set(PRESET_PHRASES.map(p => p.category)))];
  const filtered = selectedCategory === "all" ? PRESET_PHRASES : PRESET_PHRASES.filter(p => p.category === selectedCategory);

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-10 font-sans">
      <div className="max-w-[1400px] mx-auto space-y-10">

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div className="flex items-start justify-between gap-6 flex-wrap">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <Speaker className="w-8 h-8 text-purple-500" />
              Voice & Audio
            </h1>
            <p className="text-zinc-500 text-xs mt-1 font-mono tracking-wide">
              Yahboom CSK4002 · USB serial · 115200 baud · binary protocol [0xA5, id, ~id]
            </p>
          </div>
          <HardwareStatus status={status} loading={statusLoading} onRefresh={refreshStatus} />
        </div>

        {/* ── Limitation notice ───────────────────────────────────────────────── */}
        <div className="p-5 rounded-2xl bg-amber-500/5 border border-amber-500/15 flex items-start gap-4">
          <AlertTriangle className="w-5 h-5 text-amber-500/70 mt-0.5 flex-shrink-0" />
          <div className="space-y-1">
            <p className="text-[11px] font-black uppercase tracking-widest text-amber-500/80">Hardware Limitation</p>
            <p className="text-[11px] text-zinc-500 leading-relaxed">
              The CSK4002 module has a fixed firmware vocabulary of 85 preset phrases — it cannot synthesise arbitrary text.
              The <strong className="text-zinc-400">Preset Phrases</strong> panel triggers those presets via binary serial.
              The <strong className="text-zinc-400">TTS</strong> panel uses espeak-ng on the Pi over ALSA — a separate audio path with no echo cancellation.
              Upgrade path: <span className="text-indigo-400">Voice Upgrade</span> page (ReSpeaker Lite + Piper TTS).
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">

          {/* ── Left column: preset phrases ──────────────────────────────────── */}
          <div className="xl:col-span-2 space-y-6">

            {/* Category filter */}
            <div className="flex items-center gap-2 flex-wrap">
              {categories.map(cat => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-4 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all border ${
                    selectedCategory === cat
                      ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-400"
                      : "bg-zinc-900 border-white/5 text-zinc-600 hover:text-zinc-300 hover:border-white/10"
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            {/* Phrase grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
              {filtered.map(phrase => {
                const col = CATEGORY_COLORS[phrase.category] ?? "zinc";
                const isPlaying = playingId === phrase.id;
                return (
                  <motion.button
                    key={phrase.id}
                    whileTap={{ scale: 0.93 }}
                    onClick={() => handlePlay(phrase.id, phrase.label)}
                    disabled={playingId !== null}
                    className={`relative overflow-hidden rounded-2xl p-4 text-left border transition-all disabled:opacity-40 ${
                      isPlaying
                        ? `bg-${col}-500/15 border-${col}-500/40`
                        : `bg-zinc-900/60 border-white/5 hover:bg-zinc-900 hover:border-white/10`
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <span className={`text-[9px] font-black uppercase tracking-widest ${
                        isPlaying ? `text-${col}-400` : "text-zinc-600"
                      }`}>
                        #{phrase.id}
                      </span>
                      {isPlaying ? (
                        <Loader2 className={`w-3.5 h-3.5 animate-spin text-${col}-400`} />
                      ) : (
                        <Zap className="w-3.5 h-3.5 text-zinc-700" />
                      )}
                    </div>
                    <p className="text-[11px] font-bold text-zinc-300 leading-tight">{phrase.label}</p>
                    <p className={`text-[9px] mt-1 font-medium ${
                      isPlaying ? `text-${col}-500/70` : "text-zinc-700"
                    }`}>{phrase.category}</p>
                    {isPlaying && (
                      <motion.div
                        className={`absolute bottom-0 left-0 h-0.5 bg-${col}-500`}
                        initial={{ width: "0%" }}
                        animate={{ width: "100%" }}
                        transition={{ duration: 0.8 }}
                      />
                    )}
                  </motion.button>
                );
              })}
            </div>

            <p className="text-[9px] text-zinc-700 font-mono px-1">
              IDs above are firmware estimates. Run the discovery script (VOICE_AUDIO.md §4) to confirm your module's exact mapping.
            </p>
          </div>

          {/* ── Right column: controls ──────────────────────────────────────── */}
          <div className="space-y-6">

            {/* TTS panel */}
            <div className="rounded-[2rem] bg-zinc-900/40 border border-white/5 p-6 space-y-5">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-purple-500/10 flex items-center justify-center">
                  <Volume2 className="w-4 h-4 text-purple-500" />
                </div>
                <div>
                  <p className="text-[11px] font-black uppercase tracking-widest text-white">Arbitrary TTS</p>
                  <p className="text-[9px] text-zinc-600 font-mono">espeak-ng → ALSA (no AEC)</p>
                </div>
              </div>

              <textarea
                rows={3}
                placeholder="Enter text to speak…"
                value={ttsText}
                onChange={e => setTtsText(e.target.value)}
                onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) handleTts(); }}
                className="w-full bg-black/40 border border-white/5 rounded-2xl p-4 text-sm text-white placeholder-zinc-700 resize-none focus:outline-none focus:border-purple-500/30 focus:ring-2 focus:ring-purple-500/10 transition-all font-mono leading-relaxed"
              />

              <button
                onClick={handleTts}
                disabled={ttsBusy || !ttsText.trim()}
                className={`w-full flex items-center justify-center gap-2 py-3 rounded-2xl font-black text-[11px] uppercase tracking-widest transition-all border ${
                  ttsResult === "ok"
                    ? "bg-emerald-500/20 border-emerald-500/30 text-emerald-400"
                    : ttsResult === "error"
                    ? "bg-red-500/20 border-red-500/30 text-red-400"
                    : "bg-purple-500/10 border-purple-500/20 text-purple-400 hover:bg-purple-500/20 disabled:opacity-30"
                }`}
              >
                {ttsBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                {ttsBusy ? "Speaking…" : ttsResult === "ok" ? "Spoken ✓" : ttsResult === "error" ? "Failed ✗" : "Speak"}
              </button>
            </div>

            {/* Volume */}
            <div className="rounded-[2rem] bg-zinc-900/40 border border-white/5 p-6 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {volume === 0 ? <VolumeX className="w-4 h-4 text-zinc-500" /> : <Volume2 className="w-4 h-4 text-indigo-400" />}
                  <p className="text-[11px] font-black uppercase tracking-widest text-white">ALSA Volume</p>
                </div>
                <div className="flex items-center gap-2">
                  {volumeBusy && <Loader2 className="w-3 h-3 animate-spin text-zinc-500" />}
                  <span className="text-sm font-black text-indigo-400 font-mono w-8 text-right">{volume}</span>
                </div>
              </div>
              <input
                type="range" min={0} max={100} value={volume}
                onChange={e => handleVolumeChange(parseInt(e.target.value))}
                className="w-full h-1.5 appearance-none rounded-full bg-zinc-800 accent-indigo-500 cursor-pointer"
              />
              <p className="text-[9px] text-zinc-600">Controls Pi ALSA master. Does not affect module's internal speaker.</p>
            </div>

            {/* Listen panel */}
            <div className="rounded-[2rem] bg-zinc-900/40 border border-white/5 p-6 space-y-4">
              <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-xl flex items-center justify-center transition-all ${
                  listening ? "bg-red-500/20" : "bg-indigo-500/10"
                }`}>
                  {listening ? <Mic className="w-4 h-4 text-red-400 animate-pulse" /> : <MicOff className="w-4 h-4 text-indigo-400" />}
                </div>
                <div>
                  <p className="text-[11px] font-black uppercase tracking-widest text-white">Recognition Listen</p>
                  <p className="text-[9px] text-zinc-600 font-mono">5s window · 0xA5 packet</p>
                </div>
              </div>

              <button
                onClick={handleListen}
                disabled={listening}
                className={`w-full py-3 rounded-2xl font-black text-[11px] uppercase tracking-widest transition-all border flex items-center justify-center gap-2 ${
                  listening
                    ? "bg-red-500/10 border-red-500/20 text-red-400 cursor-not-allowed"
                    : "bg-indigo-500/10 border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/20"
                }`}
              >
                {listening ? <><Loader2 className="w-4 h-4 animate-spin" /> Listening…</> : <><Radio className="w-4 h-4" /> Listen (5s)</>}
              </button>

              <AnimatePresence>
                {lastRecognition && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`p-4 rounded-xl border text-[10px] font-mono ${
                      lastRecognition.command_id !== null
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                        : "bg-zinc-800/40 border-white/5 text-zinc-500"
                    }`}
                  >
                    {lastRecognition.command_id !== null ? (
                      <>
                        <p className="font-black">ID = {lastRecognition.command_id}</p>
                        <p className="text-emerald-500/60 mt-0.5">
                          {PRESET_PHRASES.find(p => p.id === lastRecognition.command_id)?.label ?? "Unknown phrase"}
                        </p>
                      </>
                    ) : (
                      <p>Timeout — no recognition event received</p>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

          </div>
        </div>

        {/* ── Event log ──────────────────────────────────────────────────────── */}
        <div className="rounded-[2rem] bg-zinc-900/30 border border-white/5 p-6">
          <div className="flex items-center gap-3 mb-4">
            <Cpu className="w-4 h-4 text-zinc-600" />
            <p className="text-[10px] font-black uppercase tracking-widest text-zinc-500">Event Log</p>
          </div>
          <div className="space-y-1 font-mono text-[10px] max-h-40 overflow-y-auto scrollbar-none">
            {eventLog.length === 0 && (
              <p className="text-zinc-700">No events yet.</p>
            )}
            {eventLog.map((e, i) => (
              <div key={i} className="flex items-start gap-3">
                <span className="text-zinc-700 flex-shrink-0">{e.time}</span>
                <span className={
                  e.type === "ok" ? "text-emerald-500/80" :
                  e.type === "warn" ? "text-amber-500/80" :
                  "text-zinc-500"
                }>
                  {e.msg}
                </span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
