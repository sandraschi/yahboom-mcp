/**
 * VoiceUpgrade.tsx — Planned Audio Upgrade: ReSpeaker Lite + Piper TTS
 *
 * MOCK PAGE — hardware not yet purchased.
 * This page shows what the audio subsystem will look like once upgraded.
 * All controls are disabled and clearly labelled as mock/planned.
 *
 * Planned hardware:
 *   Seeed ReSpeaker Lite (XMOS XU316) — ~€24 from Seeed DE warehouse
 *   Speaker via 3.5mm jack on WM8960 codec
 *
 * Planned software:
 *   Piper TTS (rhasspy/piper) — neural offline TTS, real-time on Pi 5
 *   Vosk STT from ReSpeaker mic (open vocabulary)
 *   chatbot.py — wake → STT → Ollama → Piper loop
 *
 * See: docs/hardware/VOICE_AUDIO_UPGRADE.md
 */

import type React from "react";
import { motion } from "framer-motion";
import {
  AlertTriangle,
  BrainCircuit,
  ExternalLink,
  Mic,
  ShoppingCart,
  Sparkles,
  Volume2,
  Wand2,
  Waves,
  Zap,
} from "lucide-react";

// ── Mock voice models ─────────────────────────────────────────────────────────
const PIPER_VOICES = [
  { id: "en_US-lessac-medium",    lang: "EN", locale: "en-US", name: "Lessac",   quality: "Medium", size: "63 MB", recommended: true  },
  { id: "en_GB-alan-medium",      lang: "EN", locale: "en-GB", name: "Alan",     quality: "Medium", size: "61 MB", recommended: false },
  { id: "de_DE-thorsten-medium",  lang: "DE", locale: "de-DE", name: "Thorsten", quality: "Medium", size: "89 MB", recommended: true  },
  { id: "en_US-ryan-medium",      lang: "EN", locale: "en-US", name: "Ryan",     quality: "Medium", size: "64 MB", recommended: false },
];

// ── Mock chatbot states for the preview ───────────────────────────────────────
const CHATBOT_DEMO_TURNS = [
  { role: "user",  text: "Hi Yahboom — what's the battery level?" },
  { role: "boomy", text: "Battery is at 78 percent. Voltage stable at 11.6 volts. All systems nominal." },
  { role: "user",  text: "Hi Yahboom — go do a patrol." },
  { role: "boomy", text: "Initiating patrol sequence. Moving to perimeter. Obstacle avoidance is active." },
];

// ── Mock latency data ─────────────────────────────────────────────────────────
const LATENCY_STAGES = [
  { label: "Wake detection",  ms: 100,  color: "indigo",  note: "CSK4002 hardware (unchanged)" },
  { label: "Audio capture",   ms: 3000, color: "blue",    note: "3s window, AEC active on XU316" },
  { label: "Vosk STT",        ms: 500,  color: "cyan",    note: "clean input → faster" },
  { label: "Ollama gemma3:1b",ms: 2000, color: "purple",  note: "~20 words" },
  { label: "Piper TTS",       ms: 200,  color: "violet",  note: "first audio chunk" },
];
const TOTAL_MS = LATENCY_STAGES.reduce((s, x) => s + x.ms, 0);

// ── Badge ─────────────────────────────────────────────────────────────────────
function MockBadge() {
  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/25 text-amber-400 text-[9px] font-black uppercase tracking-widest">
      <AlertTriangle className="w-3 h-3" />
      Mock — Hardware Not Installed
    </span>
  );
}

