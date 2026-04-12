import { useState, useEffect, useCallback } from 'react';
import {
    Lightbulb, Type, Volume2, Trash2, Zap,
    ArrowRightLeft, MessageSquare, CheckCircle2, XCircle,
    Wifi, WifiOff, Loader2, Radio, RefreshCw,
} from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { api, type HardwareOpResponse } from '../../lib/api';

function peripheralFailMessage(r: HardwareOpResponse): string {
    const res = r.result as { log?: string; error?: string; hint?: string } | undefined;
    return String(res?.log ?? res?.hint ?? res?.error ?? r.log ?? r.error ?? 'Command failed');
}

// ── Constants ────────────────────────────────────────────────────────────────

const LIGHTSTRIP_PATTERNS = [
    { id: 'patrol',   label: 'Patrol Car',  color: 'from-red-500 to-blue-500',   textColor: 'text-red-400',  desc: 'Red/blue flash' },
    { id: 'rainbow',  label: 'Rainbow',     color: 'from-purple-500 to-yellow-400', textColor: 'text-purple-400', desc: 'Hue cycle' },
    { id: 'breathe',  label: 'Breathe',     color: 'from-blue-500 to-cyan-400',  textColor: 'text-blue-400', desc: 'Sine fade' },
    { id: 'fire',     label: 'Fire',        color: 'from-orange-600 to-red-500', textColor: 'text-orange-400', desc: 'Random flicker' },
] as const;

type PatternId = typeof LIGHTSTRIP_PATTERNS[number]['id'];

const PRESET_MESSAGES = [
    { id: 'ready',    label: 'SYSTEM: READY' },
    { id: 'low_batt', label: 'BATTERY: LOW' },
    { id: 'scanning', label: 'SCANNING...' },
    { id: 'patrol',   label: 'PATROL ACTIVE' },
    { id: 'intruder', label: 'INTRUDER ALERT' },
];

const SOUND_LIBRARY = [
    { id: 'siren', label: 'Police Siren', sid: 1 },
    { id: 'horn',  label: 'Truck Horn',   sid: 2 },
    { id: 'bark',  label: 'Dog Bark',     sid: 3 },
    { id: 'beep',  label: 'System Beep',  sid: 4 },
    { id: 'alarm', label: 'Alarm',        sid: 5 },
    { id: 'chime', label: 'Chime',        sid: 6 },
];

// ── Sub-components ───────────────────────────────────────────────────────────

type StatusBadgeProps = {
    detected: boolean | null;   // null = loading
    label: string;
};
function StatusBadge({ detected, label }: StatusBadgeProps) {
    if (detected === null) return (
        <span className="flex items-center gap-1 text-[10px] text-zinc-500">
            <Loader2 className="w-3 h-3 animate-spin" /> Probing…
        </span>
    );
    return detected ? (
        <span className="flex items-center gap-1 text-[10px] text-emerald-400 font-bold">
            <Wifi className="w-3 h-3" /> {label}
        </span>
    ) : (
        <span className="flex items-center gap-1 text-[10px] text-zinc-600">
            <WifiOff className="w-3 h-3" /> Not detected
        </span>
    );
}

// ── Toast ────────────────────────────────────────────────────────────────────

type Toast = { message: string; type: 'success' | 'error' };

function useToast() {
    const [toast, setToast] = useState<Toast | null>(null);
    const show = useCallback((message: string, type: Toast['type'] = 'success') => {
        setToast({ message, type });
        setTimeout(() => setToast(null), 3000);
    }, []);
    return { toast, show };
}

// ── Main component ───────────────────────────────────────────────────────────

