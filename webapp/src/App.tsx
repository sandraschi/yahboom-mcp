import { useState } from 'react'
import { Activity, Battery, Compass, Play, Square, Settings } from 'lucide-react'

function App() {
    return (
        <div className="min-h-screen bg-[#0a0a0a] text-white p-8 font-sans">
            <header className="flex justify-between items-center mb-12">
                <div>
                    <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-blue-500 to-purple-600 bg-clip-text text-transparent">
                        Yahboom ROS 2
                    </h1>
                    <p className="text-gray-400 mt-2 text-lg">Mission Control & Telemetry</p>
                </div>
                <div className="flex gap-4">
                    <div className="px-4 py-2 bg-[#1a1a1a] rounded-full border border-white/10 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
                        <span className="text-sm font-medium">MCP Connected</span>
                    </div>
                </div>
            </header>

            <main className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Telemetry Cards */}
                <div className="p-6 bg-[#111] rounded-2xl border border-white/5 hover:border-blue-500/30 transition-all group">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
                            <Battery size={24} />
                        </div>
                        <span className="text-2xl font-bold">85%</span>
                    </div>
                    <h3 className="text-gray-400 font-medium">Battery Level</h3>
                    <div className="mt-4 w-full bg-white/5 h-2 rounded-full overflow-hidden">
                        <div className="bg-blue-500 h-full w-[85%]"></div>
                    </div>
                </div>

                <div className="p-6 bg-[#111] rounded-2xl border border-white/5 hover:border-purple-500/30 transition-all group">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-purple-500/10 rounded-xl text-purple-500">
                            <Compass size={24} />
                        </div>
                        <span className="text-2xl font-bold">342°</span>
                    </div>
                    <h3 className="text-gray-400 font-medium">IMU Heading</h3>
                </div>

                <div className="p-6 bg-[#111] rounded-2xl border border-white/5 hover:border-green-500/30 transition-all group">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-green-500/10 rounded-xl text-green-500">
                            <Activity size={24} />
                        </div>
                        <span className="text-2xl font-bold">0.5 m/s</span>
                    </div>
                    <h3 className="text-gray-400 font-medium">Current Velocity</h3>
                </div>

                {/* Video Feed Panel */}
                <div className="md:col-span-2 p-8 bg-[#111] rounded-2xl border border-white/5 overflow-hidden">
                    <div className="flex justify-between items-center mb-6">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <Activity size={20} className="text-blue-500" /> Live Vision Feed
                        </h2>
                        <div className="flex gap-2">
                            <span className="px-3 py-1 bg-green-500/10 text-green-500 text-xs font-bold rounded-full border border-green-500/20">
                                LIVE
                            </span>
                        </div>
                    </div>
                    <div className="aspect-video bg-black rounded-xl overflow-hidden border border-white/5 relative group">
                        <img
                            src="http://localhost:10792/stream"
                            className="w-full h-full object-cover"
                            alt="Robot View"
                            onError={(e) => {
                                e.currentTarget.src = "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&q=80&w=1200";
                                e.currentTarget.className = "w-full h-full object-cover opacity-20 grayscale";
                            }}
                        />
                        <div className="absolute top-4 left-4 p-2 bg-black/60 backdrop-blur-md rounded-lg text-[10px] font-mono text-white/70">
                            STREAM_ID: YH_G1_001 <br />
                            LATENCY: 42ms
                        </div>
                    </div>
                </div>

                {/* Trajectory & System Panel */}
                <div className="p-8 bg-[#111] rounded-2xl border border-white/5">
                    <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                        <Compass size={20} /> Path Recording
                    </h2>
                    <div className="space-y-4">
                        <button className="w-full py-4 bg-red-600/10 text-red-500 border border-red-500/20 rounded-xl font-bold hover:bg-red-600 hover:text-white transition-all flex items-center justify-center gap-2 group">
                            <div className="w-3 h-3 rounded-full bg-red-500 group-hover:scale-125 transition-all animate-pulse" />
                            Start Recording
                        </button>
                        <button className="w-full py-4 bg-white/5 text-gray-400 rounded-xl font-bold hover:bg-white/10 transition-all">
                            Save Current Trajectory
                        </button>
                        <div className="pt-4 border-t border-white/5">
                            <h4 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Saved Paths</h4>
                            <div className="space-y-2">
                                {['patrol_A.json', 'exploration_1.json'].map(path => (
                                    <div key={path} className="p-3 bg-white/5 rounded-lg text-sm flex justify-between items-center hover:bg-blue-500/10 transition-all cursor-pointer group">
                                        <span className="text-gray-300">{path}</span>
                                        <Play size={14} className="text-gray-500 group-hover:text-blue-500" />
                                    </div>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Control Panel (Re-positioned) */}
                <div className="md:col-span-2 p-8 bg-[#111] rounded-2xl border border-white/5">
                    <div className="flex justify-between items-center mb-8">
                        <h2 className="text-xl font-bold">Motion Control</h2>
                        <div className="flex gap-2">
                            <button className="px-4 py-2 bg-red-500/10 text-red-500 rounded-lg border border-red-500/20 hover:bg-red-500 hover:text-white transition-all flex items-center gap-2">
                                <Square size={18} /> Emergency Stop
                            </button>
                        </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 max-w-xs mx-auto">
                        <div />
                        <button className="aspect-square bg-[#1a1a1a] rounded-xl flex items-center justify-center hover:bg-blue-500/20 transition-all border border-white/5">
                            <Play size={24} className="-rotate-90" />
                        </button>
                        <div />
                        <button className="aspect-square bg-[#1a1a1a] rounded-xl flex items-center justify-center hover:bg-blue-500/20 transition-all border border-white/5">
                            <Play size={24} className="rotate-180" />
                        </button>
                        <button className="aspect-square bg-white/5 rounded-xl flex items-center justify-center">
                            <div className="w-2 h-2 rounded-full bg-white/20" />
                        </button>
                        <button className="aspect-square bg-[#1a1a1a] rounded-xl flex items-center justify-center hover:bg-blue-500/20 transition-all border border-white/5">
                            <Play size={24} />
                        </button>
                        <div />
                        <button className="aspect-square bg-[#1a1a1a] rounded-xl flex items-center justify-center hover:bg-blue-500/20 transition-all border border-white/5">
                            <Play size={24} className="rotate-90" />
                        </button>
                        <div />
                    </div>
                </div>

                {/* System Settings */}
                <div className="p-8 bg-[#111] rounded-2xl border border-white/5">
                    <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                        <Settings size={20} /> Parameters
                    </h2>
                    <div className="space-y-6">
                        <div>
                            <label className="text-sm text-gray-400 block mb-2">Max Linear Speed (m/s)</label>
                            <input type="range" className="w-full accent-blue-500" />
                        </div>
                        <div>
                            <label className="text-sm text-gray-400 block mb-2">Angular Turn Rate</label>
                            <input type="range" className="w-full accent-purple-500" />
                        </div>
                        <button className="w-full py-3 bg-blue-600 rounded-xl font-bold hover:bg-blue-700 transition-all">
                            Apply Changes
                        </button>
                    </div>
                </div>
            </main>
        </div>
    )
}

export default App
