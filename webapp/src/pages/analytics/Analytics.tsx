import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Zap, TrendingUp, BarChart3 } from 'lucide-react';

const Analytics: React.FC = () => {
    return (
        <div className="space-y-8 py-4 px-4 sm:px-6">
            <div className="flex items-center gap-4">
                <Activity className="text-indigo-400 w-8 h-8" />
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Telemetry Analytics</h1>
                    <p className="text-slate-400 text-sm">Deep inspection of inertial pathing and power flux data.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 lg:p-10 shadow-xl overflow-hidden relative">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                            <Zap className="text-yellow-400 w-4 h-4" />
                            Power Consumption
                        </h3>
                        <span className="text-xs font-medium text-slate-500">Last 60 Minutes</span>
                    </div>
                    <div className="h-64 flex items-end gap-2 px-2">
                        {[40, 65, 45, 90, 75, 55, 80, 60, 95, 70, 50, 85].map((val, i) => (
                            <motion.div
                                key={i}
                                initial={{ height: 0 }}
                                animate={{ height: `${val}%` }}
                                transition={{ duration: 1, delay: i * 0.05 }}
                                className="flex-1 bg-gradient-to-t from-indigo-500/20 to-indigo-500/60 rounded-t-lg border-t border-indigo-400/30"
                            />
                        ))}
                    </div>
                </div>

                <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 lg:p-10 shadow-xl overflow-hidden relative">
                    <div className="flex items-center justify-between mb-8">
                        <h3 className="text-sm font-bold text-white uppercase tracking-widest flex items-center gap-2">
                            <TrendingUp className="text-green-400 w-4 h-4" />
                            Inertial Heading
                        </h3>
                        <span className="text-xs font-medium text-slate-500">Real-time Path</span>
                    </div>
                    <div className="h-64 flex items-center justify-center p-8">
                        <div className="w-48 h-48 rounded-full border border-white/5 relative flex items-center justify-center">
                            <div className="absolute inset-0 border-2 border-dashed border-indigo-500/10 rounded-full animate-[spin_20s_linear_infinite]" />
                            <div className="w-1 h-20 bg-gradient-to-t from-transparent to-green-400 rounded-full origin-bottom rotate-[45deg]" />
                            <div className="text-center">
                                <span className="text-2xl font-bold text-white block">45.0°</span>
                                <span className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">NE Sector</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
