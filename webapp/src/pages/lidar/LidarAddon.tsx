import React, { useState, useEffect } from 'react';
import { ScanLine, ExternalLink, Package, CheckCircle2, AlertCircle } from 'lucide-react';
import { api, isBridgeLiveTelemetry } from '../../lib/api';

const MS200_PRICE_USD = 139;
const MS200_DOC_URL = 'https://www.yahboom.net/study/MS200';

const LidarAddonPage: React.FC = () => {
    const [scanActive, setScanActive] = useState<boolean | null>(null);
    const [connected, setConnected] = useState(false);

    useEffect(() => {
        let alive = true;
        const poll = async () => {
            try {
                const t = await api.getTelemetry();
                if (!alive) return;
                setConnected(isBridgeLiveTelemetry(t));
                const scan = (t as { scan?: { nearest_m?: number | null; obstacles?: Record<string, unknown> } }).scan;
                const hasScan =
                    scan &&
                    (scan.nearest_m != null || (scan.obstacles && Object.values(scan.obstacles).some((v) => v != null)));
                setScanActive(hasScan ?? false);
            } catch {
                if (alive) setScanActive(false);
                setConnected(false);
            }
        };
        poll();
        const id = setInterval(poll, 2000);
        return () => {
            alive = false;
            clearInterval(id);
        };
    }, []);

    return (
        <div className="flex flex-col h-full py-4 px-4 sm:px-6 max-w-5xl mx-auto">
            <div className="flex items-center gap-4 mb-6">
                <ScanLine className="text-indigo-400 w-8 h-8" />
                <div>
                    <h1 className="text-2xl font-bold text-white tracking-tight">Lidar addon (MS200)</h1>
                    <p className="text-slate-400 text-sm">
                        Yahboom MS200 TOF LIDAR for Raspbot v2 — setup and integration status.
                    </p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
                    <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4 flex items-center gap-2">
                        <Package className="w-4 h-4 text-indigo-400" />
                        Product and price
                    </h2>
                    <ul className="text-sm text-slate-300 space-y-2">
                        <li><strong className="text-white">Yahboom MS200</strong> TOF LIDAR — 360°, 0.03–12 m</li>
                        <li>ROS 1 / ROS 2 drivers; publishes <code className="bg-white/10 px-1 rounded">/scan</code></li>
                        <li><strong className="text-emerald-400">~${MS200_PRICE_USD} USD</strong> (check store for current price)</li>
                    </ul>
                    <a
                        href={MS200_DOC_URL}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 mt-4 px-4 py-2 rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 text-sm"
                    >
                        <ExternalLink size={14} />
                        Yahboom MS200 tutorial
                    </a>
                </div>

                <div className="rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
                    <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">
                        Integration status
                    </h2>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            {connected ? (
                                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            ) : (
                                <AlertCircle className="w-5 h-5 text-amber-400" />
                            )}
                            <span className="text-slate-300">
                                Robot connection: {connected ? 'Connected' : 'Offline'}
                            </span>
                        </div>
                        <div className="flex items-center gap-3">
                            {scanActive === true ? (
                                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                            ) : (
                                <AlertCircle className="w-5 h-5 text-slate-500" />
                            )}
                            <span className="text-slate-300">
                                /scan data: {scanActive === true ? 'Active (LIDAR or scan topic publishing)' : 'No data yet'}
                            </span>
                        </div>
                    </div>
                    <p className="text-xs text-slate-500 mt-4">
                        When the MS200 is installed and the ROS 2 driver is running on the Pi, /scan will publish and this page and the Lidar Map will show live data.
                    </p>
                </div>

                <div className="lg:col-span-2 rounded-2xl border border-white/10 bg-[#0f0f12]/80 p-5">
                    <h2 className="text-sm font-bold text-slate-300 uppercase tracking-wider mb-4">
                        Setup steps (after you have the hardware)
                    </h2>
                    <ol className="list-decimal list-inside text-sm text-slate-300 space-y-2">
                        <li>Mount the MS200 and connect it to the Raspberry Pi (USB–serial).</li>
                        <li>On the Pi: install Yahboom’s MS200 ROS 2 driver and run it so <code className="bg-white/10 px-1 rounded">/scan</code> is published.</li>
                        <li>Start rosbridge on the robot as usual. This dashboard already subscribes to /scan; the <strong>Lidar Map</strong> page and telemetry will show data automatically.</li>
                    </ol>
                    <p className="text-xs text-slate-500 mt-4">
                        See <a href={MS200_DOC_URL} target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">Yahboom MS200 tutorial</a> and <code className="bg-white/10 px-1 rounded">docs/HARDWARE_AND_ROS2.md</code> (section 5).
                    </p>
                </div>
            </div>
        </div>
    );
};

export default LidarAddonPage;
