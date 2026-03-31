import React, { useState, useEffect, useRef } from 'react';
import { 
    Shield, 
    Activity, 
    Terminal as TerminalIcon, 
    AlertCircle, 
    CheckCircle2, 
    RefreshCw,
    Wifi,
    Cpu,
    Zap,
    Search,
    ChevronRight,
    Play,
    Camera,
    Mic
} from 'lucide-react';
import { api, DiagStackResponse } from '../../lib/api';

const Diagnostics: React.FC = () => {
    const [stack, setStack] = useState<DiagStackResponse | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [command, setCommand] = useState('');
    const [shellOutput, setShellOutput] = useState<string[]>([]);
    const [loading, setLoading] = useState(true);
    const [executing, setExecuting] = useState(false);
    const logEndRef = useRef<HTMLDivElement>(null);
    const shellEndRef = useRef<HTMLDivElement>(null);

    const fetchStack = async () => {
        try {
            const data = await api.getDiagStack();
            setStack(data);
        } catch (error) {
            console.error('Failed to fetch diagnostic stack:', error);
        }
    };

    const fetchLogs = async () => {
        try {
            const data = await api.getDiagLogs();
            if (data.logs) {
                // Split string logs into lines for the viewer
                setLogs(data.logs.trim().split('\n'));
            }
        } catch (error) {
            console.error('Failed to fetch kernel logs:', error);
        }
    };

    const handleExecute = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!command.trim() || executing) return;

        setExecuting(true);
        const timestamp = new Date().toLocaleTimeString();
        setShellOutput(prev => [...prev, `[${timestamp}] $ ${command}`]);

        try {
            const result = await api.postExecCommand(command);
            if (result.stdout) setShellOutput(prev => [...prev, result.stdout]);
            if (result.stderr) setShellOutput(prev => [...prev, `Error: ${result.stderr}`]);
            if (result.error) setShellOutput(prev => [...prev, `System Error: ${result.error}`]);
            setCommand('');
        } catch (error) {
            setShellOutput(prev => [...prev, 'Failed to reach backend diagnostic bridge.']);
        } finally {
            setExecuting(false);
        }
    };

    useEffect(() => {
        const init = async () => {
            setLoading(true);
            await Promise.all([fetchStack(), fetchLogs()]);
            setLoading(false);
        };
        init();

        const interval = setInterval(() => {
            fetchStack();
            fetchLogs();
        }, 5000);

        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    useEffect(() => {
        shellEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [shellOutput]);

    if (loading && !stack) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="flex flex-col items-center gap-4">
                    <RefreshCw className="w-12 h-12 text-blue-500 animate-spin" />
                    <p className="text-gray-400 font-medium font-mono">Initializing Boomy Insight Bridge...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                        <Shield className="w-8 h-8 text-blue-500" />
                        Diagnostics
                    </h1>
                    <p className="text-gray-400 mt-1">Hardware-level telemetry and remote recovery tools</p>
                </div>
                <div className="flex gap-3">
                    <button 
                        onClick={() => { fetchStack(); fetchLogs(); }}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors border border-gray-700"
                    >
                        <RefreshCw className="w-4 h-4" />
                        Refresh
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column: Health & Stack */}
                <div className="space-y-6">
                    {/* System Health */}
                    <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-gray-800 flex items-center gap-2 bg-gray-800/30">
                            <Activity className="w-5 h-5 text-green-500" />
                            <h2 className="font-semibold text-white">System Health</h2>
                        </div>
                        <div className="p-4 space-y-4">
                            <div className="flex items-center justify-between p-3 bg-black/30 rounded-lg border border-gray-800">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-full ${stack?.i2c_bus_state === 'active' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                                        <Zap className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-400">I2C Control Bus</p>
                                        <p className="font-mono font-medium text-white uppercase">{stack?.i2c_bus_state || 'unknown'}</p>
                                    </div>
                                </div>
                                {stack?.i2c_bus_state === 'active' ? (
                                    <CheckCircle2 className="w-5 h-5 text-green-500" />
                                ) : (
                                    <AlertCircle className="w-5 h-5 text-red-500" />
                                )}
                            </div>

                            <div className="flex items-center justify-between p-3 bg-black/30 rounded-lg border border-gray-800">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-full bg-blue-500/10 text-blue-500">
                                        <Wifi className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-400">Network Interface</p>
                                        <p className="font-mono font-medium text-white">Ethernet (Cabled)</p>
                                    </div>
                                </div>
                                <div className="px-2 py-1 bg-blue-500/10 text-blue-500 text-xs rounded border border-blue-500/20">
                                    STABLE
                                </div>
                            </div>

                            <div className="flex items-center justify-between p-3 bg-black/30 rounded-lg border border-gray-800">
                                <div className="flex items-center gap-3">
                                    <div className="p-2 rounded-full bg-purple-500/10 text-purple-500">
                                        <Cpu className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-400">Host Hardware</p>
                                        <p className="font-mono font-medium text-white">Raspberry Pi 5</p>
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center justify-between p-3 bg-black/30 rounded-lg border border-gray-800">
                                <div className="flex items-center gap-3">
                                    <div className={`p-2 rounded-full ${stack?.voice_module_state === 'active' ? 'bg-indigo-500/10 text-indigo-500' : 'bg-gray-500/10 text-gray-500'}`}>
                                        <Mic className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-400">AI Voice Module</p>
                                        <p className="font-mono font-medium text-white uppercase">{stack?.voice_module_state || 'unknown'}</p>
                                    </div>
                                </div>
                                {stack?.voice_module_state === 'active' ? (
                                    <CheckCircle2 className="w-5 h-5 text-indigo-500" />
                                ) : (
                                    <AlertCircle className="w-5 h-5 text-gray-500" />
                                )}
                            </div>
                        </div>
                    </div>

                    {/* Live Vision Card */}
                    <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-800/30">
                            <div className="flex items-center gap-2">
                                <Camera className="w-5 h-5 text-blue-500" />
                                <h2 className="font-semibold text-white">Live Vision</h2>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                                <span className="text-[10px] font-bold text-red-500 uppercase tracking-wider">Live</span>
                            </div>
                        </div>
                        <div className="aspect-video bg-black relative flex items-center justify-center group">
                            {/* MJPEG Stream from Backend */}
                            <img 
                                src="/api/v1/snapshot" /* Default to snapshot first, then stream once confirmed */
                                alt="Robot Vision"
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                    (e.target as HTMLImageElement).src = 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&q=80&w=800';
                                }}
                            />
                            {/* Overlay for "Open Full Stream" or similar if needed */}
                            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4">
                                <a 
                                    href="/stream" 
                                    target="_blank" 
                                    rel="noreferrer"
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-sm font-medium transition-colors"
                                >
                                    Open Direct Stream
                                </a>
                            </div>
                        </div>
                        <div className="p-3 bg-black/40 border-t border-gray-800 flex items-center justify-between">
                            <span className="text-xs text-gray-500 font-mono">USB PTZ / CSI Camera</span>
                            <span className="text-[10px] text-blue-400 font-mono">15 FPS / MJPEG</span>
                        </div>
                    </div>

                    {/* ROS Nodes */}
                    <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden">
                        <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-800/30">
                            <div className="flex items-center gap-2">
                                <Search className="w-5 h-5 text-blue-500" />
                                <h2 className="font-semibold text-white">Active Nodes</h2>
                            </div>
                            <span className="text-xs font-mono text-gray-500 bg-black/40 px-2 py-1 rounded">
                                ROS 2 HUMBLE
                            </span>
                        </div>
                        <div className="p-2 max-h-[300px] overflow-y-auto custom-scrollbar">
                            {stack?.ros_nodes && stack.ros_nodes.length > 0 ? (
                                <ul className="space-y-1">
                                    {stack.ros_nodes.map((node, i) => (
                                        <li key={i} className="flex items-center gap-3 p-2 hover:bg-white/5 rounded-lg transition-colors group">
                                            <ChevronRight className="w-4 h-4 text-gray-600 group-hover:text-blue-500" />
                                            <span className="font-mono text-sm text-gray-300">{node}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <div className="p-8 text-center">
                                    <AlertCircle className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                                    <p className="text-gray-500 italic text-sm">No ROS nodes detected</p>
                                    <p className="text-xs text-gray-700 mt-1">Check yahboom_base.service</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Right Column: Logs & Shell */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Kernel Logs */}
                    <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden flex flex-col h-[400px]">
                        <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-800/30">
                            <div className="flex items-center gap-2">
                                <Activity className="w-5 h-5 text-orange-500" />
                                <h2 className="font-semibold text-white">Kernel Logs (dmesg)</h2>
                            </div>
                            <button 
                                onClick={() => setLogs([])}
                                className="text-xs text-gray-500 hover:text-white transition-colors"
                            >
                                Clear View
                            </button>
                        </div>
                        <div className="flex-1 p-4 font-mono text-xs overflow-y-auto bg-black/40 custom-scrollbar">
                            {logs.map((log, i) => {
                                const isI2CError = log.toLowerCase().includes('i2c') || log.toLowerCase().includes('timeout');
                                return (
                                    <div key={i} className={`py-0.5 ${isI2CError ? 'text-red-400 bg-red-500/5 px-2 -mx-2 rounded' : 'text-gray-400'}`}>
                                        <span className="text-gray-600 mr-2 select-none">[{i+1}]</span>
                                        {log}
                                    </div>
                                );
                            })}
                            <div ref={logEndRef} />
                        </div>
                    </div>

                    {/* Remote Shell */}
                    <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden flex flex-col h-[400px]">
                        <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-800/30">
                            <div className="flex items-center gap-2">
                                <TerminalIcon className="w-5 h-5 text-blue-500" />
                                <h2 className="font-semibold text-white">Remote Diagnostic Shell</h2>
                            </div>
                            <div className="flex items-center gap-4">
                                <div className="text-[10px] font-mono text-gray-500">
                                    PI@BOOMY: SSH-OVER-BRIDGE
                                </div>
                                <button 
                                    onClick={() => setShellOutput([])}
                                    className="text-xs text-gray-500 hover:text-white transition-colors"
                                >
                                    Clear
                                </button>
                            </div>
                        </div>
                        <div className="flex-1 p-4 font-mono text-xs overflow-y-auto bg-black/60 custom-scrollbar text-green-400">
                            {shellOutput.length === 0 && (
                                <p className="text-gray-600 italic">Bridge initialized. Enter command to execute on Boomy...</p>
                            )}
                            {shellOutput.map((line, i) => (
                                <div key={i} className="whitespace-pre-wrap leading-relaxed py-0.5">
                                    {line}
                                </div>
                            ))}
                            {executing && (
                                <div className="flex items-center gap-2 text-blue-400 animate-pulse mt-1">
                                    <RefreshCw className="w-3 h-3 animate-spin" />
                                    Executing...
                                </div>
                            )}
                            <div ref={shellEndRef} />
                        </div>
                        <form onSubmit={handleExecute} className="p-4 bg-gray-900 border-t border-gray-800 flex items-center gap-2">
                            <span className="text-blue-500 font-mono font-bold font-sm">$</span>
                            <input 
                                type="text"
                                value={command}
                                onChange={(e) => setCommand(e.target.value)}
                                placeholder="e.g. i2cdetect -y 1"
                                className="flex-1 bg-transparent border-none text-white font-mono text-sm focus:ring-0 placeholder:text-gray-700"
                                disabled={executing}
                            />
                            <button 
                                type="submit"
                                disabled={!command.trim() || executing}
                                className="p-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 text-white rounded-lg transition-colors"
                            >
                                {executing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                            </button>
                        </form>
                    </div>
                </div>
            </div>

            {/* Warning/Info Footer */}
            <div className="p-4 bg-blue-500/5 border border-blue-500/20 rounded-xl flex items-start gap-4">
                <div className="p-2 bg-blue-500/10 rounded-lg">
                    <AlertCircle className="w-6 h-6 text-blue-500" />
                </div>
                <div>
                    <h3 className="text-sm font-semibold text-white">Diagnostic Insights</h3>
                    <p className="text-xs text-gray-400 mt-1 leading-relaxed">
                        Currently monitoring Boomy via Ethernet bridge at <code className="text-blue-400">192.168.0.250</code>. 
                        If I2C timeouts persist after power-cycling, use the diagnostic shell to check <code className="text-gray-300">i2cdetect -y 1</code>.
                        The baudrate patch (100kHz) requires the Pi 5 to reboot to apply kernel-level DTBO changes.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default Diagnostics;
