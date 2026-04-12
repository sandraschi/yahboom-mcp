import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Gamepad2, Square, Navigation, Music, AlertCircle, WifiOff } from 'lucide-react';
import { api } from '../../lib/api';

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));

interface Step {
    linear: number;
    angular: number;
    linearY?: number;
    durationMs: number;
    label?: string;
}

interface Preset {
    id: string;
    label: string;
    description: string;
    steps: Step[];
}

const LINEAR = 0.28;
const ANGULAR = 0.9;
const STRAFE = 0.2;

const PRESETS: Preset[] = [
    {
        id: 'forward',
        label: 'Forward',
        description: 'Drive forward 1.5 s',
        steps: [{ linear: LINEAR, angular: 0, durationMs: 1500, label: 'Forward' }],
    },
    {
        id: 'backward',
        label: 'Backward',
        description: 'Drive backward 1.5 s',
        steps: [{ linear: -LINEAR, angular: 0, durationMs: 1500, label: 'Backward' }],
    },
    {
        id: 'turn-left-90',
        label: 'Turn left 90°',
        description: 'Rotate left ~90°',
        steps: [{ linear: 0, angular: ANGULAR, durationMs: 520, label: 'Turn L' }],
    },
    {
        id: 'turn-right-90',
        label: 'Turn right 90°',
        description: 'Rotate right ~90°',
        steps: [{ linear: 0, angular: -ANGULAR, durationMs: 520, label: 'Turn R' }],
    },
    {
        id: 'spin-left',
        label: 'Spin left',
        description: 'Full rotation left',
        steps: [{ linear: 0, angular: ANGULAR, durationMs: 2100, label: 'Spin L' }],
    },
    {
        id: 'spin-right',
        label: 'Spin right',
        description: 'Full rotation right',
        steps: [{ linear: 0, angular: -ANGULAR, durationMs: 2100, label: 'Spin R' }],
    },
    {
        id: 'small-square',
        label: 'Small square',
        description: 'Forward + turn x4',
        steps: [
            { linear: LINEAR, angular: 0, durationMs: 1200, label: 'F' },
            { linear: 0, angular: ANGULAR, durationMs: 520, label: 'L' },
            { linear: LINEAR, angular: 0, durationMs: 1200, label: 'F' },
            { linear: 0, angular: ANGULAR, durationMs: 520, label: 'L' },
            { linear: LINEAR, angular: 0, durationMs: 1200, label: 'F' },
            { linear: 0, angular: ANGULAR, durationMs: 520, label: 'L' },
            { linear: LINEAR, angular: 0, durationMs: 1200, label: 'F' },
            { linear: 0, angular: ANGULAR, durationMs: 520, label: 'L' },
        ],
    },
];

const PATROLS: Preset[] = [
    {
        id: 'patrol-square',
        label: 'Square patrol',
        description: 'One full square (4 sides)',
        steps: (() => {
            const side = 4;
            const steps: Step[] = [];
            for (let i = 0; i < side; i++) {
                steps.push({ linear: LINEAR, angular: 0, durationMs: 2000, label: `F${i + 1}` });
                steps.push({ linear: 0, angular: ANGULAR, durationMs: 520, label: `T${i + 1}` });
            }
            return steps;
        })(),
    },
    {
        id: 'patrol-figure8',
        label: 'Figure-8',
        description: 'Approx figure-8 with arcs',
        steps: [
            { linear: LINEAR * 0.6, angular: ANGULAR * 0.5, durationMs: 2500, label: 'Arc R' },
            { linear: LINEAR * 0.6, angular: -ANGULAR * 0.5, durationMs: 2500, label: 'Arc L' },
            { linear: LINEAR * 0.6, angular: -ANGULAR * 0.5, durationMs: 2500, label: 'Arc L' },
            { linear: LINEAR * 0.6, angular: ANGULAR * 0.5, durationMs: 2500, label: 'Arc R' },
        ],
    },
    {
        id: 'patrol-back-forth',
        label: 'Back and forth',
        description: 'Forward, turn 180°, repeat',
        steps: [
            { linear: LINEAR, angular: 0, durationMs: 2500, label: 'F' },
            { linear: 0, angular: ANGULAR, durationMs: 1050, label: '180' },
            { linear: LINEAR, angular: 0, durationMs: 2500, label: 'F' },
            { linear: 0, angular: ANGULAR, durationMs: 1050, label: '180' },
        ],
    },
];

