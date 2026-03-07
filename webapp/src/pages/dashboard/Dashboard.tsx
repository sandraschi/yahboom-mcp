import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../lib/api'
import {
    Activity, Battery, Compass,
    ChevronUp, ChevronDown, ChevronLeft, ChevronRight,
    Monitor, Zap, Shield, Rocket, WifiOff, AlertTriangle, Link2,
    Keyboard, Navigation, Square
} from 'lucide-react'

// --- Types ---
interface ImuData {
    heading: number;
    pitch: number;
    roll: number;
    yaw: number;
    angular_velocity?: { x: number; y: number; z: number };
    linear_acceleration?: { x: number; y: number; z: number };
}

interface ScanData {
    nearest_m: number | null;
    obstacles: Record<string, number | null>;
}

interface Telemetry {
    battery: number | null;
    voltage: number | null;
    imu: ImuData | null;
    velocity: { linear: number; angular: number };
    position: { x: number; y: number; z: number } | null;
    scan: ScanData | null;
    source: 'live' | 'simulated';
}

interface Health {
    status: string;
    connected: boolean;
}

// --- Connection states ---
type ConnState = 'loading' | 'server_down' | 'bot_offline' | 'connected'

// Which WASD keys are currently held
interface KeysHeld {
    w: boolean; a: boolean; s: boolean; d: boolean;
}

const LINEAR_SPEED = 0.3   // m/s
const ANGULAR_SPEED = 0.5   // rad/s

