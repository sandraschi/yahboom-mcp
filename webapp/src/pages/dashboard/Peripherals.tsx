/**
 * Peripherals.tsx — Lightstrip FX + OLED Display
 *
 * Voice/audio controls have moved to /voice.
 *
 * What works:
 *   Lightstrip — ROS /rgblight topic, fully functional after advertise() fix
 *
 * What needs Pi-side setup to work:
 *   OLED — luma.oled via SSH. Works once `pip3 install luma.oled pillow`
 *   is run on the Pi host and the ROS oled_node is not holding I2C.
 *   Use get_status to diagnose. See docs/hardware/HARDWARE_DIAGNOSIS_VOICE_I2C.md
 */

import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  Loader2,
  Mic,
  Palette,
  RefreshCw,
  ScreenShare,
  Trash2,
  Type,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

// ── Types ─────────────────────────────────────────────────────────────────────

interface OledStatus {
  active: boolean;
  detected_addresses: string[];
  driver_responding: boolean;
  driver: string;
  note: string;
}

// ── Lightstrip data ───────────────────────────────────────────────────────────

const PATTERNS = [
  { id: "patrol",  label: "Patrol Car",   color: "bg-gradient-to-r from-red-600 via-zinc-200 to-blue-600" },
  { id: "rainbow", label: "Rainbow Flow", color: "bg-gradient-to-r from-red-500 via-green-500 to-blue-500" },
  { id: "breathe", label: "Breathe",      color: "bg-gradient-to-r from-blue-600 to-cyan-400" },
  { id: "fire",    label: "Fire Flicker", color: "bg-gradient-to-r from-orange-600 to-red-500" },
  { id: "off",     label: "Kill",         color: "bg-zinc-900" },
];

const COLORS: { label: string; r: number; g: number; b: number; cls: string }[] = [
  { label: "Red",    r: 255, g: 0,   b: 0,   cls: "bg-red-600"     },
  { label: "Green",  r: 0,   g: 255, b: 0,   cls: "bg-green-500"   },
  { label: "Blue",   r: 0,   g: 0,   b: 255, cls: "bg-blue-600"    },
  { label: "White",  r: 255, g: 255, b: 255, cls: "bg-white"       },
  { label: "Amber",  r: 255, g: 160, b: 0,   cls: "bg-amber-500"   },
  { label: "Purple", r: 160, g: 0,   b: 255, cls: "bg-purple-600"  },
];

// ── OLED quick messages ───────────────────────────────────────────────────────

const OLED_PRESETS = [
  { label: "Boomy Active",   text: "Boomy Active" },
  { label: "Kaffeehaus",     text: "Kaffeehaus Mode" },
  { label: "Patrol",         text: "Patrol Active" },
  { label: "Low Battery",    text: "Low Battery!" },
  { label: "System Status",  text: null },  // triggers the status dashboard op
];

// ── API helpers ───────────────────────────────────────────────────────────────

