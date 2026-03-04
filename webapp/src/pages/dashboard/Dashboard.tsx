import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Activity, Battery, Compass, Play, Square, Settings, ChevronUp, ChevronDown, ChevronLeft, ChevronRight, Monitor, Zap, Shield, Rocket } from 'lucide-react'

// --- Types ---
interface Telemetry {
    battery: number;
    imu: { heading: number };
    velocity: { linear: number; angular: number };
}

interface Health {
    status: string;
    connected: boolean;
}

const Dashboard = () => {
    const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
    const [health, setHealth] = useState<Health | null>(null);
    const [isMoving, setIsMoving] = useState(false);

    // Poll Telemetry & Health
    useEffect(() => {
        const poll = async () => {
            try {
                const hRes = await fetch('http://localhost:10792/api/v1/health');
                const hData = await hRes.json();
                if (hData.status) setHealth(hData);

                const tRes = await fetch('http://localhost:10792/api/v1/telemetry');
                const tData = await tRes.json();
                if (tData.battery !== undefined) setTelemetry(tData);
            } catch (e) {
                console.warn('Backend unavailable');
            }
        };
        const interval = setInterval(poll, 1000);
        return () => clearInterval(interval);
    }, []);

    const move = async (linear: number, angular: number) => {
        setIsMoving(true);
        try {
            await fetch(`http://localhost:10792/api/v1/control/move?linear=${linear}&angular=${angular}`, { method: 'POST' });
        } catch (e) {
            console.error('Movement failed');
        }
        setTimeout(() => setIsMoving(false), 200);
    };

    return (
        <div className="space-y-8 py-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Monitor className="text-indigo-400 w-8 h-8" />
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight">Mission Control</h1>
                        <p className="text-slate-400 text-sm">Industrial hardware interface for Yahboom G1 Substrate.</p>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border ${health?.connected ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-red-500/10 border-red-500/20 text-red-500'}`}>
                        <span className={`w-2 h-2 rounded-full animate-pulse ${health?.connected ? 'bg-green-500' : 'bg-red-500'}`} />
                        <span className="text-xs font-bold uppercase tracking-widest">{health?.connected ? 'Hardware Linked' : 'System Degraded'}</span>
                    </div>
                </div>
            </div>

            {/* Main Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">

                {/* Left Col: Telemetry (4 cols) */}
                <div className="lg:col-span-4 space-y-6">
                    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl relative overflow-hidden group hover:border-indigo-500/30 transition-all shadow-xl">
                        <div className="absolute top-0 right-0 p-4 opacity-10"><Zap size={40} /></div>
                        <div className="flex items-center gap-4 mb-4">
                            <Battery className="text-green-500" />
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Power Matrix</span>
                        </div>
                        <div className="text-4xl font-black text-white mb-2">{telemetry?.battery?.toFixed(1) ?? '0.0'}%</div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${telemetry?.battery || 0}%` }}
                                className="h-full bg-gradient-to-r from-green-600 to-green-400"
                            />
                        </div>
                    </div>

                    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl group hover:border-indigo-500/30 transition-all shadow-xl">
                        <div className="flex items-center gap-4 mb-4">
                            <Compass className="text-indigo-500" />
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Inertial Path</span>
                        </div>
                        <div className="text-4xl font-black text-white">{telemetry?.imu?.heading?.toFixed(1) ?? '000'}°</div>
                        <div className="mt-4 flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                            <Activity size={12} className="text-indigo-500" /> Real-time IMU Flux
                        </div>
                    </div>

                    <div className="bg-indigo-600 border border-indigo-500 rounded-3xl p-8 shadow-xl shadow-indigo-600/20 group hover:scale-[1.02] transition-transform cursor-pointer relative overflow-hidden">
                        <div className="absolute -right-4 -bottom-4 opacity-20"><Rocket size={100} /></div>
                        <h3 className="text-xl font-bold text-white mb-2">Initialize Onboarding</h3>
                        <p className="text-indigo-100/70 text-sm font-medium leading-relaxed">System requires hardware binding for full G1 capability enhancement.</p>
                        <button onClick={() => window.location.href = '/onboarding'} className="mt-6 px-6 py-2 bg-white text-indigo-600 rounded-xl text-xs font-bold uppercase tracking-widest">Start Flow</button>
                    </div>
                </div>

                {/* Center: Vision (8 cols) */}
                <div className="lg:col-span-8 flex flex-col gap-8">
                    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-[40px] aspect-video relative overflow-hidden group shadow-2xl">
                        <img src="http://localhost:10792/stream" alt="Robot Feed" className="w-full h-full object-cover" />
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/40 pointer-events-none" />

                        {/* Overlays */}
                        <div className="absolute bottom-10 left-10 flex gap-4">
                            <div className="px-4 py-2 bg-black/40 backdrop-blur-md rounded-xl border border-white/10 flex items-center gap-3">
                                <div className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
                                <span className="text-xs font-bold text-white uppercase tracking-tighter">Live Stream</span>
                            </div>
                            <div className="px-4 py-2 bg-black/40 backdrop-blur-md rounded-xl border border-white/10 text-xs font-mono text-white/80">
                                {new Date().toLocaleTimeString()}
                            </div>
                        </div>

                        <div className="absolute bottom-10 right-10 flex gap-4">
                            <div className="px-4 py-2 bg-indigo-600/60 backdrop-blur-md rounded-xl border border-indigo-500/40 text-xs font-bold text-white uppercase tracking-widest">
                                G1 Primary Sensor
                            </div>
                        </div>

                        {/* Motion Vector UI Overlays */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-48 h-48 border border-white/5 rounded-full pointer-events-none opacity-20">
                            <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1 h-3 bg-white" />
                            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-1 h-3 bg-white" />
                            <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 w-3 h-1 bg-white" />
                            <div className="absolute right-0 top-1/2 -translate-y-1/2 translate-x-1/2 w-3 h-1 bg-white" />
                        </div>
                    </div>

                    {/* Controls */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center gap-3 mb-8">
                                <Monitor className="text-indigo-500 w-5 h-5" />
                                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Vector Control Array</h3>
                            </div>
                            <div className="grid grid-cols-3 gap-4 max-w-[240px] mx-auto">
                                <div />
                                <button
                                    onMouseDown={() => move(0.3, 0)}
                                    onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90"
                                >
                                    <ChevronUp />
                                </button>
                                <div />
                                <button
                                    onMouseDown={() => move(0, 0.5)}
                                    onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90"
                                >
                                    <ChevronLeft />
                                </button>
                                <button
                                    onClick={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-red-600/20 border border-red-500/30 flex items-center justify-center text-red-500 hover:bg-red-600 hover:text-white transition-all"
                                >
                                    <Square size={18} />
                                </button>
                                <button
                                    onMouseDown={() => move(0, -0.5)}
                                    onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90"
                                >
                                    <ChevronRight />
                                </button>
                                <div />
                                <button
                                    onMouseDown={() => move(-0.3, 0)}
                                    onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90"
                                >
                                    <ChevronDown />
                                </button>
                                <div />
                            </div>
                        </div>

                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center gap-3 mb-8">
                                <Shield className="text-indigo-500 w-5 h-5" />
                                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Active Safety Protocols</h3>
                            </div>
                            <div className="space-y-4">
                                {[
                                    { label: 'E-Stop Link', val: 'Operational' },
                                    { label: 'Proximity Field', val: 'Active' },
                                    { label: 'Thermal Guard', val: 'Safe' }
                                ].map((p, i) => (
                                    <div key={i} className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/5">
                                        <span className="text-xs font-medium text-slate-400">{p.label}</span>
                                        <span className="text-[10px] font-bold text-green-400 uppercase tracking-widest">{p.val}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