const Dashboard = () => {
    const [telemetry, setTelemetry] = useState<Telemetry | null>(null)
    const [health, setHealth] = useState<Health | null>(null)
    const [connState, setConnState] = useState<ConnState>('loading')
    const [keysHeld, setKeysHeld] = useState<KeysHeld>({ w: false, a: false, s: false, d: false })
    const [wasdActive, setWasdActive] = useState(false)  // user has enabled keyboard mode
    const moveRef = useRef<(l: number, a: number) => void>(() => { })

    // --- Telemetry polling (via api client / Vite proxy to backend) ---
    useEffect(() => {
        const poll = async () => {
            try {
                const hData = await api.getHealth()
                if (hData.status) {
                    setHealth(hData)
                    setConnState(hData.connected ? 'connected' : 'bot_offline')
                }
                const tData = await api.getTelemetry()
                if (tData.battery !== undefined) setTelemetry(tData)
            } catch (err) {
                setHealth(null)
                setConnState('server_down')
            }
        }
        poll()
        const interval = setInterval(poll, 2000)
        return () => clearInterval(interval)
    }, [])

    // --- Move command ---
    const move = useCallback(async (linear: number, angular: number) => {
        if (connState !== 'connected') return
        try {
            await api.postMove(linear, angular)
        } catch {
            // movement failed
        }
    }, [connState])

    // Keep moveRef in sync so the keyboard handler always sees fresh version
    useEffect(() => { moveRef.current = move }, [move])

    // --- WASD keyboard handler ---
    useEffect(() => {
        if (!wasdActive) return

        const keyMap: Record<string, keyof KeysHeld> = {
            w: 'w', arrowup: 'w',
            s: 's', arrowdown: 's',
            a: 'a', arrowleft: 'a',
            d: 'd', arrowright: 'd',
        }

        const sendFromKeys = (held: KeysHeld) => {
            const linear = (held.w ? 1 : 0) - (held.s ? 1 : 0)
            const angular = (held.a ? 1 : 0) - (held.d ? 1 : 0)
            moveRef.current(linear * LINEAR_SPEED, angular * ANGULAR_SPEED)
        }

        const onDown = (e: KeyboardEvent) => {
            const k = keyMap[e.key.toLowerCase()]
            if (!k) return
            e.preventDefault()
            setKeysHeld(prev => {
                if (prev[k]) return prev  // already held — no extra fetch
                const next = { ...prev, [k]: true }
                sendFromKeys(next)
                return next
            })
        }

        const onUp = (e: KeyboardEvent) => {
            const k = keyMap[e.key.toLowerCase()]
            if (!k) return
            setKeysHeld(prev => {
                const next = { ...prev, [k]: false }
                sendFromKeys(next)
                return next
            })
        }

        window.addEventListener('keydown', onDown)
        window.addEventListener('keyup', onUp)
        return () => {
            window.removeEventListener('keydown', onDown)
            window.removeEventListener('keyup', onUp)
            // Stop robot when mode toggled off
            moveRef.current(0, 0)
        }
    }, [wasdActive])

    // --- Connection Banner ---
    const ConnBanner = () => {
        const banners: Record<Exclude<ConnState, 'connected'>, {
            icon: JSX.Element; title: string; sub: string;
            color: string; border: string; pulse: string
        }> = {
            loading: {
                icon: <Activity className="w-6 h-6 animate-spin" />,
                title: 'Connecting to backend…',
                sub: 'Waiting for response from http://localhost:10792',
                color: 'from-slate-900/95 to-slate-800/95',
                border: 'border-slate-600/40',
                pulse: 'bg-slate-400',
            },
            server_down: {
                icon: <WifiOff className="w-6 h-6" />,
                title: 'MCP Server Offline',
                sub: 'Cannot reach http://localhost:10792 — run start.ps1 to launch the backend.',
                color: 'from-red-950/95 to-slate-900/95',
                border: 'border-red-500/40',
                pulse: 'bg-red-500',
            },
            bot_offline: {
                icon: <AlertTriangle className="w-6 h-6" />,
                title: 'Robot Not Connected',
                sub: 'Backend is running but no ROS 2 bridge detected. Power on the Yahboom G1 and ensure ROSBridge is running on the robot.',
                color: 'from-amber-950/95 to-slate-900/95',
                border: 'border-amber-500/40',
                pulse: 'bg-amber-500',
            },
        }

        if (connState === 'connected') return null
        const cfg = banners[connState]
        const textColor = cfg.pulse === 'bg-red-500' ? 'text-red-400'
            : cfg.pulse === 'bg-amber-500' ? 'text-amber-400'
                : 'text-slate-400'

        return (
            <motion.div
                key={connState}
                initial={{ opacity: 0, y: -16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                className={`flex items-start gap-4 px-6 py-4 rounded-2xl border bg-gradient-to-r ${cfg.color} ${cfg.border} shadow-xl`}
            >
                <div className={`mt-0.5 flex-shrink-0 ${textColor}`}>{cfg.icon}</div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-1">
                        <span className={`w-2 h-2 rounded-full animate-pulse flex-shrink-0 ${cfg.pulse}`} />
                        <span className="text-sm font-bold text-white uppercase tracking-widest">{cfg.title}</span>
                    </div>
                    <p className="text-xs text-slate-400 leading-relaxed">{cfg.sub}</p>
                </div>
                {connState === 'bot_offline' && (
                    <button
                        onClick={() => window.location.href = '/onboarding'}
                        className="flex-shrink-0 flex items-center gap-2 px-4 py-2 bg-amber-500/20 hover:bg-amber-500/40 border border-amber-500/40 rounded-xl text-amber-300 text-xs font-bold uppercase tracking-widest transition-all"
                    >
                        <Link2 size={14} /> Setup
                    </button>
                )}
            </motion.div>
        )
    }

    const isOffline = connState !== 'connected'
    const imu = telemetry?.imu ?? null

    return (
        <div className="space-y-6 py-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Monitor className="text-indigo-400 w-8 h-8" />
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight">Mission Control</h1>
                        <p className="text-slate-400 text-sm">Industrial hardware interface for Yahboom G1 Substrate.</p>
                    </div>
                </div>
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border transition-all ${connState === 'connected' ? 'bg-green-500/10  border-green-500/20  text-green-400' :
                    connState === 'bot_offline' ? 'bg-amber-500/10  border-amber-500/20  text-amber-400' :
                        connState === 'server_down' ? 'bg-red-500/10    border-red-500/20    text-red-400' :
                            'bg-slate-500/10  border-slate-500/20  text-slate-400'
                    }`}>
                    <span className={`w-2 h-2 rounded-full animate-pulse ${connState === 'connected' ? 'bg-green-500' :
                        connState === 'bot_offline' ? 'bg-amber-500' :
                            connState === 'server_down' ? 'bg-red-500' : 'bg-slate-400'
                        }`} />
                    <span className="text-xs font-bold uppercase tracking-widest">
                        {connState === 'connected' ? 'Hardware Linked' :
                            connState === 'bot_offline' ? 'Bot Offline' :
                                connState === 'server_down' ? 'Server Down' : 'Connecting…'}
                    </span>
                </div>
            </div>

            {/* Connection Banner */}
            <AnimatePresence mode="wait">
                {isOffline && <ConnBanner key={connState} />}
            </AnimatePresence>

            {/* Main Grid */}
            <div className={`grid grid-cols-1 lg:grid-cols-12 gap-8 transition-opacity duration-500 ${isOffline ? 'opacity-40 pointer-events-none select-none' : 'opacity-100'}`}>

                {/* Left Col: Telemetry cards */}
                <div className="lg:col-span-4 space-y-6">

                    {/* Battery */}
                    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl relative overflow-hidden group hover:border-indigo-500/30 transition-all shadow-xl">
                        <div className="absolute top-0 right-0 p-4 opacity-10"><Zap size={40} /></div>
                        <div className="flex items-center gap-4 mb-4">
                            <Battery className="text-green-500" />
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Power Matrix</span>
                        </div>
                        <div className="text-4xl font-black text-white mb-1">
                            {telemetry?.battery?.toFixed(1) ?? '—'}%
                        </div>
                        {telemetry?.voltage != null && (
                            <div className="text-xs text-slate-500 font-mono mb-2">{telemetry.voltage.toFixed(1)} V</div>
                        )}
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <motion.div
                                initial={{ width: 0 }}
                                animate={{ width: `${telemetry?.battery ?? 0}%` }}
                                className={`h-full ${(telemetry?.battery ?? 100) < 20 ? 'bg-gradient-to-r from-red-600 to-red-400' : 'bg-gradient-to-r from-green-600 to-green-400'}`}
                            />
                        </div>
                        {telemetry?.source === 'simulated' && (
                            <div className="mt-2 text-[10px] text-amber-500/60 font-mono uppercase tracking-widest">[simulated]</div>
                        )}
                    </div>

                    {/* IMU */}
                    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl group hover:border-indigo-500/30 transition-all shadow-xl space-y-3">
                        <div className="flex items-center gap-4 mb-1">
                            <Compass className="text-indigo-500" />
                            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Inertial Path</span>
                        </div>
                        <div className="text-4xl font-black text-white">{imu?.heading?.toFixed(1) ?? '—'}°</div>
                        <div className="grid grid-cols-2 gap-4 mb-6">
                            {[
                                { label: 'Heading', val: imu?.heading },
                                { label: 'Pitch', val: imu?.pitch },
                                { label: 'Roll', val: imu?.roll },
                            ].map(({ label, val }) => (
                                <div key={label} className="bg-white/5 rounded-2xl p-4 border border-white/5">
                                    <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-0.5">{label}</div>
                                    <div className="text-sm font-mono text-slate-200">{typeof val === 'number' ? val.toFixed(1) : '—'}°</div>
                                </div>
                            ))}
                        </div>
                        {imu?.linear_acceleration && typeof imu.linear_acceleration === 'object' && (() => {
                            const accel = imu.linear_acceleration as Record<string, number>
                            return (
                                <div className="grid grid-cols-3 gap-2">
                                    {(['x', 'y', 'z'] as const).map(ax => (
                                        <div key={ax} className="bg-white/5 rounded-xl px-3 py-2 text-center">
                                            <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-0.5">Accel {ax.toUpperCase()}</div>
                                            <div className="text-sm font-mono text-slate-300">
                                                {typeof accel[ax] === 'number' ? accel[ax].toFixed(2) : '—'}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )
                        })()}
                        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-500 uppercase tracking-widest pt-4">
                            <Activity size={12} className="text-indigo-500" /> Real-time IMU Flux
                        </div>
                    </div>

                    {/* Position */}
                    {telemetry?.position && (
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center gap-4 mb-4">
                                <Navigation className="text-cyan-500 w-4 h-4" />
                                <span className="text-xs font-bold text-slate-500 uppercase tracking-widest">Odometry Position</span>
                            </div>
                            <div className="grid grid-cols-3 gap-2">
                                {(['x', 'y', 'z'] as const).map(ax => {
                                    const val = telemetry.position?.[ax]
                                    return (
                                        <div key={ax} className="bg-white/5 rounded-xl px-3 py-2 text-center">
                                            <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-0.5">{ax.toUpperCase()}</div>
                                            <div className="text-sm font-mono text-slate-200">{typeof val === 'number' ? val.toFixed(3) : '—'} m</div>
                                        </div>
                                    )
                                })}
                            </div>
                        </div>
                    )}

                    {/* Onboarding CTA */}
                    <div className="bg-indigo-600 border border-indigo-500 rounded-3xl p-8 shadow-xl shadow-indigo-600/20 group hover:scale-[1.02] transition-transform cursor-pointer relative overflow-hidden">
                        <div className="absolute -right-4 -bottom-4 opacity-20"><Rocket size={100} /></div>
                        <h3 className="text-xl font-bold text-white mb-2">Initialize Onboarding</h3>
                        <p className="text-indigo-100/70 text-sm font-medium leading-relaxed">System requires hardware binding for full G1 capability enhancement.</p>
                        <button onClick={() => window.location.href = '/onboarding'} className="mt-6 px-6 py-2 bg-white text-indigo-600 rounded-xl text-xs font-bold uppercase tracking-widest">Start Flow</button>
                    </div>
                </div>

                {/* Right: Camera + Controls */}
                <div className="lg:col-span-8 flex flex-col gap-8">

                    {/* Camera feed with HUD overlay */}
                    <div className="bg-[#0f0f12]/80 border border-white/5 rounded-[40px] aspect-video relative overflow-hidden group shadow-2xl">
                        <img src="http://localhost:10792/stream" alt="Robot Feed" className="w-full h-full object-cover" />

                        {/* Vignette */}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/40 pointer-events-none" />

                        {/* Corner brackets (tactical HUD) */}
                        <div className="absolute top-6 left-6 w-8 h-8 border-l-2 border-t-2 border-emerald-500/50 pointer-events-none" />
                        <div className="absolute top-6 right-6 w-8 h-8 border-r-2 border-t-2 border-emerald-500/50 pointer-events-none" />
                        <div className="absolute bottom-6 left-6 w-8 h-8 border-l-2 border-b-2 border-emerald-500/50 pointer-events-none" />
                        <div className="absolute bottom-6 right-6 w-8 h-8 border-r-2 border-b-2 border-emerald-500/50 pointer-events-none" />

                        {/* Crosshair */}
                        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none">
                            <div className="w-6 h-0.5 bg-emerald-400/40 absolute -left-3 top-0" />
                            <div className="w-6 h-0.5 bg-emerald-400/40 absolute  left-0  top-0 translate-x-0 ml-1 translate-x-1" />
                            <div className="h-6 w-0.5 bg-emerald-400/40 absolute top-0 left-0 -translate-y-3" />
                            <div className="h-6 w-0.5 bg-emerald-400/40 absolute top-0 left-0 translate-y-1" />
                            <div className="w-1.5 h-1.5 rounded-full border border-emerald-400/60" />
                        </div>

                        {/* Bottom-left: telemetry readout */}
                        <div className="absolute bottom-8 left-8 font-mono text-xs text-emerald-400 drop-shadow-md space-y-0.5 pointer-events-none">
                            <p>HDG: {imu?.heading?.toFixed(1) ?? '—'}°</p>
                            <p>PCH: {imu?.pitch?.toFixed(1) ?? '—'}°</p>
                            <p>ROL: {imu?.roll?.toFixed(1) ?? '—'}°</p>
                            <p>VEL: {telemetry?.velocity?.linear?.toFixed(2) ?? '—'} m/s</p>
                            {telemetry?.scan?.nearest_m != null && (
                                <p className={telemetry.scan.nearest_m < 0.4 ? 'text-red-400' : 'text-emerald-400'}>
                                    OBS: {telemetry.scan.nearest_m.toFixed(2)} m
                                </p>
                            )}
                        </div>

                        {/* Bottom-right: status tags */}
                        <div className="absolute bottom-8 right-8 flex flex-col items-end gap-2">
                            <div className="flex items-center gap-2 px-3 py-1.5 bg-black/40 backdrop-blur-md rounded-xl border border-white/10">
                                <div className="w-2 h-2 rounded-full bg-red-600 animate-pulse" />
                                <span className="text-xs font-bold text-white uppercase tracking-tighter">Live Stream</span>
                            </div>
                            <div className="px-3 py-1.5 bg-black/40 backdrop-blur-md rounded-xl border border-white/10 text-xs font-mono text-white/80">
                                {new Date().toLocaleTimeString()}
                            </div>
                            <div className="px-3 py-1.5 bg-indigo-600/60 backdrop-blur-md rounded-xl border border-indigo-500/40 text-xs font-bold text-white uppercase tracking-widest">
                                G1 Primary Sensor
                            </div>
                        </div>
                    </div>

                    {/* Controls row */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

                        {/* D-pad */}
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center gap-3 mb-6">
                                <Monitor className="text-indigo-500 w-5 h-5" />
                                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">D-Pad Control</h3>
                            </div>
                            <div className="grid grid-cols-3 gap-3 max-w-[180px] mx-auto">
                                <div />
                                <button onMouseDown={() => move(LINEAR_SPEED, 0)} onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90">
                                    <ChevronUp />
                                </button>
                                <div />
                                <button onMouseDown={() => move(0, ANGULAR_SPEED)} onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90">
                                    <ChevronLeft />
                                </button>
                                <button onClick={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-red-600/20 border border-red-500/30 flex items-center justify-center text-red-500 hover:bg-red-600 hover:text-white transition-all">
                                    <Square size={18} />
                                </button>
                                <button onMouseDown={() => move(0, -ANGULAR_SPEED)} onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90">
                                    <ChevronRight />
                                </button>
                                <div />
                                <button onMouseDown={() => move(-LINEAR_SPEED, 0)} onMouseUp={() => move(0, 0)}
                                    className="aspect-square rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center text-slate-300 hover:bg-indigo-600 hover:text-white transition-all active:scale-90">
                                    <ChevronDown />
                                </button>
                                <div />
                            </div>
                        </div>

                        {/* WASD keyboard control */}
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <Keyboard className="text-indigo-500 w-5 h-5" />
                                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Keyboard</h3>
                                </div>
                                <button
                                    onClick={() => setWasdActive(v => !v)}
                                    className={`px-3 py-1 rounded-lg text-[10px] font-bold uppercase tracking-widest transition-all ${wasdActive
                                        ? 'bg-emerald-500/20 border border-emerald-500/40 text-emerald-400'
                                        : 'bg-white/5 border border-white/10 text-slate-500 hover:text-slate-300'
                                        }`}
                                >
                                    {wasdActive ? 'Active' : 'Enable'}
                                </button>
                            </div>

                            {/* WASD visual */}
                            <div className="flex flex-col items-center gap-2">
                                <div className={`w-10 h-10 rounded-lg border-b-4 flex items-center justify-center font-bold text-sm transition-all ${keysHeld.w && wasdActive ? 'bg-indigo-600 border-indigo-800 text-white' : 'bg-slate-800 border-slate-900 text-slate-400'
                                    }`}>W</div>
                                <div className="flex gap-2">
                                    {(['a', 's', 'd'] as const).map(k => (
                                        <div key={k} className={`w-10 h-10 rounded-lg border-b-4 flex items-center justify-center font-bold text-sm uppercase transition-all ${keysHeld[k] && wasdActive ? 'bg-indigo-600 border-indigo-800 text-white' : 'bg-slate-800 border-slate-900 text-slate-400'
                                            }`}>{k}</div>
                                    ))}
                                </div>
                            </div>
                            <p className="text-[10px] text-slate-500 text-center mt-3 font-mono">
                                {wasdActive ? 'Keys active — click elsewhere to blur' : 'Click Enable to drive with keyboard'}
                            </p>
                        </div>

                        {/* Safety / Status */}
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center gap-3 mb-6">
                                <Shield className="text-indigo-500 w-5 h-5" />
                                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Safety</h3>
                            </div>
                            <div className="space-y-3">
                                {[
                                    { label: 'E-Stop Link', val: health?.connected ? 'Operational' : 'Standby' },
                                    {
                                        label: 'Nearest Obstacle',
                                        val: telemetry?.scan?.nearest_m != null
                                            ? `${telemetry.scan.nearest_m.toFixed(2)} m`
                                            : 'No LIDAR',
                                    },
                                    { label: 'Thermal Guard', val: health?.connected ? 'Safe' : 'Standby' },
                                ].map((p, i) => (
                                    <div key={i} className="flex justify-between items-center p-3 rounded-xl bg-white/5 border border-white/5">
                                        <span className="text-xs font-medium text-slate-400">{p.label}</span>
                                        <span className={`text-[10px] font-bold uppercase tracking-widest ${health?.connected ? 'text-green-400' : 'text-slate-500'}`}>{p.val}</span>
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
