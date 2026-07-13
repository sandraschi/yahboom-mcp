/**
 * Audio.tsx — Boomy Soundboard & Audio Hub
 *
 * Built-in sound effects (17 procedurally generated), file upload/play,
 * stored audio depot management, and cross-connect links to fleet audio repos.
 *
 * Calls go through POST /api/v1/control/tool (portmanteau) for file ops.
 * Sound effects use the audio tool directly.
 */

import { AnimatePresence, motion } from "framer-motion";
import {
  AlertTriangle,
  CheckCircle2,
  Disc3,
  FileAudio,
  FolderOpen,
  Globe,
  Headphones,
  Loader2,
  Music,
  Play,
  Plus,
  RefreshCw,
  Send,
  Square,
  Trash2,
  Upload,
  Volume2,
  Zap,
} from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

// ── Types ────────────────────────────────────────────────────────────────────

interface AudioResult {
  success: boolean;
  operation: string;
  status?: string;
  error?: string;
  sound?: string;
  file_name?: string;
  files?: string[];
  count?: number;
  available?: string[];
}

interface FleetAudioRepo {
  name: string;
  port: number;
  description: string;
  icon: string;
}

// ── Sound Effects ────────────────────────────────────────────────────────────

const SOUND_CATEGORIES: {
  label: string;
  sounds: { id: string; label: string; emoji: string }[];
}[] = [
  {
    label: "Feedback",
    sounds: [
      { id: "ding", label: "Ding", emoji: "🔔" },
      { id: "buzzer", label: "Buzzer", emoji: "❌" },
      { id: "tada", label: "Ta-Da!", emoji: "🎉" },
      { id: "sad_trombone", label: "Womp Womp", emoji: "😢" },
      { id: "beep", label: "Beep", emoji: "📟" },
    ],
  },
  {
    label: "Comedy",
    sounds: [
      { id: "fart", label: "Fart", emoji: "💨" },
      { id: "clap", label: "Clap", emoji: "👏" },
      { id: "boo", label: "Boo", emoji: "👎" },
      { id: "applause", label: "Applause", emoji: "🙌" },
    ],
  },
  {
    label: "Military",
    sounds: [
      { id: "reveille", label: "Reveille", emoji: "🌅" },
      { id: "deguello", label: "Degüello", emoji: "⚔️" },
      { id: "siren", label: "Siren", emoji: "🚨" },
    ],
  },
  {
    label: "Signature",
    sounds: [
      { id: "take_five", label: "Take Five", emoji: "🎵" },
      { id: "circus", label: "Circus", emoji: "🎪" },
      { id: "elevator", label: "Lift Music", emoji: "🛗" },
      { id: "coin", label: "Coin", emoji: "🪙" },
      { id: "zap", label: "Zap", emoji: "⚡" },
    ],
  },
];

// ── Fleet Audio Repos ────────────────────────────────────────────────────────

const FLEET_AUDIO: FleetAudioRepo[] = [
  { name: "reaper-mcp", port: 10797, description: "DAW — record, mix, master", icon: "🎛️" },
  { name: "virtualdj-mcp", port: 10877, description: "DJ deck control", icon: "🎧" },
  { name: "plex-mcp", port: 10740, description: "Media server", icon: "📀" },
  { name: "speech-mcp", port: 10909, description: "TTS / STT", icon: "🗣️" },
  { name: "suno-mcp", port: 10883, description: "AI music generation", icon: "🎹" },
  { name: "songgeneration-mcp", port: 10885, description: "Song composition", icon: "🎼" },
  { name: "magentart-mcp", port: 10899, description: "Music AI models", icon: "🤖" },
  { name: "audiotool-nexus", port: 10901, description: "Audiotool bridge", icon: "🔊" },
  { name: "directmedia-mcp", port: 10827, description: "Direct media control", icon: "🎬" },
];

// ── API helper ───────────────────────────────────────────────────────────────

