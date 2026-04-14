import {
  ArrowRightLeft,
  Loader2,
  Palette,
  Radio,
  RefreshCw,
  ScreenShare,
  Trash2,
  Volume2,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";

const PATTERNS = [
  {
    id: "patrol",
    label: "Patrol Car",
    sid: "patrol",
    color: "bg-gradient-to-r from-red-600 via-zinc-200 to-blue-600",
  },
  {
    id: "rainbow",
    label: "Rainbow Flow",
    sid: "rainbow",
    color: "bg-gradient-to-r from-red-500 via-green-500 to-blue-500",
  },
  {
    id: "breathe",
    label: "Breathe RGB",
    sid: "breathe",
    color: "bg-gradient-to-r from-blue-600 to-cyan-400",
  },
  {
    id: "fire",
    label: "Fire Flicker",
    sid: "fire",
    color: "bg-gradient-to-r from-orange-600 to-red-500",
  },
  { id: "off", label: "Kill Lights", sid: "off", color: "bg-zinc-900" },
];

const PRESET_MESSAGES = [
  { id: "hello", label: "Hello World" },
  { id: "ready", label: "Boomy Active" },
  { id: "threat", label: "Threat Detected" },
  { id: "intel", label: "Logic Initialized" },
];

const SOUND_LIBRARY = [
  { id: "startup", sid: 1, label: "System Start" },
  { id: "alert", sid: 2, label: "Alert Chime" },
  { id: "ping", sid: 3, label: "Sonar Pulse" },
  { id: "success", sid: 4, label: "Success Jingle" },
  { id: "failure", sid: 5, label: "Fault Alarm" },
  { id: "mode", sid: 6, label: "Gear Shift" },
];

const StatusBadge = ({ detected, label }: { detected: boolean; label: string }) => (
  <div
    className={`px-4 py-1.5 rounded-full border text-[9px] font-black uppercase tracking-widest flex items-center gap-2 transition-all ${
      detected
        ? "bg-green-500/10 border-green-500/20 text-green-500 shadow-lg shadow-green-500/10"
        : "bg-zinc-900 border-white/5 text-zinc-600"
    }`}
  >
    <div
      className={`w-1 h-1 rounded-full ${detected ? "bg-green-500 animate-pulse" : "bg-zinc-800"}`}
    />
    {label}
  </div>
);

export default function Peripherals() {
  const [ledLoading, setLedLoading] = useState<string | null>(null);
  const [_oledLoading, setOledLoading] = useState<string | null>(null);
  const [soundLoading, setSoundLoading] = useState<string | number | null>(null);

  // OLED States
  const [voiceText, setVoiceText] = useState("");
  const [volume, setVolume] = useState(20);
  const [voiceDevice, setVoiceDevice] = useState<string | null>(null);
  const [voiceStatus, setVoiceStatus] = useState(false);
  const [displayNote, setDisplayNote] = useState<string | null>(null);

  useEffect(() => {
    refreshVoiceStatus();
  }, [refreshVoiceStatus]);

  const refreshVoiceStatus = async () => {
    try {
      const res = await fetch("/api/v1/control/voice/status");
      const data = await res.json();
      setVoiceStatus(data.success);
      if (data.success) setVoiceDevice("USB AUDIO OK");
    } catch (_e) {
      setVoiceStatus(false);
    }
  };

  const handlePattern = async (sid: string) => {
    setLedLoading(sid);
    try {
      await fetch("/api/v1/control/lightstrip", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation: sid === "off" ? "off" : "pattern",
          pattern: sid,
        }),
      });
    } finally {
      setTimeout(() => setLedLoading(null), 800);
    }
  };

  const handleOLED = async (action: string, text?: string) => {
    setOledLoading(action);
    try {
      if (action === "clear") {
        await fetch("/api/v1/control/lightstrip", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ operation: "off" }),
        });
        setDisplayNote(null);
      } else {
        await fetch("/api/v1/display/write", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: text || "Boomy System", line: 0 }),
        });
        if (action === "scroll") setDisplayNote(`OLED Transmission: ${text || "Active"}`);
      }
    } finally {
      setTimeout(() => setOledLoading(null), 600);
    }
  };

  const handleVoiceSay = async () => {
    if (!voiceText.trim()) return;
    setSoundLoading("tts");
    try {
      await fetch("/api/v1/control/voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operation: "say", text: voiceText }),
      });
    } finally {
      setSoundLoading(null);
    }
  };

  const handleSoundPlay = async (sid: number) => {
    setSoundLoading(sid);
    try {
      await fetch("/api/v1/control/voice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operation: "play", id: sid }),
      });
    } finally {
      setTimeout(() => setSoundLoading(null), 1000);
    }
  };

  const handleSetVolume = async (val: number) => {
    setVolume(val);
    await fetch("/api/v1/control/voice", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ operation: "volume", volume: val }),
    });
  };

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-10 lg:p-20 font-sans selection:bg-blue-500/30">
      <div className="max-w-[1400px] mx-auto space-y-20">
        {/* ── LIGHTS: ILLUMINATION ARTIFACTS ─────────────────────────── */}
        <section className="group relative overflow-hidden rounded-[3rem] border border-white/5 bg-zinc-900/40 p-10 backdrop-blur-2xl transition-all hover:bg-zinc-900/60 hover:border-white/10 shadow-2xl">
          <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[100px] rounded-full -mr-20 -mt-20 pointer-events-none group-hover:bg-blue-500/10 transition-all duration-1000" />
          <div className="relative z-10 space-y-10">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h2 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                  <Palette className="w-6 h-6 text-blue-500" />
                  Lightstrip FX
                </h2>
                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em] px-1">
                  Chrono-RGB Core
                </p>
              </div>
              <StatusBadge detected={true} label="LED OK" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {PATTERNS.map((pattern) => (
                <button
                  key={pattern.id}
                  onClick={() => handlePattern(pattern.sid as string)}
                  disabled={ledLoading !== null}
                  className={`group relative h-32 rounded-[2rem] overflow-hidden transition-all active:scale-95 ${pattern.color} border border-white/5 hover:border-white/20 hover:shadow-2xl hover:shadow-white/5 disabled:opacity-40`}
                >
                  <div className="absolute inset-0 bg-black/60 backdrop-blur-sm group-hover:bg-black/20 transition-all" />
                  <div className="relative h-full flex flex-col justify-end p-6">
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] mb-1 opacity-50">
                      {pattern.id}
                    </span>
                    <span className="text-xs font-black tracking-widest uppercase">
                      {pattern.label}
                    </span>
                    {ledLoading === pattern.sid && (
                      <div className="absolute top-4 right-4">
                        <Loader2 className="w-4 h-4 animate-spin text-white" />
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* ── DISPLAY: VISUAL TELEMETRY ─────────────────────────────── */}
        <section className="group relative overflow-hidden rounded-[3rem] border border-white/5 bg-zinc-900/40 p-10 backdrop-blur-2xl transition-all hover:bg-zinc-900/60 hover:border-white/10 shadow-2xl">
          <div className="absolute top-0 right-0 w-64 h-64 bg-green-500/5 blur-[100px] rounded-full -mr-20 -mt-20 pointer-events-none group-hover:bg-green-500/10 transition-all duration-1000" />
          <div className="relative z-10 space-y-10">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h2 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                  <ScreenShare className="w-6 h-6 text-green-500" />
                  OLED Controller
                </h2>
                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em] px-1">
                  I2C Pixel Matrix
                </p>
              </div>
              <StatusBadge detected={true} label="SSD1306 OK" />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-10">
              {/* Terminal Input */}
              <div className="space-y-6">
                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">
                  Flash Message
                </label>
                <div className="relative group/input">
                  <input
                    type="text"
                    placeholder="Transmit signal..."
                    className="w-full bg-black/40 border-2 border-white/5 rounded-2xl py-6 px-8 text-white placeholder-zinc-800 transition-all focus:border-green-500/30 focus:outline-none focus:ring-4 focus:ring-green-500/5 font-mono text-sm"
                  />
                  <div className="absolute right-4 top-1/2 -translate-y-1/2 flex gap-2">
                    <button
                      onClick={() => handleOLED("flash")}
                      className="px-6 py-2 rounded-xl bg-green-500 text-black font-black text-[10px] uppercase tracking-widest hover:bg-green-400 transition-all active:scale-95 shadow-lg shadow-green-500/20"
                    >
                      Flash
                    </button>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Presets */}
                <div className="space-y-4">
                  <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">
                    Quick Presets
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {PRESET_MESSAGES.map((msg) => (
                      <button
                        key={msg.id}
                        onClick={() => handleOLED("scroll", msg.label)}
                        className="px-4 py-2 rounded-xl bg-black/20 border border-white/5 text-[10px] font-bold text-zinc-500 hover:text-blue-400 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all uppercase tracking-wider"
                      >
                        {msg.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Controls */}
                <div className="space-y-4">
                  <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">
                    Mode Sequence
                  </label>
                  <div className="grid grid-cols-2 gap-3">
                    <button
                      onClick={() => handleOLED("scroll")}
                      className="py-3 rounded-2xl bg-zinc-800/30 border border-white/5 text-[10px] font-black uppercase tracking-widest text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-all flex items-center justify-center gap-2"
                    >
                      <ArrowRightLeft className="w-4 h-4" /> Scroll Env
                    </button>
                    <button
                      onClick={() => handleOLED("clear")}
                      className="py-3 rounded-2xl bg-red-500/5 border border-white/5 text-[10px] font-black uppercase tracking-widest text-zinc-500 hover:text-red-400 hover:bg-red-500/10 transition-all flex items-center justify-center gap-2"
                    >
                      <Trash2 className="w-4 h-4" /> Purge
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {displayNote && (
              <div className="p-4 rounded-2xl bg-blue-500/5 border border-blue-500/10">
                <p className="text-[10px] text-blue-400/60 font-medium leading-relaxed italic">
                  System Note: {displayNote}
                </p>
              </div>
            )}
          </div>
        </section>

        {/* ── AUDIO: SONIC COMMAND CENTER ───────────────────────────── */}
        <section className="group relative overflow-hidden rounded-[3rem] border border-white/5 bg-zinc-900/40 p-10 backdrop-blur-2xl transition-all hover:bg-zinc-900/60 hover:border-white/10 shadow-2xl">
          <div className="absolute top-0 right-0 w-64 h-64 bg-purple-500/5 blur-[100px] rounded-full -mr-20 -mt-20 pointer-events-none group-hover:bg-purple-500/10 transition-all duration-1000" />
          <div className="relative z-10 space-y-10">
            <div className="flex items-center justify-between">
              <div className="space-y-1">
                <h2 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                  <Volume2 className="w-6 h-6 text-purple-500" />
                  Sonic Command
                </h2>
                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em] px-1">
                  USB Voice Subsystem
                </p>
              </div>
              <div className="flex items-center gap-4">
                <StatusBadge detected={voiceStatus} label={voiceDevice || "VOICE OK"} />
                <button
                  onClick={refreshVoiceStatus}
                  className="p-2 rounded-full bg-white/5 text-zinc-500 hover:bg-white/10 hover:text-white transition-all"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
              {/* Left: Conversational TTS */}
              <div className="space-y-6">
                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">
                  Conversational TTS
                </label>
                <div className="space-y-4">
                  <textarea
                    rows={4}
                    placeholder="Enter transmission text…"
                    value={voiceText}
                    onChange={(e) => setVoiceText(e.target.value)}
                    className="w-full bg-black/40 border-2 border-white/5 rounded-[2rem] p-6 text-white placeholder-zinc-800 transition-all focus:border-purple-500/30 focus:outline-none focus:ring-4 focus:ring-purple-500/5 resize-none text-sm leading-relaxed"
                  />
                  <div className="flex items-center gap-4">
                    <button
                      onClick={handleVoiceSay}
                      disabled={!voiceText.trim()}
                      className="flex-1 py-4 rounded-2xl bg-purple-500 text-black font-black hover:bg-purple-400 active:scale-95 transition-all text-xs uppercase tracking-widest disabled:opacity-20 shadow-lg shadow-purple-500/20"
                    >
                      Transmit Speech
                    </button>
                    <div className="w-32 space-y-1">
                      <div className="flex justify-between text-[9px] text-zinc-500 font-black uppercase tracking-widest">
                        <span>Gain</span>
                        <span>{volume}</span>
                      </div>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        value={volume}
                        onChange={(e) => handleSetVolume(parseInt(e.target.value, 10))}
                        className="w-full h-1.5 appearance-none bg-zinc-800 rounded-full accent-purple-400 cursor-pointer"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Right: SFX Manifest */}
              <div className="space-y-6">
                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">
                  SFX Manifest
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {SOUND_LIBRARY.map((sound) => (
                    <button
                      key={sound.id}
                      onClick={() => handleSoundPlay(sound.sid as number)}
                      disabled={soundLoading !== null}
                      className="group/sfx relative overflow-hidden px-5 py-4 rounded-2xl bg-black/20 border border-white/5 text-[10px] font-black text-zinc-500 hover:text-white hover:border-purple-500/30 hover:bg-purple-500/5 transition-all uppercase tracking-widest flex items-center justify-between gap-3 disabled:opacity-40"
                    >
                      <span className="relative z-10">{sound.label}</span>
                      <div className="relative z-10">
                        {soundLoading === sound.sid ? (
                          <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                        ) : (
                          <Zap className="w-4 h-4 text-zinc-700 group-hover/sfx:text-purple-500/50 transition-colors" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
                <div className="p-5 rounded-2xl bg-purple-500/5 border border-purple-500/10 flex items-center gap-4">
                  <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                    <Radio className="w-5 h-5 text-purple-400 animate-pulse" />
                  </div>
                  <div className="flex-1">
                    <p className="text-[10px] text-white font-black tracking-widest uppercase">
                      Direct Stream Active
                    </p>
                    <p className="text-[9px] text-zinc-500 font-medium">
                      9600 Baud Serial Loopback
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
