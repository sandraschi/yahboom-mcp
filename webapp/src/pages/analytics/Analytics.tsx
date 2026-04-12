import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Zap, TrendingUp, BarChart3, WifiOff, AlertCircle } from 'lucide-react';
import { api, Telemetry } from '../../lib/api';

const Analytics: React.FC = () => {
    const [history, setHistory] = useState<Telemetry[]>([]);
    const [current, setCurrent] = useState<Telemetry | null>(null);
    const [isConnected, setIsConnected] = useState(true);

    useEffect(() => {
        const poll = async () => {
            try {
                const telemetry = await api.getTelemetry();
                setCurrent(telemetry);
                setIsConnected(telemetry.source === 'live');
                
                setHistory(prev => {
                    const newHistory = [...prev, telemetry];
                    // Keep last 15 points for the flux chart
                    return newHistory.slice(-15);
                });
            } catch (err) {
                setIsConnected(false);
            }
        };

        const interval = setInterval(poll, 1000);
        poll(); // Immediate first poll
        return () => clearInterval(interval);
    }, []);

    // Helper to calculate battery percentage mock if voltage is 0/null
    const getBatteryFlux = (t: Telemetry) => {
        if (!t.voltage) return 0;
        // Assume 12.6V is 100%, 10.5V is 0%
        const pct = ((t.voltage - 10.5) / (12.6 - 10.5)) * 100;
        return Math.max(5, Math.min(100, pct));
    };

    return (
        <div className="space-y-8 py-4 px-4 sm:px-6 animate-fade-in relative z-10">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Activity className="text-indigo-400 w-8 h-8" />
                    <div>
                        <h1 className="text-3xl font-bold text-white tracking-tight">Telemetry Analytics</h1>
                        <p className="text-slate-400 text-sm">Deep inspection of inertial pathing and power flux data.</p>
                    </div>
                </div>

                <div className={`flex items-center gap-2 px-3 py-1 rounded-full border text-[10px] font-bold uppercase tracking-widest ${
                    isConnected ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-red-500/10 text-red-400 border-red-500/20'
                }`}>
                    {isConnected ? 'LIVE FEED' : 'OFFLINE / SIMULATED'}
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Power Flux Chart */}
                <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 lg:p-10 shadow-xl overflow-hidden relative">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                            <Zap className="text-yellow-400 w-4 h-4" />
                            Power Flux History
                        </h3>
                        <span className="text-xs font-medium text-slate-500 font-mono">
                            {current?.voltage?.toFixed(2) ?? '0.00'}V • {current?.battery?.toFixed(0) ?? '0'}%
                        </span>
                    </div>
                    <div className="h-64 flex items-end gap-1 px-2">
                        {/* Fill with empty spacers if history is sparse */}
                        {Array.from({ length: 15 - history.length }).map((_, i) => (
                            <div key={`spacer-${i}`} className="flex-1 h-1 bg-white/5 rounded-t-sm" />
                        ))}
                        {history.map((t, i) => (
                            <motion.div
                                key={i}
                                initial={{ height: 0 }}
                                animate={{ height: `${getBatteryFlux(t)}%` }}
                                className={`flex-1 rounded-t-sm border-t ${
                                    (t.voltage ?? 0) < 11.0 
                                    ? 'bg-red-500/40 border-red-400/30' 
                                    : 'bg-indigo-500/40 border-indigo-400/30'
                                }`}
                            />
                        ))}
                    </div>
                    <div className="mt-4 flex justify-between text-[8px] uppercase tracking-widest text-slate-600 font-bold">
                        <span>T-15s</span>
                        <span>Now</span>
                    </div>
                </div>

                {/* Inertial Heading Compass */}
                <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 lg:p-10 shadow-xl overflow-hidden relative">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                            <TrendingUp className="text-green-400 w-4 h-4" />
                            Inertial Pathing
                        </h3>
                        <span className="text-xs font-medium text-slate-500 font-mono">
                            IMU ACTIVE
                        </span>
                    </div>
                    <div className="h-64 flex items-center justify-center p-8">
                        <div className="w-48 h-48 rounded-full border border-white/5 relative flex items-center justify-center">
                            <div className="absolute inset-0 border-2 border-dashed border-indigo-500/20 rounded-full animate-[spin_30s_linear_infinite]" />
                            
                            {/* The Compass Needle */}
                            <motion.div 
                                className="absolute inset-0 flex items-center justify-center"
                                animate={{ rotate: current?.imu?.yaw ?? 0 }}
                                transition={{ type: 'spring', stiffness: 50, damping: 10 }}
                            >
                                <div className="w-1 h-20 bg-gradient-to-t from-transparent via-cyan-500 to-cyan-400 rounded-full origin-bottom -translate-y-10" />
                                <div className="w-2 h-2 bg-cyan-400 rounded-full absolute" />
                            </motion.div>

                            <div className="text-center z-10 bg-slate-900/40 backdrop-blur-md px-4 py-2 rounded-xl border border-white/5">
                                <span className="text-2xl font-bold text-white block font-mono">
                                    {(current?.imu?.yaw ?? 0).toFixed(1)}°
                                </span>
                                <span className="text-[10px] text-indigo-400 font-bold uppercase tracking-widest mt-1">
                                    {isConnected ? 'Live Euler' : 'Offline'}
                                </span>
                            </div>

                            {/* Degree Markers */}
                            {[0, 90, 180, 270].map(deg => (
                                <div 
                                    key={deg}
                                    className="absolute text-[8px] font-bold text-slate-600"
                                    style={{
                                        top: deg === 0 ? '8px' : deg === 180 ? 'auto' : '50%',
                                        bottom: deg === 180 ? '8px' : 'auto',
                                        left: deg === 270 ? '8px' : deg === 90 ? 'auto' : '50%',
                                        right: deg === 90 ? '8px' : 'auto',
                                        transform: (deg === 90 || deg === 270) ? 'translateY(-50%)' : 'translateX(-50%)'
                                    }}
                                >
                                    {deg === 0 ? 'N' : deg === 90 ? 'E' : deg === 180 ? 'S' : 'W'}
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            {/* Status Footer */}
            <div className="flex gap-4">
               <div className="flex-1 bg-white/5 border border-white/5 rounded-2xl p-4 flex items-center gap-4">
                   <div className={`p-2 rounded-lg ${isConnected ? 'bg-emerald-500/20' : 'bg-red-500/20'}`}>
                       <BarChart3 className={isConnected ? 'text-emerald-400' : 'text-red-400'} size={20} />
                   </div>
                   <div>
                       <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Data Fidelity</p>
                       <p className="text-sm font-mono text-white">{isConnected ? 'High (1Hz Polling)' : 'Null / Signal Lost'}</p>
                   </div>
               </div>
               {!isConnected && (
                   <div className="flex-1 bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 flex items-center gap-4 animate-pulse">
                       <AlertCircle className="text-amber-500" size={20} />
                       <p className="text-xs text-amber-500/80 font-medium">
                           Robot bridge disconnected. Viewing simulated telemetry buffer.
                       </p>
                   </div>
               )}
            </div>
        </div>
    );
};

export default Analytics;
