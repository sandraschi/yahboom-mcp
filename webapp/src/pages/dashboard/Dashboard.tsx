import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { api } from '../../lib/api'
import {
    Activity, Battery, Compass,
    ChevronUp, ChevronDown, ChevronLeft, ChevronRight,
    Monitor, Zap, Shield, WifiOff, AlertTriangle, Link2,
    Keyboard, Navigation, Square, CameraOff, Loader2, Volume2, MessageSquare,
    Camera
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
    sonar_m: number | null;
    line_sensors: number[] | null;
    button_pressed: boolean;
}

export default function Dashboard() {
    const [telemetry, setTelemetry] = useState<Telemetry | null>(null)
    const [connected, setConnected] = useState(false)
    const [lastFrame, setLastFrame] = useState<string | null>(null)
    const [keysHeld, setKeysHeld] = useState<Record<string, boolean>>({})
    const [wasdActive, setWasdActive] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isReconnecting, setIsReconnecting] = useState(false)

    // WebSocket for telemetry
    useEffect(() => {
        let ws: WebSocket | null = null;
        let reconnectTimer: any = null;

        const connect = () => {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/telemetry`;
            
            console.log('Connecting telemetry WS:', wsUrl);
            ws = new WebSocket(wsUrl);

            ws.onopen = () => {
                setConnected(true);
                setError(null);
                setIsReconnecting(false);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'telemetry') {
                    setTelemetry(data.data);
                } else if (data.type === 'image') {
                    setLastFrame(data.data);
                }
            };

            ws.onclose = () => {
                setConnected(false);
                setIsReconnecting(true);
                reconnectTimer = setTimeout(connect, 3000);
            };

            ws.onerror = () => {
                setConnected(false);
            };
        };

        connect();
        return () => {
            if (ws) ws.close();
            clearTimeout(reconnectTimer);
        };
    }, []);

    // Drive keyboard handler
    useEffect(() => {
        if (!wasdActive) return;

        const handleKeyDown = (e: KeyboardEvent) => {
            const key = e.key.toLowerCase();
            if (['w', 'a', 's', 'd'].includes(key)) {
                setKeysHeld(prev => ({ ...prev, [key]: true }));
            }
        };

        const handleKeyUp = (e: KeyboardEvent) => {
            const key = e.key.toLowerCase();
            if (['w', 'a', 's', 'd'].includes(key)) {
                setKeysHeld(prev => ({ ...prev, [key]: false }));
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
        };
    }, [wasdActive]);

    // Directional control loop
    useEffect(() => {
        if (!wasdActive || !connected) return;

        const interval = setInterval(() => {
            let lin_x = 0;
            let ang_z = 0;
            const speed = 0.5;
            const turnSpeed = 1.0;

            if (keysHeld.w) lin_x += speed;
            if (keysHeld.s) lin_x -= speed;
            if (keysHeld.a) ang_z += turnSpeed;
            if (keysHeld.d) ang_z -= turnSpeed;

            if (lin_x !== 0 || ang_z !== 0) {
                api.postMove(lin_x, ang_z);
            }
        }, 100);

        return () => clearInterval(interval);
    }, [wasdActive, keysHeld, connected]);

    const handleReconnect = async () => {
        setIsReconnecting(true);
        try {
            await api.postReconnect();
        } catch (err) {
            console.error('Manual reconnect failed:', err);
        } finally {
            setIsReconnecting(false);
        }
    };

    return (
        <div className="flex flex-col gap-6 p-4 lg:p-8 animate-in fade-in duration-700">
            {/* Header / Status Bar */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-black text-white tracking-tighter flex items-center gap-3">
                        <Activity className="text-indigo-500 animate-pulse" />
                        CONTROL CENTER
                    </h1>
                    <p className="text-slate-500 text-xs font-medium tracking-[0.2em] mt-1 ml-9">
                        SOTA v1.20 | ROS 2 HUMBLE | VIENNA_ALSERGRUND
                    </p>
                </div>
                
                <div className="flex items-center gap-2">
                    <div className={`px-4 py-2 rounded-2xl border flex items-center gap-2 transition-all ${
                        connected 
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                        : 'bg-red-500/10 border-red-500/20 text-red-400'
                    }`}>
                        <div className={`w-2 h-2 rounded-full ${connected ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
                        <span className="text-[10px] font-black uppercase tracking-widest">
                            {connected ? 'Hardware Connected' : 'Link Offline'}
                        </span>
                    </div>
                    
                    {!connected && (
                        <button
                            onClick={handleReconnect}
                            disabled={isReconnecting}
                            className="p-2 aspect-square bg-white/5 border border-white/10 rounded-2xl text-slate-400 hover:text-white hover:bg-white/10 transition-all disabled:opacity-50"
                        >
                            <Loader2 className={`w-5 h-5 ${isReconnecting ? 'animate-spin' : ''}`} />
                        </button>
                    )}
                </div>
            </div>

            {/* Error Alert */}
            <AnimatePresence>
                {error && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="bg-red-500/10 border border-red-500/20 rounded-3xl p-4 flex items-center gap-3 text-red-400 text-sm">
                            <AlertTriangle size={18} />
                            <span className="font-medium">{error}</span>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* Left Column: Visual Feedback & Map */}
                <div className="xl:col-span-2 space-y-6">
                    {/* Primary Camera / Visual Feed */}
                    <div className="relative aspect-video bg-black rounded-[2.5rem] border border-white/5 overflow-hidden shadow-2xl group">
                        {lastFrame ? (
                            <img 
                                src={`data:image/jpeg;base64,${lastFrame}`} 
                                className="w-full h-full object-cover"
                                alt="Robot Camera Feed"
                            />
                        ) : (
                            <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-slate-900/50">
                                <CameraOff className="text-slate-700 w-16 h-16 animate-pulse" />
                                <p className="text-slate-500 text-xs font-bold uppercase tracking-widest">Visual Stream Offline</p>
                            </div>
                        )}
                        
                        {/* Stream Overlay Details */}
                        <div className="absolute top-6 left-6 flex flex-col gap-2">
                            <div className="px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-xl border border-white/10 flex items-center gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                                <span className="text-[9px] font-bold text-white uppercase tracking-widest">Live Feed</span>
                            </div>
                            <div className="px-3 py-1.5 bg-black/60 backdrop-blur-md rounded-xl border border-white/10 flex items-center gap-2">
                                <Volume2 size={12} className="text-slate-400" />
                                <span className="text-[9px] font-bold text-slate-300 uppercase tracking-widest">Mic Idle</span>
                            </div>
                        </div>

                        {/* Control Hud Overlay */}
                        <div className="absolute inset-0 pointer-events-none border-[20px] border-transparent group-hover:border-indigo-500/5 transition-all duration-700" />
                        
                        <div className="absolute bottom-8 right-8 pointer-events-auto">
                            <button 
                                onClick={() => api.postTool('stop_all')}
                                className="w-16 h-16 rounded-full bg-red-600/90 hover:bg-red-500 shadow-2xl shadow-red-500/40 flex items-center justify-center text-white transition-all hover:scale-110 active:scale-95 group"
                                title="Emergency Stop"
                            >
                                <Square size={24} className="group-hover:scale-110 transition-transform" />
                            </button>
                        </div>
                        
                        {/* Orientation Indicator */}
                        <div className="absolute bottom-8 left-8 flex items-center gap-4 bg-black/40 backdrop-blur-lg p-4 rounded-3xl border border-white/10">
                            <div className="relative w-12 h-12 flex items-center justify-center">
                                <div className="absolute inset-0 rounded-full border-2 border-dashed border-white/10" />
                                <Compass 
                                    className="text-indigo-400 w-8 h-8 transition-transform duration-300" 
                                    style={{ transform: `rotate(${telemetry?.imu?.heading || 0}deg)` }}
                                />
                            </div>
                            <div>
                                <p className="text-[8px] font-black text-slate-500 uppercase tracking-widest">Heading</p>
                                <p className="text-lg font-black text-white leading-none">{(telemetry?.imu?.heading || 0).toFixed(1)}°</p>
                            </div>
                        </div>
                    </div>

                    {/* Sensor Overlay Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <TelemetryCard 
                            icon={<Zap className="text-amber-500" />} 
                            label="Core Energy" 
                            value={telemetry?.battery ? `${telemetry.battery}%` : '--'} 
                            subValue={telemetry?.voltage ? `${telemetry.voltage}v` : '--'}
                            trend={telemetry?.battery ? (telemetry.battery > 20 ? 'stable' : 'warning') : 'idle'}
                        />
                        <TelemetryCard 
                            icon={<Compass className="text-indigo-500" />} 
                            label="Tilt/Trim" 
                            value={`${telemetry?.imu?.pitch?.toFixed(1) || 0}°`} 
                            subValue={`P: ${telemetry?.imu?.roll?.toFixed(1) || 0}°`}
                        />
                        <TelemetryCard 
                            icon={<Navigation className="text-cyan-500" />} 
                            label="Speed" 
                            value={`${telemetry?.velocity?.linear?.toFixed(2) || 0} m/s`} 
                            subValue={`Rot: ${telemetry?.velocity?.angular?.toFixed(2) || 0}`}
                        />
                        <TelemetryCard 
                            icon={<Shield className="text-emerald-500" />} 
                            label="Obstacles" 
                            value={telemetry?.scan?.nearest_m ? `${telemetry.scan.nearest_m}m` : 'Clear'} 
                            subValue="LIDAR Active"
                            trend={telemetry?.scan?.nearest_m && telemetry.scan.nearest_m < 0.5 ? 'danger' : 'stable'}
                        />
                    </div>
                </div>

                {/* Right Column: Control & Missions */}
                <div className="space-y-6">
                    {/* Control Panel Section */}
                    <div className="space-y-4">
                        <div className="flex items-center gap-2 mb-2 px-2">
                            <div className="w-1 h-4 bg-indigo-500 rounded-full" />
                            <h2 className="text-sm font-black text-white uppercase tracking-[0.2em]">Deployment System</h2>
                        </div>

                        {/* Camera PTZ Control */}
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <Camera className="text-cyan-500 w-5 h-5" />
                                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Camera PTZ</h3>
                                </div>
                                <button
                                    onClick={() => api.postTool('camera_reset')}
                                    className="px-3 py-1 bg-white/5 border border-white/10 rounded-lg text-[10px] font-bold text-slate-400 uppercase tracking-widest hover:text-white transition-all"
                                    title="Center Camera"
                                >
                                    Center
                                </button>
                            </div>

                            <div className="grid grid-cols-3 gap-2 max-w-[140px] mx-auto">
                                <div />
                                <button 
                                    onClick={() => api.postTool('camera_move', 'up')}
                                    className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                                    title="Tilt Up"
                                >
                                    <ChevronUp size={20} />
                                </button>
                                <div />
                                
                                <button 
                                    onClick={() => api.postTool('camera_move', 'left')}
                                    className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                                    title="Pan Left"
                                >
                                    <ChevronLeft size={20} />
                                </button>
                                <div className="w-10 h-10 flex items-center justify-center">
                                    <div className="w-1.5 h-1.5 rounded-full bg-cyan-500/50 shadow-[0_0_8px_rgba(6,182,212,0.5)]" />
                                </div>
                                <button 
                                    onClick={() => api.postTool('camera_move', 'right')}
                                    className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                                    title="Pan Right"
                                >
                                    <ChevronRight size={20} />
                                </button>

                                <div />
                                <button 
                                    onClick={() => api.postTool('camera_move', 'down')}
                                    className="w-10 h-10 rounded-xl bg-slate-800 border border-white/5 flex items-center justify-center text-slate-400 hover:text-cyan-400 hover:bg-slate-700 transition-all active:scale-90"
                                    title="Tilt Down"
                                >
                                    <ChevronDown size={20} />
                                </button>
                                <div />
                            </div>
                            
                            <p className="text-[10px] text-slate-600 text-center mt-4 uppercase tracking-tighter">
                                Pan: ID 1 | Tilt: ID 2
                            </p>
                        </div>

                        {/* Keyboard visual mockup (Simplified) */}
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center justify-between mb-4">
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
                            <p className="text-[10px] text-slate-500 text-center font-mono">
                                Use WASD keys to drive
                            </p>
                        </div>

                        {/* Lightstrip Control Matrix */}
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <Zap className="text-amber-500 w-5 h-5" />
                                    <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Light Control</h3>
                                </div>
                                <button
                                    onClick={() => api.postLightstrip('off')}
                                    className="px-3 py-1 bg-red-500/10 border border-red-500/20 rounded-lg text-[10px] font-bold text-red-400 uppercase tracking-widest hover:bg-red-500/20 transition-all"
                                >
                                    Stop
                                </button>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    onClick={() => api.postLightstrip('pattern', 10)}
                                    className="col-span-2 h-12 rounded-2xl bg-gradient-to-r from-blue-600/20 to-red-600/20 border border-white/10 flex items-center justify-center text-xs font-black text-white uppercase tracking-widest"
                                >
                                    Patrol Car Pattern
                                </button>
                                <button
                                    onClick={() => api.postLightstrip('set', 255, 0, 0)}
                                    className="h-10 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-[10px] font-bold uppercase"
                                >
                                    Danger Red
                                </button>
                                <button
                                    onClick={() => api.postLightstrip('set', 0, 255, 0)}
                                    className="h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase"
                                >
                                    Safe Green
                                </button>
                            </div>
                        </div>

                        {/* Intelligence Hub */}
                        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 backdrop-blur-xl shadow-xl">
                            <div className="flex items-center gap-3 mb-4">
                                <MessageSquare className="text-indigo-400 w-5 h-5" />
                                <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest">Intelligence Hub</h3>
                            </div>
                            <div className="space-y-3">
                                <button 
                                    onClick={() => api.postTool('camera_center')}
                                    className="w-full py-3 bg-white/5 border border-white/10 rounded-xl text-[10px] font-bold text-slate-400 uppercase tracking-widest hover:bg-indigo-500/20 hover:text-indigo-300 transition-all text-left px-4 flex items-center justify-between group"
                                >
                                    <span>Hardware Centering Assist</span>
                                    <Link2 size={12} className="group-hover:rotate-45 transition-transform" />
                                </button>
                                <div className="p-3 bg-indigo-500/5 border border-indigo-500/10 rounded-xl">
                                    <p className="text-[10px] text-indigo-300/60 leading-relaxed italic">
                                        "Positioning servos at 90° for assembly alignment."
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

function TelemetryCard({ icon, label, value, subValue, trend }: { icon: any, label: string, value: string, subValue: string, trend?: 'stable' | 'warning' | 'danger' | 'idle' }) {
    const trendColors = {
        stable: 'bg-emerald-500',
        warning: 'bg-amber-500',
        danger: 'bg-red-500 animate-pulse',
        idle: 'bg-slate-700'
    };

    return (
        <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-5 backdrop-blur-xl shadow-xl">
            <div className="flex items-center justify-between mb-4">
                <div className="w-10 h-10 rounded-2xl bg-white/5 border border-white/10 flex items-center justify-center">
                    {icon}
                </div>
                {trend && (
                    <div className={`w-1.5 h-1.5 rounded-full ${trendColors[trend]}`} />
                )}
            </div>
            <p className="text-[8px] font-black text-slate-500 uppercase tracking-[0.2em] mb-1">{label}</p>
            <p className="text-xl font-black text-white tracking-tight">{value}</p>
            <p className="text-[10px] text-slate-600 font-medium mt-1">{subValue}</p>
        </div>
    );
}
