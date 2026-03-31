import React, { useState, useEffect, useCallback } from 'react';
import { Gauge, WifiOff, RefreshCw } from 'lucide-react';
import { api, type SensorsResponse } from '../../lib/api';

const POLL_MS = 500;

const IR_LABELS = ['FL', 'F', 'FR', 'R', 'BR', 'B', 'BL', 'L'];
const LINE_LABELS = ['L', 'ML', 'C', 'MR', 'R'];

const SensorsPage: React.FC = () => {
    const [data, setData] = useState<SensorsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchSensors = useCallback(async () => {
        try {
            const res = await api.getSensors();
            setData(res);
            setError(null);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to load sensors');
            setData(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchSensors();
        const id = setInterval(fetchSensors, POLL_MS);
        return () => clearInterval(id);
    }, [fetchSensors]);


    const irValues: number[] = Array.isArray(data?.ir_proximity) ? data.ir_proximity : [];
    const lineValues: number[] = Array.isArray(data?.line_sensors) ? data.line_sensors : [];

    if (loading && !data) {
        return (
            <div className="flex items-center justify-center py-24 text-slate-500">
                <RefreshCw className="w-8 h-8 animate-spin mr-2" />
                Loading sensors…
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full py-4 px-4 sm:px-6 max-w-5xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <Gauge className="text-indigo-400 w-8 h-8" />
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight">Sensors</h1>
                        <p className="text-slate-400 text-sm">
                            IR proximity and line-following front sensors.
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    {data?.source === 'live' ? (
                        <span className="px-3 py-1.5 rounded-xl border border-emerald-500/40 bg-emerald-500/10 text-emerald-400 text-xs font-bold uppercase">
                            Live
                        </span>
                    ) : (
                        <span className="px-3 py-1.5 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-400 text-xs font-bold uppercase flex items-center gap-1.5">
                            <WifiOff size={12} />
                            Offline
                        </span>
                    )}
                </div>
            </div>

            {error && (
                <div className="mb-4 p-4 rounded-xl border border-red-500/20 bg-red-500/10 text-red-200 text-sm">
                    {error}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* IR proximity sensors */}
                <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
                    <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">
                        IR proximity sensors
                    </h2>
                    <p className="text-xs text-slate-500 mb-4">
                        Distance readings (m). Configure ROS topic on robot to see live values.
                    </p>
                    <div className="flex flex-wrap gap-3">
                        {(irValues.length ? irValues : [null, null, null, null, null, null]).map((val, i) => (
                            <div
                                key={i}
                                className="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10 min-w-[3.5rem]"
                            >
                                <span className="text-[10px] text-slate-500 uppercase font-mono">
                                    {IR_LABELS[i] ?? `IR${i}`}
                                </span>
                                <span className="text-sm font-mono text-slate-200 mt-1">
                                    {val != null ? val.toFixed(2) : '—'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Line-following front sensors */}
                <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
                    <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">
                        Line-following front sensors
                    </h2>
                    <p className="text-xs text-slate-500 mb-4">
                        Front L / ML / C / MR / R. Configure line-sensor topic on robot for live values.
                    </p>
                    <div className="flex justify-center gap-2">
                        {(lineValues.length ? lineValues : [null, null, null, null, null]).map((val, i) => (
                            <div
                                key={i}
                                className="flex flex-col items-center p-3 rounded-xl bg-white/5 border border-white/10 flex-1 max-w-[4rem]"
                            >
                                <span className="text-[10px] text-slate-500 uppercase font-mono">
                                    {LINE_LABELS[i] ?? `L${i}`}
                                </span>
                                <span className="text-sm font-mono text-slate-200 mt-1">
                                    {val != null ? val.toFixed(2) : '—'}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

            </div>
        </div>
    );
};

export default SensorsPage;