async function post(path: string, body: object) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function Peripherals() {
  const navigate = useNavigate();

  // Lightstrip
  const [ledLoading, setLedLoading] = useState<string | null>(null);
  const [ledError, setLedError] = useState<string | null>(null);
  const [rgbR, setRgbR] = useState(0);
  const [rgbG, setRgbG] = useState(100);
  const [rgbB, setRgbB] = useState(255);
  const rgbDebounce = useRef<ReturnType<typeof setTimeout> | null>(null);

  // OLED
  const [oledStatus, setOledStatus] = useState<OledStatus | null>(null);
  const [oledProbing, setOledProbing] = useState(false);
  const [oledText, setOledText] = useState("");
  const [oledLine, setOledLine] = useState(0);
  const [oledBusy, setOledBusy] = useState<string | null>(null);
  const [oledFeedback, setOledFeedback] = useState<{ ok: boolean; msg: string } | null>(null);

  const probeOled = useCallback(async () => {
    setOledProbing(true);
    try {
      const data = await post("/api/v1/control/display/status", {});
      setOledStatus(data.result as OledStatus);
    } catch {
      setOledStatus(null);
    } finally {
      setOledProbing(false);
    }
  }, []);

  useEffect(() => { probeOled(); }, [probeOled]);

  // ── Lightstrip handlers ───────────────────────────────────────────────────

  const handlePattern = async (id: string) => {
    setLedLoading(id);
    setLedError(null);
    try {
      await post("/api/v1/control/lightstrip", {
        operation: id === "off" ? "off" : "pattern",
        pattern: id,
      });
    } catch (e: any) {
      setLedError(e.message ?? "Lightstrip error");
    } finally {
      setTimeout(() => setLedLoading(null), 600);
    }
  };

  const handleColor = async (r: number, g: number, b: number) => {
    setLedLoading(`color-${r}-${g}-${b}`);
    setLedError(null);
    try {
      await post("/api/v1/control/lightstrip", { operation: "set", r, g, b });
    } catch (e: any) {
      setLedError(e.message ?? "Lightstrip error");
    } finally {
      setTimeout(() => setLedLoading(null), 400);
    }
  };

  const handleRgbSlider = (r: number, g: number, b: number) => {
    setRgbR(r); setRgbG(g); setRgbB(b);
    if (rgbDebounce.current) clearTimeout(rgbDebounce.current);
    rgbDebounce.current = setTimeout(() => handleColor(r, g, b), 120);
  };

  // ── OLED handlers ─────────────────────────────────────────────────────────

  const flashFeedback = (ok: boolean, msg: string) => {
    setOledFeedback({ ok, msg });
    setTimeout(() => setOledFeedback(null), 3000);
  };

  const handleOledWrite = async (text: string, line: number = oledLine) => {
    if (!text.trim()) return;
    setOledBusy("write");
    try {
      const res = await post("/api/v1/display/write", { text, line });
      flashFeedback(res.success, res.success ? `Line ${line}: "${text}"` : res.result?.log || "Failed");
    } catch (e: any) {
      flashFeedback(false, e.message);
    } finally {
      setOledBusy(null);
    }
  };

  const handleOledStatus = async () => {
    setOledBusy("status");
    try {
      const res = await post("/api/v1/control/tool", { operation: "display", param1: "status" });
      flashFeedback(res.success, res.success ? "System status shown on OLED" : res.result?.log || "Failed — check luma.oled on Pi");
    } catch (e: any) {
      flashFeedback(false, e.message);
    } finally {
      setOledBusy(null);
    }
  };

  const handleOledClear = async () => {
    setOledBusy("clear");
    try {
      const res = await post("/api/v1/display/clear", {});
      flashFeedback(res.success, res.success ? "Display cleared" : res.result?.log || "Failed");
    } catch (e: any) {
      flashFeedback(false, e.message);
    } finally {
      setOledBusy(null);
    }
  };

  const handleOledScroll = async (text: string) => {
    setOledBusy("scroll");
    try {
      const res = await post("/api/v1/display/scroll", { text });
      flashFeedback(res.success, res.success ? `Scrolling: "${text}"` : "Failed");
    } catch (e: any) {
      flashFeedback(false, e.message);
    } finally {
      setOledBusy(null);
    }
  };

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-10 font-sans">
      <div className="max-w-[1400px] mx-auto space-y-10">

        {/* ── Header ───────────────────────────────────────────────────────── */}
        <div>
          <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
            <Palette className="w-8 h-8 text-blue-500" />
            Peripherals
          </h1>
          <p className="text-zinc-500 text-xs mt-1 font-mono">Lightstrip FX · OLED Display</p>
        </div>

        {/* ── Voice redirect card ───────────────────────────────────────────── */}
        <button
          onClick={() => navigate("/voice")}
          className="w-full flex items-center justify-between gap-4 p-5 rounded-2xl bg-purple-500/5 border border-purple-500/15 hover:bg-purple-500/10 hover:border-purple-500/25 transition-all group text-left"
        >
          <div className="flex items-center gap-4">
            <div className="w-9 h-9 rounded-xl bg-purple-500/15 flex items-center justify-center flex-shrink-0">
              <Mic className="w-4 h-4 text-purple-400" />
            </div>
            <div>
              <p className="text-[11px] font-black uppercase tracking-widest text-purple-300">Voice & Audio →</p>
              <p className="text-[10px] text-zinc-600 font-mono">CSK4002 preset phrases · espeak-ng TTS · recognition listen · volume</p>
            </div>
          </div>
          <ArrowRight className="w-4 h-4 text-purple-500/50 group-hover:text-purple-400 group-hover:translate-x-1 transition-all flex-shrink-0" />
        </button>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">

          {/* ══════════════════════════════════════════════════════════════════
              LIGHTSTRIP
          ══════════════════════════════════════════════════════════════════ */}
          <section className="relative overflow-hidden rounded-[2.5rem] border border-white/5 bg-zinc-900/40 p-8 backdrop-blur-xl">
            <div className="absolute top-0 right-0 w-48 h-48 bg-blue-500/5 blur-[80px] rounded-full -mr-16 -mt-16 pointer-events-none" />
            <div className="relative z-10 space-y-8">

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Palette className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-sm font-black uppercase tracking-widest">Lightstrip</p>
                    <p className="text-[9px] text-zinc-600 font-mono">ROS /rgblight · std_msgs/Int32MultiArray</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                  <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  <span className="text-[9px] font-black text-emerald-500 uppercase tracking-wider">Live</span>
                </div>
              </div>

              {ledError && (
                <p className="text-xs text-red-400 font-mono bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 -mt-2">
                  {ledError}
                </p>
              )}

              {/* Patterns */}
              <div className="space-y-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Patterns</p>
                <div className="grid grid-cols-5 gap-2">
                  {PATTERNS.map(p => (
                    <button
                      key={p.id}
                      onClick={() => handlePattern(p.id)}
                      disabled={ledLoading !== null}
                      className={`group relative h-20 rounded-2xl overflow-hidden border border-white/5 hover:border-white/15 transition-all active:scale-95 disabled:opacity-40 ${p.color}`}
                    >
                      <div className="absolute inset-0 bg-black/50 group-hover:bg-black/20 transition-all" />
                      <div className="relative h-full flex flex-col justify-end p-2">
                        <span className="text-[9px] font-black uppercase tracking-wider text-white leading-tight">{p.label}</span>
                      </div>
                      {ledLoading === p.id && (
                        <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                          <Loader2 className="w-4 h-4 animate-spin text-white" />
                        </div>
                      )}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick colours */}
              <div className="space-y-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Quick Colours</p>
                <div className="flex flex-wrap gap-2">
                  {COLORS.map(c => (
                    <button
                      key={c.label}
                      onClick={() => handleColor(c.r, c.g, c.b)}
                      disabled={ledLoading !== null}
                      className="flex items-center gap-2 px-3 py-2 rounded-xl bg-zinc-900 border border-white/5 hover:border-white/15 transition-all active:scale-95 disabled:opacity-40"
                    >
                      <div className={`w-3 h-3 rounded-full ${c.cls} border border-white/20`} />
                      <span className="text-[10px] font-bold text-zinc-400">{c.label}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* RGB sliders */}
              <div className="space-y-3 p-5 rounded-2xl bg-black/20 border border-white/5">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Custom RGB</p>
                <div className="flex items-center gap-4 mb-3">
                  <div
                    className="w-10 h-10 rounded-xl border border-white/10 flex-shrink-0 transition-all"
                    style={{ backgroundColor: `rgb(${rgbR},${rgbG},${rgbB})` }}
                  />
                  <span className="text-[10px] font-mono text-zinc-500">
                    rgb({rgbR}, {rgbG}, {rgbB})
                  </span>
                </div>
                {(["R", "G", "B"] as const).map((ch, i) => {
                  const val = [rgbR, rgbG, rgbB][i];
                  const setter = [
                    (v: number) => handleRgbSlider(v, rgbG, rgbB),
                    (v: number) => handleRgbSlider(rgbR, v, rgbB),
                    (v: number) => handleRgbSlider(rgbR, rgbG, v),
                  ][i];
                  const accentClass = ["accent-red-500", "accent-green-500", "accent-blue-500"][i];
                  return (
                    <div key={ch} className="flex items-center gap-3">
                      <span className="text-[10px] font-black text-zinc-600 w-3">{ch}</span>
                      <input
                        type="range" min={0} max={255} value={val}
                        onChange={e => setter(parseInt(e.target.value))}
                        className={`flex-1 h-1 appearance-none rounded-full bg-zinc-800 cursor-pointer ${accentClass}`}
                      />
                      <span className="text-[10px] font-mono text-zinc-500 w-7 text-right">{val}</span>
                    </div>
                  );
                })}
              </div>

            </div>
          </section>

          {/* ══════════════════════════════════════════════════════════════════
              OLED DISPLAY
          ══════════════════════════════════════════════════════════════════ */}
          <section className="relative overflow-hidden rounded-[2.5rem] border border-white/5 bg-zinc-900/40 p-8 backdrop-blur-xl">
            <div className="absolute top-0 right-0 w-48 h-48 bg-green-500/5 blur-[80px] rounded-full -mr-16 -mt-16 pointer-events-none" />
            <div className="relative z-10 space-y-7">

              {/* Header + status */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <ScreenShare className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-sm font-black uppercase tracking-widest">OLED Display</p>
                    <p className="text-[9px] text-zinc-600 font-mono">I2C via SSH · luma.oled · ssd1306</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {oledProbing ? (
                    <Loader2 className="w-4 h-4 animate-spin text-zinc-600" />
                  ) : oledStatus?.driver_responding ? (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20">
                      <CheckCircle2 className="w-3 h-3 text-emerald-500" />
                      <span className="text-[9px] font-black text-emerald-500 uppercase tracking-wider">
                        {oledStatus.detected_addresses[0] ? `0x${oledStatus.detected_addresses[0]}` : "OK"}
                      </span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20">
                      <AlertTriangle className="w-3 h-3 text-amber-500" />
                      <span className="text-[9px] font-black text-amber-500 uppercase tracking-wider">
                        {oledStatus ? "No luma" : "Not probed"}
                      </span>
                    </div>
                  )}
                  <button
                    onClick={probeOled}
                    className="p-1.5 rounded-lg bg-white/5 text-zinc-600 hover:text-zinc-300 hover:bg-white/10 transition-all"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Setup hint when luma not installed */}
              {oledStatus && !oledStatus.driver_responding && (
                <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/15 space-y-1">
                  <p className="text-[10px] font-black uppercase tracking-widest text-amber-500/70">Setup Required</p>
                  <p className="text-[10px] text-zinc-500 font-mono leading-relaxed">{oledStatus.note}</p>
                  <p className="text-[10px] text-amber-500/60 font-mono mt-1">
                    On Pi: pip3 install luma.oled luma.core pillow
                  </p>
                </div>
              )}

              {/* Text write */}
              <div className="space-y-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Write Line</p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Text to display…"
                    value={oledText}
                    onChange={e => setOledText(e.target.value)}
                    onKeyDown={e => e.key === "Enter" && handleOledWrite(oledText)}
                    className="flex-1 bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-sm text-white placeholder-zinc-700 focus:outline-none focus:border-green-500/30 focus:ring-2 focus:ring-green-500/10 transition-all font-mono"
                  />
                  <select
                    value={oledLine}
                    onChange={e => setOledLine(parseInt(e.target.value))}
                    className="bg-zinc-900 border border-white/5 rounded-xl px-3 py-3 text-[11px] font-black text-zinc-400 focus:outline-none cursor-pointer"
                  >
                    {[0, 1, 2, 3].map(n => (
                      <option key={n} value={n}>L{n}</option>
                    ))}
                  </select>
                  <button
                    onClick={() => handleOledWrite(oledText)}
                    disabled={!oledText.trim() || oledBusy !== null}
                    className="px-4 py-3 rounded-xl bg-green-500/15 border border-green-500/20 text-green-400 hover:bg-green-500/25 transition-all disabled:opacity-30 flex-shrink-0"
                  >
                    {oledBusy === "write" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Type className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Quick presets */}
              <div className="space-y-3">
                <p className="text-[10px] font-black uppercase tracking-widest text-zinc-600">Presets</p>
                <div className="flex flex-wrap gap-2">
                  {OLED_PRESETS.map(p => (
                    <button
                      key={p.label}
                      onClick={() => p.text ? handleOledWrite(p.text, 0) : handleOledStatus()}
                      disabled={oledBusy !== null}
                      className="px-3 py-2 rounded-xl bg-zinc-900 border border-white/5 text-[10px] font-bold text-zinc-500 hover:text-zinc-200 hover:border-white/10 transition-all disabled:opacity-30"
                    >
                      {p.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Scroll + clear */}
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={() => handleOledScroll(oledText || "Boomy Patrol Active")}
                  disabled={oledBusy !== null}
                  className="py-3 rounded-2xl bg-zinc-800/40 border border-white/5 text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800/70 transition-all disabled:opacity-30 flex items-center justify-center gap-2"
                >
                  {oledBusy === "scroll" ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Scroll Marquee
                </button>
                <button
                  onClick={handleOledClear}
                  disabled={oledBusy !== null}
                  className="py-3 rounded-2xl bg-red-500/5 border border-white/5 text-[10px] font-black uppercase tracking-widest text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-all disabled:opacity-30 flex items-center justify-center gap-2"
                >
                  {oledBusy === "clear" ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                  Clear
                </button>
              </div>

              {/* Feedback toast */}
              <AnimatePresence>
                {oledFeedback && (
                  <motion.div
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className={`p-3 rounded-xl border text-[10px] font-mono ${
                      oledFeedback.ok
                        ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                        : "bg-red-500/10 border-red-500/20 text-red-400"
                    }`}
                  >
                    {oledFeedback.msg}
                  </motion.div>
                )}
              </AnimatePresence>

            </div>
          </section>

        </div>
      </div>
    </div>
  );
}