export default function Peripherals() {
    const { toast, show: showToast } = useToast();

    // Lightstrip
    const [ledColor, setLedColor]         = useState('#ff0000');
    const [brightness, setBrightness]     = useState(100);
    const [activePattern, setActivePattern] = useState<PatternId | null>(null);
    const [patternLoading, setPatternLoading] = useState(false);

    // OLED
    const [oledText, setOledText]         = useState('');
    const [isScrolling, setIsScrolling]   = useState(false);
    const [displayStatus, setDisplayStatus] = useState<boolean | null>(null);
    const [displayNote, setDisplayNote]   = useState('');

    // Voice
    const [voiceText, setVoiceText]       = useState('');
    const [voiceStatus, setVoiceStatus]   = useState<boolean | null>(null);
    const [voiceDevice, setVoiceDevice]   = useState('');
    const [soundLoading, setSoundLoading] = useState<number | null>(null);
    const [volume, setVolume]             = useState(20);

    // ── Probe peripheral status on mount ────────────────────────────────────

    useEffect(() => {
        api.getVoiceStatus()
            .then(r => {
                setVoiceStatus(r.result?.detected ?? false);
                setVoiceDevice(r.result?.device ?? '');
            })
            .catch(() => setVoiceStatus(false));

        api.getDisplayStatus()
            .then(r => {
                setDisplayStatus(r.result?.active ?? false);
                setDisplayNote(r.result?.note ?? '');
            })
            .catch(() => setDisplayStatus(false));
    }, []);

    // ── Lightstrip handlers ──────────────────────────────────────────────────

    const handleSetLED = async () => {
        const r = Math.round(parseInt(ledColor.slice(1, 3), 16) * brightness / 100);
        const g = Math.round(parseInt(ledColor.slice(3, 5), 16) * brightness / 100);
        const b = Math.round(parseInt(ledColor.slice(5, 7), 16) * brightness / 100);
        try {
            await api.setLed(r, g, b);
            setActivePattern(null);
            showToast(`Lightstrip → RGB(${r},${g},${b})`);
        } catch {
            showToast('Lightstrip set failed', 'error');
        }
    };

    const handlePattern = async (patternId: PatternId) => {
        setPatternLoading(true);
        try {
            if (activePattern === patternId) {
                await api.postLightstripOff();
                setActivePattern(null);
                showToast('Pattern stopped');
            } else {
                await api.postLightstripPattern(patternId);
                setActivePattern(patternId);
                showToast(`Pattern: ${patternId}`);
            }
        } catch {
            showToast('Pattern control failed', 'error');
        } finally {
            setPatternLoading(false);
        }
    };

    const handleLightsOff = async () => {
        try {
            await api.postLightstripOff();
            setActivePattern(null);
            showToast('Lightstrip off');
        } catch {
            showToast('Failed to turn off', 'error');
        }
    };

    // ── OLED handlers ────────────────────────────────────────────────────────

    const handleOLED = async (action: 'write' | 'scroll' | 'clear', text?: string) => {
        const content = text ?? oledText;
        try {
            if (action === 'clear') {
                const r = await api.postDisplayClear();
                if (r.success === false) {
                    showToast(peripheralFailMessage(r), 'error');
                    return;
                }
                setOledText('');
                setIsScrolling(false);
                showToast('Display cleared');
            } else if (action === 'scroll') {
                const r = await api.postDisplayControl('scroll', content);
                if (r.success === false) {
                    showToast(peripheralFailMessage(r), 'error');
                    return;
                }
                setIsScrolling(true);
                showToast('Scrolling…');
            } else {
                const r = await api.postDisplayWrite(content, 0);
                if (r.success === false) {
                    showToast(peripheralFailMessage(r), 'error');
                    return;
                }
                setIsScrolling(false);
                showToast('Written to display');
            }
        } catch {
            showToast(`Display ${action} failed`, 'error');
        }
    };

    const refreshDisplayStatus = async () => {
        setDisplayStatus(null);
        try {
            const r = await api.getDisplayStatus();
            setDisplayStatus(r.result?.active ?? false);
            setDisplayNote(r.result?.note ?? '');
            showToast(r.result?.note ?? 'Display probed');
        } catch {
            setDisplayStatus(false);
            showToast('Display probe failed', 'error');
        }
    };

    // ── Voice handlers ───────────────────────────────────────────────────────

    const handleVoiceSay = async () => {
        if (!voiceText.trim()) return;
        try {
            const r = await api.postVoiceControl(voiceText);
            if (r.success === false) {
                showToast(peripheralFailMessage(r), 'error');
                return;
            }
            showToast('Speaking…');
        } catch {
            showToast('Voice failed', 'error');
        }
    };

    const handleSoundPlay = async (sid: number) => {
        setSoundLoading(sid);
        try {
            const r = await api.postVoicePlay(sid);
            if (r.success === false) {
                showToast(peripheralFailMessage(r), 'error');
                return;
            }
            showToast(`Sound ${sid} triggered`);
        } catch {
            showToast(`Sound ${sid} failed`, 'error');
        } finally {
            setSoundLoading(null);
        }
    };

    const handleSetVolume = async (val: number) => {
        setVolume(val);
        try {
            await api.postVoice('volume', undefined, val);
        } catch { /* best-effort */ }
    };

    const refreshVoiceStatus = async () => {
        setVoiceStatus(null);
        try {
            const r = await api.getVoiceStatus();
            setVoiceStatus(r.result?.detected ?? false);
            setVoiceDevice(r.result?.device ?? '');
            showToast(r.result?.note ?? 'Voice probed');
        } catch {
            setVoiceStatus(false);
            showToast('Voice probe failed', 'error');
        }
    };

    // ── Render ───────────────────────────────────────────────────────────────

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">

            {/* Toast */}
            <AnimatePresence>
                {toast && (
                    <motion.div
                        initial={{ opacity: 0, y: -20, scale: 0.95 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95 }}
                        className="fixed top-8 right-8 z-[100] flex items-center gap-3 px-6 py-4 rounded-3xl bg-[#12121a]/95 border border-white/5 backdrop-blur-2xl shadow-2xl"
                    >
                        {toast.type === 'success'
                            ? <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            : <XCircle className="w-5 h-5 text-red-400" />
                        }
                        <span className="text-sm font-medium text-white">{toast.message}</span>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Header */}
            <div className="flex flex-col gap-1">
                <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
                    <Zap className="w-8 h-8 text-yellow-400" />
                    Hardware Peripherals
                </h1>
                <p className="text-zinc-400 text-sm">Lightstrip patterns, OLED display, audio module.</p>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 pb-20">

                {/* ── LIGHTSTRIP: CHASSIS AMBIANCE ───────────────────────────── */}
                <section className="group relative overflow-hidden rounded-[3rem] border border-white/5 bg-zinc-900/40 p-10 backdrop-blur-2xl transition-all hover:bg-zinc-900/60 hover:border-white/10 shadow-2xl">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-yellow-500/5 blur-[100px] rounded-full -mr-20 -mt-20 pointer-events-none group-hover:bg-yellow-500/10 transition-all duration-1000" />
                    <div className="relative z-10 space-y-10">
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <h2 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                                    <Lightbulb className="w-6 h-6 text-yellow-500" />
                                    Chassis Ambiance
                                </h2>
                                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em] px-1">Atmospheric Control Plane</p>
                            </div>
                            {activePattern && (
                                <motion.div 
                                    initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
                                    className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-yellow-500/10 border border-yellow-500/20 shadow-lg"
                                >
                                    <div className="w-1.5 h-1.5 rounded-full bg-yellow-400 animate-pulse" />
                                    <span className="text-[10px] text-yellow-400 font-black uppercase tracking-widest">{activePattern}</span>
                                </motion.div>
                            )}
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                            {/* Left: Quick Visual Patterns */}
                            <div className="space-y-4">
                                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">Quick Visual Patterns</label>
                                <div className="grid grid-cols-2 gap-3">
                                    {LIGHTSTRIP_PATTERNS.map(p => (
                                        <button
                                            key={p.id}
                                            onClick={() => handlePattern(p.id)}
                                            disabled={patternLoading}
                                            className={`relative overflow-hidden group/btn aspect-square rounded-3xl border transition-all duration-500 ${
                                                activePattern === p.id
                                                    ? 'border-white/20 bg-white/5 text-white shadow-xl translate-y-0.5'
                                                    : 'border-white/5 bg-black/20 text-zinc-500 hover:text-white hover:border-yellow-500/30'
                                            }`}
                                        >
                                            <div className="flex flex-col items-center justify-center p-4 gap-2 h-full">
                                                <Radio className={`w-5 h-5 ${activePattern === p.id ? 'text-yellow-400' : 'text-zinc-700 group-hover/btn:text-yellow-500/50'} transition-colors`} />
                                                <div className="text-center">
                                                    <span className={`block text-[11px] font-black uppercase tracking-wider ${activePattern === p.id ? 'text-white' : ''}`}>{p.label}</span>
                                                    <span className="block text-[9px] text-zinc-500 font-medium leading-tight mt-1">{p.desc}</span>
                                                </div>
                                            </div>
                                            {activePattern === p.id && (
                                                <div className={`absolute inset-0 bg-gradient-to-br ${p.color} opacity-10 animate-pulse`} />
                                            )}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Right: Manual Chroma Tuning */}
                            <div className="space-y-6">
                                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">Manual Chroma Tuning</label>
                                <div className="p-6 rounded-[2rem] bg-black/30 border border-white/5 space-y-6">
                                    <div className="flex items-center gap-6">
                                        <div className="relative group/picker">
                                            <input
                                                type="color"
                                                value={ledColor}
                                                onChange={e => setLedColor(e.target.value)}
                                                className="w-20 h-20 rounded-2xl border-none bg-transparent cursor-pointer relative z-10"
                                            />
                                            <div 
                                                className="absolute inset-0 rounded-2xl blur-xl opacity-50 group-hover/picker:opacity-100 transition-opacity"
                                                style={{ backgroundColor: ledColor }}
                                            />
                                        </div>
                                        <div className="flex-1 space-y-4">
                                            <div>
                                                <p className="font-mono text-xl text-white font-black tracking-tighter uppercase">{ledColor}</p>
                                                <p className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest mt-1">HEX CORE SPEC</p>
                                            </div>
                                            <div className="space-y-1">
                                                <div className="flex justify-between text-[10px] text-zinc-400 font-bold uppercase">
                                                    <span>Brightness</span>
                                                    <span>{brightness}%</span>
                                                </div>
                                                <input
                                                    type="range" min="0" max="100" value={brightness}
                                                    onChange={e => setBrightness(parseInt(e.target.value))}
                                                    className="w-full h-1.5 appearance-none bg-zinc-800 rounded-full accent-yellow-400 cursor-pointer"
                                                />
                                            </div>
                                        </div>
                                    </div>
                                    <button
                                        onClick={handleSetLED}
                                        className="w-full py-4 rounded-2xl bg-yellow-400 text-black font-black hover:bg-yellow-300 active:scale-95 transition-all text-xs uppercase tracking-widest shadow-lg shadow-yellow-500/20"
                                    >
                                        Deploy Payload
                                    </button>
                                </div>
                                <button
                                    onClick={handleLightsOff}
                                    className="w-full py-3 rounded-2xl bg-red-500/5 text-zinc-600 hover:text-red-400 hover:bg-red-500/10 transition-all text-[10px] font-black uppercase tracking-[0.2em] flex items-center justify-center gap-3"
                                >
                                    <Trash2 className="w-3 h-3" /> Silence Ambiance
                                </button>
                            </div>
                        </div>
                    </div>
                </section>

                {/* ── OLED: DISPLAY CONTROLLER ───────────────────────────────── */}
                <section className="group relative overflow-hidden rounded-[3rem] border border-white/5 bg-zinc-900/40 p-10 backdrop-blur-2xl transition-all hover:bg-zinc-900/60 hover:border-white/10 shadow-2xl">
                    <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 blur-[100px] rounded-full -mr-20 -mt-20 pointer-events-none group-hover:bg-blue-500/10 transition-all duration-1000" />
                    <div className="relative z-10 space-y-10">
                        <div className="flex items-center justify-between">
                            <div className="space-y-1">
                                <h2 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                                    <Type className="w-6 h-6 text-blue-500" />
                                    Visual Display
                                </h2>
                                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em] px-1">I2C SSD1306 Protocol</p>
                            </div>
                            <div className="flex items-center gap-4">
                                {isScrolling && (
                                    <span className="flex h-3 w-3 relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                                        <span className="relative inline-flex rounded-full h-3 w-3 bg-blue-500" />
                                    </span>
                                )}
                                <StatusBadge detected={displayStatus} label="OLED ACTIVE" />
                                <button onClick={refreshDisplayStatus} className="p-2 rounded-full bg-white/5 text-zinc-500 hover:bg-white/10 hover:text-white transition-all">
                                    <RefreshCw className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <div className="space-y-8">
                            {/* Input Core */}
                            <div className="space-y-4">
                                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">Direct Buffer Write</label>
                                <div className="relative group/input">
                                    <input
                                        type="text"
                                        placeholder="Transmit buffer data…"
                                        value={oledText}
                                        onChange={e => setOledText(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleOLED('write')}
                                        className="w-full bg-black/40 border-2 border-white/5 rounded-[2rem] p-6 pr-32 text-white font-mono text-lg placeholder-zinc-800 transition-all focus:border-blue-500/30 focus:outline-none focus:ring-4 focus:ring-blue-500/5"
                                    />
                                    <div className="absolute right-3 top-3 bottom-3 flex gap-2">
                                        <button
                                            onClick={() => handleOLED('write')}
                                            className="px-6 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 font-black text-[10px] uppercase tracking-widest hover:bg-blue-500/20 active:scale-95 transition-all"
                                        >
                                            Flash
                                        </button>
                                    </div>
                                </div>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                {/* Presets */}
                                <div className="space-y-4">
                                    <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">Quick Presets</label>
                                    <div className="flex flex-wrap gap-2">
                                        {PRESET_MESSAGES.map(msg => (
                                            <button
                                                key={msg.id}
                                                onClick={() => handleOLED('scroll', msg.label)}
                                                className="px-4 py-2 rounded-xl bg-black/20 border border-white/5 text-[10px] font-bold text-zinc-500 hover:text-blue-400 hover:border-blue-500/30 hover:bg-blue-500/5 transition-all uppercase tracking-wider"
                                            >
                                                {msg.label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Controls */}
                                <div className="space-y-4">
                                    <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">Mode Sequence</label>
                                    <div className="grid grid-cols-2 gap-3">
                                        <button
                                            onClick={() => handleOLED('scroll')}
                                            className="py-3 rounded-2xl bg-zinc-800/30 border border-white/5 text-[10px] font-black uppercase tracking-widest text-zinc-400 hover:text-white hover:bg-zinc-800/50 transition-all flex items-center justify-center gap-2"
                                        >
                                            <ArrowRightLeft className="w-4 h-4" /> Scroll Env
                                        </button>
                                        <button
                                            onClick={() => handleOLED('clear')}
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
                                <p className="text-[10px] text-blue-400/60 font-medium leading-relaxed italic">System Note: {displayNote}</p>
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
                                <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-[0.2em] px-1">USB Voice Subsystem</p>
                            </div>
                            <div className="flex items-center gap-4">
                                <StatusBadge detected={voiceStatus} label={voiceDevice || 'VOICE OK'} />
                                <button onClick={refreshVoiceStatus} className="p-2 rounded-full bg-white/5 text-zinc-500 hover:bg-white/10 hover:text-white transition-all">
                                    <RefreshCw className="w-4 h-4" />
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                            {/* Left: Conversational TTS */}
                            <div className="space-y-6">
                                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">Conversational TTS</label>
                                <div className="space-y-4">
                                    <textarea
                                        rows={4}
                                        placeholder="Enter transmission text…"
                                        value={voiceText}
                                        onChange={e => setVoiceText(e.target.value)}
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
                                                type="range" min="0" max="30" value={volume}
                                                onChange={e => handleSetVolume(parseInt(e.target.value))}
                                                className="w-full h-1.5 appearance-none bg-zinc-800 rounded-full accent-purple-400 cursor-pointer"
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Right: SFX Manifest */}
                            <div className="space-y-6">
                                <label className="text-[11px] font-black text-zinc-600 uppercase tracking-[0.25em]">SFX Manifest</label>
                                <div className="grid grid-cols-2 gap-3">
                                    {SOUND_LIBRARY.map(sound => (
                                        <button
                                            key={sound.id}
                                            onClick={() => handleSoundPlay(sound.sid)}
                                            disabled={soundLoading !== null}
                                            className="group/sfx relative overflow-hidden px-5 py-4 rounded-2xl bg-black/20 border border-white/5 text-[10px] font-black text-zinc-500 hover:text-white hover:border-purple-500/30 hover:bg-purple-500/5 transition-all uppercase tracking-widest flex items-center justify-between gap-3 disabled:opacity-40"
                                        >
                                            <span className="relative z-10">{sound.label}</span>
                                            <div className="relative z-10">
                                                {soundLoading === sound.sid
                                                    ? <Loader2 className="w-4 h-4 animate-spin text-purple-400" />
                                                    : <Zap className="w-4 h-4 text-zinc-700 group-hover/sfx:text-purple-500/50 transition-colors" />
                                                }
                                            </div>
                                        </button>
                                    ))}
                                </div>
                                <div className="p-5 rounded-2xl bg-purple-500/5 border border-purple-500/10 flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center">
                                        <Radio className="w-5 h-5 text-purple-400 animate-pulse" />
                                    </div>
                                    <div className="flex-1">
                                        <p className="text-[10px] text-white font-black tracking-widest uppercase">Direct Stream Active</p>
                                        <p className="text-[9px] text-zinc-500 font-medium">9600 Baud Serial Loopback</p>
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
