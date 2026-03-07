import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Trash2, Wifi, WifiOff, Compass, Battery } from 'lucide-react';
import { api, type Telemetry } from '../../lib/api';

const POLL_MS = 800;
const METRES_PER_PX = 0.015;
const TRAIL_MIN_DISTANCE_M = 0.03;
const MAP_SIZE_PX = 480;
const CENTER_PX = MAP_SIZE_PX / 2;

function useTelemetry() {
    const [data, setData] = useState<Telemetry | null>(null);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        let alive = true;
        const poll = async () => {
            try {
                const j = await api.getTelemetry();
                if (!alive) return;
                setData(j);
                setConnected((j as { source?: string }).source === 'live');
            } catch {
                if (alive) setConnected(false);
            }
        };
        poll();
        const id = setInterval(poll, POLL_MS);
        return () => {
            alive = false;
            clearInterval(id);
        };
    }, []);

    return { data, connected };
}

function toPx(x: number, y: number): [number, number] {
    const px = CENTER_PX + x / METRES_PER_PX;
    const py = CENTER_PX - y / METRES_PER_PX;
    return [px, py];
}

const MapPage: React.FC = () => {
    const { data, connected } = useTelemetry();
    const [trail, setTrail] = useState<Array<{ x: number; y: number }>>([]);
    const lastTrailRef = useRef<{ x: number; y: number } | null>(null);

    const position = data?.position ?? null;
    const heading = data?.imu && typeof (data.imu as { heading?: number }).heading === 'number'
        ? (data.imu as { heading: number }).heading
        : 0;
    const battery = data?.battery ?? 0;

    useEffect(() => {
        if (!position || position.x == null || position.y == null) return;
        const x = position.x;
        const y = position.y;
        const last = lastTrailRef.current;
        const dist = last != null
            ? Math.hypot(x - last.x, y - last.y)
            : TRAIL_MIN_DISTANCE_M + 1;
        if (dist >= TRAIL_MIN_DISTANCE_M) {
            lastTrailRef.current = { x, y };
            setTrail((prev) => [...prev, { x, y }]);
        }
    }, [position?.x, position?.y]);

    const clearTrail = useCallback(() => {
        setTrail([]);
        lastTrailRef.current = null;
    }, []);

    const [robotPx, robotPy] = position ? toPx(position.x, position.y) : [CENTER_PX, CENTER_PX];
    const trailPath =
        trail.length < 2
            ? ''
            : trail
                .map((p, i) => {
                    const [px, py] = toPx(p.x, p.y);
                    return `${i === 0 ? 'M' : 'L'} ${px} ${py}`;
                })
                .join(' ');

    const headingRad = (heading * Math.PI) / 180;
    const arrowLen = 18;
    const arrowEndX = robotPx + arrowLen * Math.sin(headingRad);
    const arrowEndY = robotPy - arrowLen * Math.cos(headingRad);

    const standardPrompts = [
        { label: 'Patrol the apartment', prompt: 'Patrol the apartment: do a full circuit of the main rooms, avoid obstacles, and return to start. Use the agentic workflow or step-by-step motion.' },
        { label: 'Go to recharge', prompt: 'Go to recharge: drive to the charging station and stop. (Contactless recharger will be equipped later; for now position the robot at the dock.)' },
    ];

    const navigate = useNavigate();
    const sendToChat = useCallback((prompt: string) => {
        navigate(`/chat?prompt=${encodeURIComponent(prompt)}`);
    }, [navigate]);

    return (
        <div className="flex flex-col h-full py-4 px-4 sm:px-6 max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <MapPin className="text-indigo-400 w-8 h-8" />
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight">Map</h1>
                        <p className="text-slate-400 text-sm">
                            Robot position and movement trail (odometry)
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <div
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold uppercase ${
                            connected
                                ? 'border-green-500/40 bg-green-500/10 text-green-400'
                                : 'border-amber-500/40 bg-amber-500/10 text-amber-400'
                        }`}
                    >
                        {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
                        {connected ? 'Live' : 'Simulated'}
                    </div>
                    <button
                        type="button"
                        onClick={clearTrail}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl border border-white/10 bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10 text-sm"
                    >
                        <Trash2 size={14} />
                        Clear trail
                    </button>
                </div>
            </div>

            <div className="flex flex-col lg:flex-row gap-6 flex-1 min-h-0">
                <div className="flex-shrink-0 bg-[#0f0f12]/80 border border-white/10 rounded-2xl p-4 overflow-hidden">
                    <svg
                        width={MAP_SIZE_PX}
                        height={MAP_SIZE_PX}
                        viewBox={`0 0 ${MAP_SIZE_PX} ${MAP_SIZE_PX}`}
                        className="bg-[#0a0a0e] rounded-xl border border-white/5"
                    >
                        <defs>
                            <pattern id="grid" width={1 / METRES_PER_PX} height={1 / METRES_PER_PX} patternUnits="userSpaceOnUse">
                                <path d={`M ${1 / METRES_PER_PX} 0 L 0 0 0 ${1 / METRES_PER_PX}`} fill="none" stroke="#1e1e2e" strokeWidth="0.5" />
                            </pattern>
                        </defs>
                        <rect width={MAP_SIZE_PX} height={MAP_SIZE_PX} fill="url(#grid)" />
                        <circle cx={CENTER_PX} cy={CENTER_PX} r={4} fill="none" stroke="#333" strokeWidth="1" strokeDasharray="2 2" />
                        {trailPath && (
                            <path
                                d={trailPath}
                                fill="none"
                                stroke="#6366f1"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                opacity={0.9}
                            />
                        )}
                        <line
                            x1={robotPx}
                            y1={robotPy}
                            x2={arrowEndX}
                            y2={arrowEndY}
                            stroke="#22d3ee"
                            strokeWidth="2"
                            strokeLinecap="round"
                        />
                        <circle
                            cx={robotPx}
                            cy={robotPy}
                            r={10}
                            fill="#6366f1"
                            stroke="#93c5fd"
                            strokeWidth="2"
                        />
                    </svg>
                    <div className="mt-3 flex gap-4 text-xs text-slate-500">
                        <span>Scale: 1 m = {Math.round(1 / METRES_PER_PX)} px</span>
                        {position && (
                            <span className="text-slate-400">
                                Pos: ({position.x.toFixed(2)}, {position.y.toFixed(2)})
                            </span>
                        )}
                    </div>
                </div>

                <div className="flex flex-col gap-4 flex-1 min-w-0">
                    <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-4">
                        <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Status</h2>
                        <div className="flex flex-wrap gap-4">
                            <div className="flex items-center gap-2">
                                <Compass className="text-indigo-400 w-4 h-4" />
                                <span className="text-slate-400 text-sm">Heading</span>
                                <span className="text-white font-mono">{heading.toFixed(1)}°</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Battery className="text-emerald-400 w-4 h-4" />
                                <span className="text-slate-400 text-sm">Battery</span>
                                <span className="text-white font-mono">{battery.toFixed(0)}%</span>
                            </div>
                            <div className="text-slate-400 text-sm">
                                Trail points: <span className="text-white font-mono">{trail.length}</span>
                            </div>
                        </div>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-4">
                        <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-3">Standard actions</h2>
                        <p className="text-slate-400 text-sm mb-3">
                            Use the AI Companion with these prompts for common tasks.
                        </p>
                        <div className="flex flex-wrap gap-2">
                            {standardPrompts.map((item) => (
                                <button
                                    key={item.label}
                                    type="button"
                                    onClick={() => sendToChat(item.prompt)}
                                    className="px-4 py-2.5 rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 text-sm font-medium transition-colors"
                                >
                                    {item.label}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MapPage;