async function audioTool(operation: string, file_path?: string, file_name?: string) {
  const body: Record<string, string> = { operation };
  if (file_path) body.file_path = file_path;
  if (file_name) body.file_name = file_name;
  const res = await fetch("/api/v1/control/tool", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<AudioResult>;
}

// ── Component ────────────────────────────────────────────────────────────────

export default function Audio() {
  const [playing, setPlaying] = useState<string | null>(null);
  const [loading, setLoading] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [storedFiles, setStoredFiles] = useState<string[]>([]);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [storedName, setStoredName] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  // ── Sound effect ─────────────────────────────────────────────────────────

  const playSound = useCallback(async (soundId: string) => {
    setPlaying(soundId);
    setLoading(soundId);
    setError("");
    try {
      const res = await fetch("/api/v1/control/tool", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ operation: "audio_sound", param1: soundId }),
      });
      const data = await res.json();
      if (data.success) {
        setStatus(`Played: ${soundId}`);
      } else {
        setError(data.error || "Sound failed");
      }
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(null);
      setTimeout(() => setPlaying(null), 2000);
    }
  }, []);

  // ── List stored files ────────────────────────────────────────────────────

  const listStored = useCallback(async () => {
    try {
      const data = await audioTool("audio_list_stored");
      if (data.success && data.files) {
        setStoredFiles(data.files);
      }
    } catch {
      // silent
    }
  }, []);

  useEffect(() => {
    listStored();
  }, [listStored]);

  // ── Play stored file ─────────────────────────────────────────────────────

  const playStored = useCallback(async (name: string) => {
    setPlaying(name);
    setLoading(name);
    setError("");
    try {
      const data = await audioTool("audio_play_stored", "", name);
      if (!data.success) setError(data.error || "Play failed");
      else setStatus(`Playing: ${name}`);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(null);
      setTimeout(() => setPlaying(null), 3000);
    }
  }, []);

  // ── Delete stored ────────────────────────────────────────────────────────

  const deleteStored = useCallback(
    async (name: string) => {
      try {
        await audioTool("audio_delete_stored", "", name);
        listStored();
      } catch {
        // silent
      }
    },
    [listStored],
  );

  // ── Stop ─────────────────────────────────────────────────────────────────

  const stop = useCallback(async () => {
    setPlaying(null);
    try {
      await audioTool("audio_stop");
      setStatus("Stopped");
    } catch (e: any) {
      setError(e.message);
    }
  }, []);

  // ── Upload & play ────────────────────────────────────────────────────────

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setUploadFile(file);
  }, []);

  const uploadAndPlay = useCallback(
    async (store = false) => {
      if (!uploadFile) return;
      setLoading("upload");
      setError("");
      try {
        const formData = new FormData();
        formData.append("file", uploadFile);
        const uploadRes = await fetch("/api/v1/upload", {
          method: "POST",
          body: formData,
        });
        if (!uploadRes.ok) throw new Error("Upload failed");
        const { filename, path: savedPath } = await uploadRes.json();

        if (store) {
          const data = await audioTool("audio_store", savedPath, storedName || filename);
          if (data.success) {
            setStatus(`Stored: ${storedName || filename}`);
            setStoredName("");
            setShowUpload(false);
            setUploadFile(null);
            listStored();
          } else {
            setError(data.error || "Store failed");
          }
        } else {
          const data = await audioTool("audio_play", savedPath);
          if (data.success) {
            setStatus(`Playing: ${filename}`);
          } else {
            setError(data.error || "Play failed");
          }
        }
      } catch (e: any) {
        setError(e.message);
      } finally {
        setLoading(null);
      }
    },
    [uploadFile, storedName, listStored],
  );

  // ── Parse stored file line ────────────────────────────────────────────────

  const parseStoredLine = (line: string) => {
    const parts = line.trim().split(/\s+/);
    if (parts.length < 5) return { name: line, size: "" };
    return {
      name: parts.slice(4).join(" "),
      size: parts[4],
    };
  };

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-black text-white p-6 md:p-10 font-sans">
      <div className="max-w-[1400px] mx-auto space-y-10">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-black tracking-tight flex items-center gap-3">
              <Volume2 className="w-8 h-8 text-indigo-500" />
              Audio Soundboard
            </h1>
            <p className="text-zinc-500 text-xs mt-1 font-mono">
              Built-in effects + file playback through Boomy USB speaker
            </p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setShowUpload(!showUpload);
                setUploadFile(null);
              }}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-800/60 border border-zinc-700/50 hover:border-zinc-600 text-xs font-semibold text-zinc-300 transition-colors"
            >
              <Plus className="w-4 h-4" /> Upload
            </motion.button>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={listStored}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-zinc-800/60 border border-zinc-700/50 hover:border-zinc-600 text-xs font-semibold text-zinc-300 transition-colors"
            >
              <RefreshCw className="w-4 h-4" /> Refresh
            </motion.button>
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={stop}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-red-600/20 border border-red-500/30 hover:bg-red-600/40 text-xs font-bold text-red-400 transition-colors"
            >
              <Square className="w-4 h-4 fill-current" /> STOP
            </motion.button>
          </div>
        </div>

        {/* Status & Error */}
        <AnimatePresence>
          {status && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/5 border border-emerald-500/20 rounded-xl px-4 py-2.5"
            >
              <CheckCircle2 className="w-3.5 h-3.5" /> {status}
            </motion.div>
          )}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              className="flex items-center gap-2 text-xs text-red-400 bg-red-500/5 border border-red-500/20 rounded-xl px-4 py-2.5"
            >
              <AlertTriangle className="w-3.5 h-3.5" /> {error}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Upload Panel */}
        <AnimatePresence>
          {showUpload && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="rounded-[2rem] bg-zinc-900/40 border border-white/5 p-6 backdrop-blur-xl space-y-4">
                <h2 className="text-sm font-black uppercase tracking-widest text-zinc-500">
                  Upload Audio File
                </h2>
                <div className="flex flex-col md:flex-row gap-4">
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".mp3,.wav"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <button
                    type="button"
                    onClick={() => fileInputRef.current?.click()}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-xl bg-zinc-800/60 border border-dashed border-zinc-600/50 hover:border-indigo-500/50 text-xs text-zinc-400 hover:text-zinc-200 transition-colors cursor-pointer"
                  >
                    <Upload className="w-4 h-4" />
                    {uploadFile ? uploadFile.name : "Choose .mp3 or .wav file..."}
                  </button>
                  <input
                    type="text"
                    value={storedName}
                    onChange={(e) => setStoredName(e.target.value)}
                    placeholder="Name for depot (optional)"
                    className="flex-1 px-4 py-3 rounded-xl bg-zinc-800/60 border border-zinc-700/50 text-xs text-zinc-200 placeholder:text-zinc-600 focus:outline-none focus:border-indigo-500/50"
                  />
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => uploadAndPlay(false)}
                    disabled={!uploadFile || loading === "upload"}
                    className="flex items-center gap-2 px-5 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 text-xs font-bold text-white transition-colors"
                  >
                    {loading === "upload" ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Play className="w-4 h-4" />
                    )}
                    Play
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    onClick={() => uploadAndPlay(true)}
                    disabled={!uploadFile || loading === "upload"}
                    className="flex items-center gap-2 px-5 py-3 rounded-xl bg-zinc-700 hover:bg-zinc-600 disabled:opacity-40 text-xs font-semibold text-zinc-200 transition-colors"
                  >
                    <Plus className="w-4 h-4" /> Store
                  </motion.button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Sound Effects Grid */}
        <div className="space-y-6">
          <h2 className="text-sm font-black uppercase tracking-widest text-zinc-500 flex items-center gap-2">
            <Zap className="w-4 h-4 text-amber-500" /> Built-in Sound Effects
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
            {SOUND_CATEGORIES.map((cat) => (
              <div
                key={cat.label}
                className="rounded-[2rem] bg-zinc-900/40 border border-white/5 p-5 backdrop-blur-xl space-y-3"
              >
                <h3 className="text-[10px] font-black uppercase tracking-widest text-zinc-600">
                  {cat.label}
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {cat.sounds.map((s) => {
                    const isActive = playing === s.id;
                    const isLoading = loading === s.id;
                    return (
                      <motion.button
                        key={s.id}
                        whileTap={{ scale: 0.93 }}
                        onClick={() => playSound(s.id)}
                        disabled={loading !== null}
                        className={`
                          flex items-center gap-2 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all duration-200 border
                          ${
                            isActive
                              ? "bg-indigo-500/20 border-indigo-500/40 text-indigo-300"
                              : "bg-zinc-800/40 border-zinc-700/30 hover:border-zinc-500/50 text-zinc-400 hover:text-zinc-200"
                          }
                          disabled:opacity-50
                        `}
                      >
                        <span className="text-sm">{s.emoji}</span>
                        <span className="truncate">{s.label}</span>
                        {isLoading && (
                          <Loader2 className="w-3 h-3 animate-spin ml-auto flex-shrink-0" />
                        )}
                        {isActive && !isLoading && (
                          <Play className="w-3 h-3 ml-auto flex-shrink-0 fill-current" />
                        )}
                      </motion.button>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Stored Files */}
        {storedFiles.length > 0 && (
          <div className="rounded-[2rem] bg-zinc-900/40 border border-white/5 p-6 backdrop-blur-xl space-y-4">
            <h2 className="text-sm font-black uppercase tracking-widest text-zinc-500 flex items-center gap-2">
              <FolderOpen className="w-4 h-4 text-violet-500" /> Stored on Boomy (
              {storedFiles.length})
            </h2>
            <div className="space-y-2">
              {storedFiles.map((line, i) => {
                const f = parseStoredLine(line);
                const isPlaying = playing === f.name;
                const isLoading = loading === f.name;
                return (
                  <div
                    key={i}
                    className="flex items-center gap-4 px-4 py-3 rounded-xl bg-zinc-800/30 border border-zinc-700/20 group"
                  >
                    <FileAudio className="w-4 h-4 text-zinc-500 flex-shrink-0" />
                    <span className="flex-1 text-xs text-zinc-300 font-mono truncate">
                      {f.name}
                    </span>
                    <span className="text-[10px] text-zinc-600 font-mono flex-shrink-0 hidden md:inline">
                      {f.size}
                    </span>
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={() => playStored(f.name)}
                      disabled={loading !== null}
                      className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/20 hover:bg-emerald-500/20 text-emerald-400 disabled:opacity-40 transition-colors"
                    >
                      {isLoading ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Play className={`w-3.5 h-3.5 ${isPlaying ? "fill-current" : ""}`} />
                      )}
                    </motion.button>
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={() => deleteStored(f.name)}
                      className="p-2 rounded-lg bg-transparent hover:bg-red-500/10 text-zinc-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </motion.button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Fleet Audio Cross-Connect */}
        <div className="rounded-[2rem] bg-zinc-900/40 border border-white/5 p-6 backdrop-blur-xl space-y-4">
          <h2 className="text-sm font-black uppercase tracking-widest text-zinc-500 flex items-center gap-2">
            <Globe className="w-4 h-4 text-cyan-500" /> Fleet Audio Repos
          </h2>
          <p className="text-[10px] text-zinc-600 font-mono">
            Cross-connect to other MCP servers for DAW, DJ, media, TTS, and AI music.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {FLEET_AUDIO.map((repo) => (
              <a
                key={repo.name}
                href={`http://127.0.0.1:${repo.port}`}
                target="_blank"
                rel="noreferrer"
                className="flex flex-col items-center gap-2 p-4 rounded-xl bg-zinc-800/30 border border-zinc-700/20 hover:border-indigo-500/30 hover:bg-zinc-800/50 transition-all duration-200 group text-center"
              >
                <span className="text-2xl">{repo.icon}</span>
                <span className="text-[10px] font-bold text-zinc-400 group-hover:text-zinc-200 uppercase tracking-wide">
                  {repo.name}
                </span>
                <span className="text-[9px] text-zinc-600 font-mono">:{repo.port}</span>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
