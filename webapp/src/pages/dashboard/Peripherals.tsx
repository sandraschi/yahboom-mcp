import { useState, useEffect, useCallback } from 'react';
import {
    Lightbulb, Type, Volume2, Send, Trash2, Zap,
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

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">

                {/* ── LIGHTSTRIP ──────────────────────────────────────────── */}
                <section className="group relative overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/50 p-6 backdrop-blur-xl transition-all hover:border-white/20">
                    <div className="absolute inset-0 bg-gradient-to-br from-yellow-500/5 to-transparent pointer-events-none" />
                    <div className="relative z-10 space-y-5">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                <Lightbulb className="w-5 h-5 text-yellow-400" />
                                Chassis Lightstrip
                            </h2>
                            {activePattern && (
                                <span className="flex items-center gap-1 text-[10px] text-yellow-400 font-bold animate-pulse">
                                    <Radio className="w-3 h-3" /> {activePattern}
                                </span>
                            )}
                        </div>

                        {/* Autochange patterns */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-[2px]">Autochange Patterns</label>
                            <div className="grid grid-cols-2 gap-2">
                                {LIGHTSTRIP_PATTERNS.map(p => (
                                    <button
                                        key={p.id}
                                        onClick={() => handlePattern(p.id)}
                                        disabled={patternLoading}
                                        className={`relative overflow-hidden py-3 px-3 rounded-2xl border text-xs font-bold transition-all flex flex-col items-center gap-1 ${
                                            activePattern === p.id
                                                ? 'border-white/30 bg-white/10 text-white scale-[0.97]'
                                                : 'border-white/5 bg-zinc-950 text-zinc-400 hover:text-white hover:border-white/20'
                                        }`}
                                    >
                                        {activePattern === p.id && (
                                            <div className={`absolute inset-0 bg-gradient-to-br ${p.color} opacity-10`} />
                                        )}
                                        <span className={`relative z-10 ${p.textColor}`}>{p.label}</span>
                                        <span className="relative z-10 text-[9px] text-zinc-500">{p.desc}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Static colour */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-[2px]">Static Colour</label>
                            <div className="flex items-center gap-3">
                                <input
                                    type="color"
                                    value={ledColor}
                                    onChange={e => setLedColor(e.target.value)}
                                    className="w-12 h-12 rounded-xl border-none bg-transparent cursor-pointer"
                                    title="Pick colour"
                                />
                                <div className="flex-1">
                                    <p className="font-mono text-white text-sm uppercase">{ledColor}</p>
                                    <input
                                        type="range" min="0" max="100" value={brightness}
                                        onChange={e => setBrightness(parseInt(e.target.value))}
                                        className="w-full h-1 mt-1 appearance-none bg-zinc-800 rounded accent-yellow-400"
                                        title={`Brightness ${brightness}%`}
                                    />
                                    <p className="text-[10px] text-zinc-600 mt-0.5">Brightness {brightness}%</p>
                                </div>
                            </div>
                            <button
                                onClick={handleSetLED}
                                className="w-full py-3 rounded-2xl bg-yellow-400 text-black font-bold hover:bg-yellow-300 transition-colors text-sm"
                            >
                                Apply Colour
                            </button>
                        </div>

                        <button
                            onClick={handleLightsOff}
                            className="w-full py-2 rounded-xl text-zinc-500 hover:text-red-400 transition-colors text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2"
                        >
                            <Trash2 className="w-3 h-3" /> All Off
                        </button>
                    </div>
                </section>

                {/* ── OLED DISPLAY ────────────────────────────────────────── */}
                <section className="group relative overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/50 p-6 backdrop-blur-xl transition-all hover:border-white/20">
                    <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-transparent pointer-events-none" />
                    <div className="relative z-10 space-y-5">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                <Type className="w-5 h-5 text-blue-400" />
                                OLED Display
                            </h2>
                            <div className="flex items-center gap-2">
                                {isScrolling && (
                                    <span className="flex h-2 w-2 relative">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75" />
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500" />
                                    </span>
                                )}
                                <StatusBadge detected={displayStatus} label="I2C OK" />
                                <button onClick={refreshDisplayStatus} title="Re-probe display" className="text-zinc-600 hover:text-zinc-300 transition-colors">
                                    <RefreshCw className="w-3 h-3" />
                                </button>
                            </div>
                        </div>

                        {displayNote && (
                            <p className="text-[10px] text-zinc-500 leading-relaxed">{displayNote}</p>
                        )}

                        <div className="space-y-3">
                            <input
                                type="text"
                                placeholder="Message to display…"
                                value={oledText}
                                onChange={e => setOledText(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && handleOLED('write')}
                                className="w-full bg-zinc-950 border border-white/5 rounded-2xl p-3 text-white placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-blue-500/50 font-mono text-sm"
                            />
                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={() => handleOLED('write')}
                                    className="py-3 rounded-xl bg-zinc-800/50 text-white font-medium hover:bg-zinc-800 transition-colors flex items-center justify-center gap-2 border border-white/5 text-sm"
                                >
                                    <Send className="w-4 h-4 text-blue-400" /> Static
                                </button>
                                <button
                                    onClick={() => handleOLED('scroll')}
                                    className="py-3 rounded-xl bg-zinc-800/50 text-white font-medium hover:bg-zinc-800 transition-colors flex items-center justify-center gap-2 border border-white/5 text-sm"
                                >
                                    <ArrowRightLeft className="w-4 h-4 text-blue-400" /> Scroll
                                </button>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-[2px]">Quick Presets</label>
                            <div className="flex flex-wrap gap-2">
                                {PRESET_MESSAGES.map(msg => (
                                    <button
                                        key={msg.id}
                                        onClick={() => handleOLED('scroll', msg.label)}
                                        className="px-3 py-1.5 rounded-xl bg-zinc-950 border border-white/5 text-[10px] text-zinc-400 hover:text-white hover:border-blue-500/50 transition-all"
                                    >
                                        {msg.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <button
                            onClick={() => handleOLED('clear')}
                            className="w-full py-2 rounded-xl text-zinc-500 hover:text-red-400 transition-colors text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2"
                        >
                            <Trash2 className="w-3 h-3" /> Clear Display
                        </button>
                    </div>
                </section>

                {/* ── VOICE / AUDIO ────────────────────────────────────────── */}
                <section className="group relative overflow-hidden rounded-3xl border border-white/10 bg-zinc-900/50 p-6 backdrop-blur-xl transition-all hover:border-white/20">
                    <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-transparent pointer-events-none" />
                    <div className="relative z-10 space-y-5">
                        <div className="flex items-center justify-between">
                            <h2 className="text-xl font-semibold text-white flex items-center gap-2">
                                <Volume2 className="w-5 h-5 text-purple-400" />
                                Audio Module
                            </h2>
                            <div className="flex items-center gap-2">
                                <StatusBadge detected={voiceStatus} label={voiceDevice || 'USB OK'} />
                                <button onClick={refreshVoiceStatus} title="Re-probe voice" className="text-zinc-600 hover:text-zinc-300 transition-colors">
                                    <RefreshCw className="w-3 h-3" />
                                </button>
                            </div>
                        </div>

                        {/* Volume */}
                        <div className="space-y-1">
                            <div className="flex justify-between text-[10px] text-zinc-600 font-bold uppercase tracking-wider">
                                <label>Volume</label>
                                <span>{volume}/30</span>
                            </div>
                            <input
                                type="range" min="0" max="30" value={volume}
                                onChange={e => handleSetVolume(parseInt(e.target.value))}
                                className="w-full h-1 appearance-none bg-zinc-800 rounded accent-purple-400"
                            />
                        </div>

                        {/* TTS */}
                        <div className="space-y-2">
                            <textarea
                                rows={3}
                                placeholder="Type to speak…"
                                value={voiceText}
                                onChange={e => setVoiceText(e.target.value)}
                                className="w-full bg-zinc-950 border border-white/5 rounded-2xl p-3 text-white placeholder-zinc-700 focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none text-sm"
                            />
                            <button
                                onClick={handleVoiceSay}
                                disabled={!voiceText.trim()}
                                className="w-full py-3 rounded-2xl bg-purple-500/10 border border-purple-500/20 text-purple-400 font-bold hover:bg-purple-500/20 transition-all flex items-center justify-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed text-sm"
                            >
                                <Volume2 className="w-4 h-4" /> Speak
                            </button>
                        </div>

                        {/* Sound library */}
                        <div className="space-y-2">
                            <label className="text-[10px] font-bold text-zinc-600 uppercase tracking-[2px]">Sound Library</label>
                            <div className="grid grid-cols-2 gap-2">
                                {SOUND_LIBRARY.map(sound => (
                                    <button
                                        key={sound.id}
                                        onClick={() => handleSoundPlay(sound.sid)}
                                        disabled={soundLoading !== null}
                                        className="px-3 py-2.5 rounded-2xl bg-zinc-950 border border-white/5 text-[11px] text-zinc-400 hover:text-white hover:border-purple-500/50 transition-all flex items-center gap-2 disabled:opacity-40"
                                    >
                                        {soundLoading === sound.sid
                                            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                            : <MessageSquare className="w-3.5 h-3.5" />
                                        }
                                        {sound.label}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </section>
            </div>
        </div>
    );
}