const DANCES: Preset[] = [
    {
        id: 'dance-wiggle',
        label: 'Wiggle',
        description: 'Quick left-right sway',
        steps: [
            { linear: 0, angular: ANGULAR * 0.7, durationMs: 300, label: 'L' },
            { linear: 0, angular: -ANGULAR * 0.7, durationMs: 300, label: 'R' },
            { linear: 0, angular: ANGULAR * 0.7, durationMs: 300, label: 'L' },
            { linear: 0, angular: -ANGULAR * 0.7, durationMs: 300, label: 'R' },
            { linear: 0, angular: ANGULAR * 0.7, durationMs: 300, label: 'L' },
            { linear: 0, angular: -ANGULAR * 0.7, durationMs: 300, label: 'R' },
        ],
    },
    {
        id: 'dance-box',
        label: 'Box step',
        description: 'Forward, strafe, back, strafe',
        steps: [
            { linear: LINEAR * 0.6, angular: 0, durationMs: 800, label: 'F' },
            { linear: 0, angular: 0, linearY: STRAFE, durationMs: 800, label: 'R' },
            { linear: -LINEAR * 0.6, angular: 0, durationMs: 800, label: 'B' },
            { linear: 0, angular: 0, linearY: -STRAFE, durationMs: 800, label: 'L' },
        ],
    },
    {
        id: 'dance-spin',
        label: 'Spin dance',
        description: 'Two full rotations',
        steps: [
            { linear: 0, angular: ANGULAR, durationMs: 2100, label: '360' },
            { linear: 0, angular: 0, durationMs: 200, label: '-' },
            { linear: 0, angular: -ANGULAR, durationMs: 2100, label: '360' },
        ],
    },
    {
        id: 'dance-shuffle',
        label: 'Shuffle',
        description: 'Small forward-back pulse',
        steps: [
            { linear: LINEAR * 0.4, angular: 0, durationMs: 400, label: 'F' },
            { linear: -LINEAR * 0.4, angular: 0, durationMs: 400, label: 'B' },
            { linear: LINEAR * 0.4, angular: 0, durationMs: 400, label: 'F' },
            { linear: -LINEAR * 0.4, angular: 0, durationMs: 400, label: 'B' },
        ],
    },
];

const MovementPage: React.FC = () => {
    const [connected, setConnected] = useState(false);
    const [running, setRunning] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [currentStep, setCurrentStep] = useState<string | null>(null);
    const abortedRef = useRef(false);

    useEffect(() => {
        let alive = true;
        const check = async () => {
            try {
                const h = await api.getHealth();
                if (alive) setConnected(h.robot_connection?.ros === 'connected');
            } catch {
                if (alive) setConnected(false);
            }
        };
        check();
        const id = setInterval(check, 2000);
        return () => {
            alive = false;
            clearInterval(id);
        };
    }, []);

    const runSteps = useCallback(async (preset: Preset) => {
        if (running) return;
        setError(null);
        abortedRef.current = false;
        setRunning(true);
        try {
            for (let i = 0; i < preset.steps.length; i++) {
                if (abortedRef.current) break;
                const step = preset.steps[i];
                setCurrentStep(step.label ?? `Step ${i + 1}`);
                await api.postMove(step.linear, step.angular, step.linearY);
                const deadline = Date.now() + step.durationMs;
                while (Date.now() < deadline && !abortedRef.current) {
                    await sleep(80);
                }
                if (abortedRef.current) break;
                await api.postMove(0, 0);
                await sleep(50);
            }
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Move failed');
        } finally {
            setCurrentStep(null);
            setRunning(false);
            try {
                await api.postMove(0, 0);
            } catch {
                // ignore
            }
        }
    }, [running]);

    const stop = useCallback(() => {
        abortedRef.current = true;
    }, []);

    const Section: React.FC<{ title: string; icon: React.ReactNode; items: Preset[] }> = ({ title, icon, items }) => (
        <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
            <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                {icon}
                {title}
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {items.map((preset) => (
                    <button
                        key={preset.id}
                        type="button"
                        disabled={!connected || running}
                        onClick={() => runSteps(preset)}
                        className="text-left p-4 rounded-xl border border-white/10 bg-white/5 hover:bg-indigo-500/10 hover:border-indigo-500/30 disabled:opacity-50 disabled:pointer-events-none transition-all"
                    >
                        <p className="font-medium text-white">{preset.label}</p>
                        <p className="text-xs text-slate-400 mt-0.5">{preset.description}</p>
                    </button>
                ))}
            </div>
        </div>
    );

    return (
        <div className="flex flex-col h-full py-4 px-4 sm:px-6 max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <Gamepad2 className="text-indigo-400 w-8 h-8" />
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight">Movement</h1>
                        <p className="text-slate-400 text-sm">
                            Preset movements, patrols, and dances. Robot must be connected.
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <div
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold uppercase ${
                            connected
                                ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
                                : 'border-amber-500/40 bg-amber-500/10 text-amber-400'
                        }`}
                    >
                        {connected ? <Gamepad2 size={12} /> : <WifiOff size={12} />}
                        {connected ? 'Connected' : 'Offline'}
                    </div>
                    {running && (
                        <button
                            type="button"
                            onClick={stop}
                            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-red-500/20 border border-red-500/40 text-red-400 hover:bg-red-500/30 font-bold text-sm"
                        >
                            <Square size={14} />
                            Stop
                        </button>
                    )}
                </div>
            </div>

            {error && (
                <div className="flex items-center gap-3 p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-200 mb-6">
                    <AlertCircle className="w-5 h-5 flex-shrink-0" />
                    <span className="text-sm">{error}</span>
                </div>
            )}

            {running && currentStep && (
                <p className="text-slate-400 text-sm mb-4 font-mono">Running: {currentStep}</p>
            )}

            <div className="space-y-6">
                <Section title="Preset movements" icon={<Square className="w-4 h-4 text-indigo-400" />} items={PRESETS} />
                <Section title="Patrolling" icon={<Navigation className="w-4 h-4 text-indigo-400" />} items={PATROLS} />
                <Section title="Dancing" icon={<Music className="w-4 h-4 text-indigo-400" />} items={DANCES} />
            </div>
        </div>
    );
};

export default MovementPage;