function SectionCard({ children, glow = "indigo" }: { children: React.ReactNode; glow?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-[2.5rem] border border-white/5 bg-zinc-900/40 p-8 backdrop-blur-2xl`}>
      <div className={`absolute top-0 right-0 w-48 h-48 bg-${glow}-500/5 blur-[80px] rounded-full -mr-16 -mt-16 pointer-events-none`} />
      <div className="relative z-10">{children}</div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────
export default function VoiceUpgrade() {
  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-10 font-sans">
      <div className="max-w-[1400px] mx-auto space-y-10">

        {/* ── Header ─────────────────────────────────────────────────────────── */}
        <div className="space-y-4">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
                <Sparkles className="w-8 h-8 text-indigo-400" />
                Voice Upgrade
              </h1>
              <p className="text-zinc-500 text-xs mt-1 font-mono tracking-wide">
                Seeed ReSpeaker Lite (XMOS XU316) + Piper TTS — planned upgrade
              </p>
            </div>
            <MockBadge />
          </div>

          {/* Purchase card */}
          <div className="p-5 rounded-2xl bg-indigo-500/5 border border-indigo-500/15 flex items-start gap-4">
            <ShoppingCart className="w-5 h-5 text-indigo-400 mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-[11px] font-black uppercase tracking-widest text-indigo-300 mb-1">Purchase Required</p>
              <p className="text-[11px] text-zinc-500 leading-relaxed">
                <strong className="text-zinc-300">Seeed ReSpeaker Lite (XU316)</strong> — ~€24 from Seeed DE warehouse.
                Bare board (no ESP32S3 kit needed — the ESP32S3 is irrelevant when connecting via USB to Pi).
                Piper TTS and Vosk are free software.
              </p>
              <div className="flex flex-wrap gap-2 mt-3">
                <a
                  href="https://www.seeedstudio.com/ReSpeaker-Lite-p-5928.html"
                  target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-500/15 border border-indigo-500/25 text-indigo-400 text-[10px] font-black uppercase tracking-wider hover:bg-indigo-500/25 transition-all"
                >
                  <ExternalLink className="w-3 h-3" /> Seeed Store (DE)
                </a>
                <a
                  href="https://github.com/rhasspy/piper"
                  target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-800 border border-white/5 text-zinc-400 text-[10px] font-black uppercase tracking-wider hover:border-white/10 hover:text-zinc-200 transition-all"
                >
                  <ExternalLink className="w-3 h-3" /> Piper TTS
                </a>
                <a
                  href="https://github.com/m15-ai/TrooperAI"
                  target="_blank" rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-800 border border-white/5 text-zinc-400 text-[10px] font-black uppercase tracking-wider hover:border-white/10 hover:text-zinc-200 transition-all"
                >
                  <ExternalLink className="w-3 h-3" /> TrooperAI Reference
                </a>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">

          {/* ── Piper TTS mock ──────────────────────────────────────────────── */}
          <SectionCard glow="purple">
            <div className="space-y-6">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-purple-500/15 flex items-center justify-center">
                    <Volume2 className="w-4 h-4 text-purple-400" />
                  </div>
                  <div>
                    <p className="text-sm font-black uppercase tracking-widest text-white">Piper TTS</p>
                    <p className="text-[9px] text-zinc-600 font-mono">Neural offline · FastSpeech2 + HiFiGAN</p>
                  </div>
                </div>
                <MockBadge />
              </div>

              {/* Voice selector */}
              <div className="space-y-2">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Voice Model</p>
                <div className="grid grid-cols-1 gap-2">
                  {PIPER_VOICES.map(v => (
                    <div
                      key={v.id}
                      className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-all opacity-50 cursor-not-allowed ${
                        v.recommended
                          ? "bg-purple-500/8 border-purple-500/20"
                          : "bg-zinc-900/60 border-white/5"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className={`text-[9px] font-black px-2 py-0.5 rounded-md ${
                          v.lang === "DE" ? "bg-amber-500/15 text-amber-400" : "bg-indigo-500/15 text-indigo-400"
                        }`}>{v.lang}</span>
                        <div>
                          <p className="text-[11px] font-bold text-zinc-300">{v.name}</p>
                          <p className="text-[9px] text-zinc-600 font-mono">{v.locale} · {v.size}</p>
                        </div>
                      </div>
                      {v.recommended && (
                        <span className="text-[9px] font-black uppercase tracking-widest text-purple-500/60">recommended</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* TTS input (mock) */}
              <div className="space-y-3">
                <textarea
                  rows={3}
                  disabled
                  defaultValue="Battery at 78 percent. Proceeding to patrol waypoint alpha."
                  className="w-full bg-black/20 border border-white/5 rounded-2xl p-4 text-sm text-zinc-500 resize-none font-mono leading-relaxed cursor-not-allowed"
                />
                <div className="flex items-center gap-3">
                  <button disabled className="flex-1 py-3 rounded-2xl bg-purple-500/10 border border-purple-500/15 text-purple-500/40 font-black text-[11px] uppercase tracking-widest cursor-not-allowed flex items-center justify-center gap-2">
                    <Waves className="w-4 h-4" /> Synthesise & Play
                  </button>
                  <div className="text-center px-4">
                    <p className="text-[18px] font-black text-zinc-600">~200ms</p>
                    <p className="text-[9px] text-zinc-700 uppercase tracking-widest">latency</p>
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-xl bg-emerald-500/5 border border-emerald-500/15">
                <p className="text-[10px] text-emerald-500/70 font-mono">
                  vs espeak-ng: ~500ms latency, robotic voice → Piper: ~200ms, natural neural voice
                </p>
              </div>
            </div>
          </SectionCard>

          {/* ── ReSpeaker status mock ────────────────────────────────────────── */}
          <SectionCard glow="cyan">
            <div className="space-y-6">
              <div className="flex items-center justify-between gap-3 flex-wrap">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-xl bg-cyan-500/15 flex items-center justify-center">
                    <Mic className="w-4 h-4 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-sm font-black uppercase tracking-widest text-white">ReSpeaker Lite</p>
                    <p className="text-[9px] text-zinc-600 font-mono">XMOS XU316 · USB UAC 2.0 · zero-driver</p>
                  </div>
                </div>
                <MockBadge />
              </div>

              {/* Spec table */}
              <div className="space-y-2">
                {[
                  ["Chip",           "XMOS XU316 AI Audio DSP"],
                  ["Microphones",    "2× digital MEMS · -26 dBFS · 64 dBA SNR"],
                  ["Far-field",      "3 m with AEC active"],
                  ["USB class",      "UAC 2.0 — plug and play on Pi OS"],
                  ["AEC",            "Hardware · cancels Piper output from mic"],
                  ["Beamforming",    "Dual-mic + XMOS algorithm"],
                  ["Audio output",   "3.5mm jack via WM8960 codec"],
                  ["ALSA device",    "/dev/snd-respeaker (planned udev)"],
                  ["Price",          "~€24 Seeed DE warehouse"],
                ].map(([k, v]) => (
                  <div key={k} className="flex items-start gap-4 py-2 border-b border-white/3 last:border-0">
                    <span className="text-[10px] font-black uppercase tracking-wider text-zinc-600 w-28 flex-shrink-0 pt-0.5">{k}</span>
                    <span className="text-[11px] text-zinc-400 font-mono leading-relaxed">{v}</span>
                  </div>
                ))}
              </div>

              {/* Mock status indicators */}
              <div className="grid grid-cols-3 gap-3">
                {[
                  { label: "Device",     ok: false },
                  { label: "AEC",        ok: false },
                  { label: "Playback",   ok: false },
                ].map(item => (
                  <div key={item.label} className="rounded-xl bg-zinc-800/30 border border-white/5 p-3 text-center opacity-40">
                    <div className="w-2 h-2 rounded-full bg-zinc-600 mx-auto mb-2" />
                    <p className="text-[9px] font-black uppercase tracking-widest text-zinc-600">{item.label}</p>
                  </div>
                ))}
              </div>
              <p className="text-[9px] text-zinc-700 font-mono text-center">Status indicators will be live once hardware is connected</p>
            </div>
          </SectionCard>

        </div>

        {/* ── Latency pipeline ────────────────────────────────────────────────── */}
        <SectionCard glow="indigo">
          <div className="space-y-6">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-3">
                <BrainCircuit className="w-5 h-5 text-indigo-400" />
                <p className="text-sm font-black uppercase tracking-widest text-white">Chatrobot Latency Pipeline</p>
              </div>
              <span className="text-[10px] font-black text-zinc-500 font-mono">
                Total: ~{(TOTAL_MS / 1000).toFixed(1)}s to first spoken word
              </span>
            </div>

            <div className="space-y-3">
              {LATENCY_STAGES.map((stage, i) => {
                const pct = (stage.ms / TOTAL_MS) * 100;
                return (
                  <div key={i} className="space-y-1.5">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="text-[9px] font-black text-zinc-600 w-4 text-right flex-shrink-0">{i + 1}</span>
                        <span className="text-[11px] font-bold text-zinc-300 truncate">{stage.label}</span>
                      </div>
                      <div className="flex items-center gap-3 flex-shrink-0">
                        <span className="text-[9px] text-zinc-600 font-mono hidden sm:block">{stage.note}</span>
                        <span className="text-[11px] font-black text-zinc-400 font-mono w-16 text-right">{stage.ms >= 1000 ? `${stage.ms/1000}s` : `${stage.ms}ms`}</span>
                      </div>
                    </div>
                    <div className="h-1.5 bg-zinc-800 rounded-full overflow-hidden">
                      <motion.div
                        className={`h-full bg-${stage.color}-500 rounded-full`}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                        transition={{ duration: 0.8, delay: i * 0.1, ease: "easeOut" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/15">
              <p className="text-[10px] text-amber-500/70 font-mono">
                With sentence-streaming (Piper plays sentence 1 while generating sentence 2), perceived latency drops to ~3.5s.
                The audio capture window can be shortened once VAD (Voice Activity Detection) is tuned.
              </p>
            </div>
          </div>
        </SectionCard>

        {/* ── Chatrobot conversation preview ───────────────────────────────────── */}
        <SectionCard glow="purple">
          <div className="space-y-6">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <div className="flex items-center gap-3">
                <Wand2 className="w-5 h-5 text-purple-400" />
                <div>
                  <p className="text-sm font-black uppercase tracking-widest text-white">Chatrobot Preview</p>
                  <p className="text-[9px] text-zinc-600 font-mono">Wake → Vosk STT → Ollama gemma3:1b → Piper TTS</p>
                </div>
              </div>
              <MockBadge />
            </div>

            {/* Architecture diagram */}
            <div className="flex items-center gap-2 flex-wrap text-[10px] font-mono">
              {[
                { label: "Hi, Yahboom",     sub: "wake word", color: "indigo"  },
                { label: "CSK4002",          sub: "0xA5 packet", color: "blue"  },
                { label: "ReSpeaker mic",    sub: "AEC active", color: "cyan"   },
                { label: "Vosk STT",         sub: "~500ms", color: "teal"      },
                { label: "Ollama",           sub: "gemma3:1b", color: "purple" },
                { label: "Piper TTS",        sub: "~200ms", color: "violet"    },
                { label: "Speaker",          sub: "3.5mm jack", color: "pink"  },
              ].map((node, i, arr) => (
                <div key={i} className="flex items-center gap-2">
                  <div className={`px-3 py-2 rounded-xl bg-${node.color}-500/10 border border-${node.color}-500/20 text-center`}>
                    <p className={`font-black text-${node.color}-400`}>{node.label}</p>
                    <p className="text-zinc-600">{node.sub}</p>
                  </div>
                  {i < arr.length - 1 && <Zap className="w-3 h-3 text-zinc-700 flex-shrink-0" />}
                </div>
              ))}
            </div>

            {/* Mock conversation */}
            <div className="space-y-3">
              <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Example Exchange</p>
              {CHATBOT_DEMO_TURNS.map((turn, i) => (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: turn.role === "user" ? -10 : 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.15 }}
                  className={`flex gap-3 ${turn.role === "boomy" ? "flex-row-reverse" : ""}`}
                >
                  <div className={`w-7 h-7 rounded-xl flex items-center justify-center flex-shrink-0 text-[9px] font-black ${
                    turn.role === "user" ? "bg-zinc-800 text-zinc-400" : "bg-purple-500/20 text-purple-400"
                  }`}>
                    {turn.role === "user" ? "YOU" : "B"}
                  </div>
                  <div className={`px-4 py-3 rounded-2xl text-[11px] leading-relaxed max-w-[75%] font-mono opacity-70 ${
                    turn.role === "user"
                      ? "bg-zinc-800/60 text-zinc-300"
                      : "bg-purple-500/10 border border-purple-500/15 text-purple-300"
                  }`}>
                    {turn.text}
                  </div>
                </motion.div>
              ))}
              <p className="text-[9px] text-zinc-700 font-mono text-center mt-2">
                Conversation is illustrative — will use Ollama gemma3:1b on Pi 5 with Boomy system prompt
              </p>
            </div>

          </div>
        </SectionCard>

      </div>
    </div>
  );
}
