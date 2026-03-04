import React from 'react';
import { motion } from 'framer-motion';
import { HelpCircle, Book, Terminal, MessageCircle, FileText } from 'lucide-react';

const Help: React.FC = () => {
    return (
        <div className="space-y-8 py-4 px-4 sm:px-6 max-w-5xl mx-auto">
            <div className="flex items-center gap-4">
                <HelpCircle className="text-indigo-400 w-8 h-8" />
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Mission Support</h1>
                    <p className="text-slate-400 text-sm">Documentation, troubleshooting, and hardware protocols.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="space-y-6">
                    <h2 className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1">Knowledge Base</h2>
                    {[
                        { icon: Book, label: 'G1 User Manual', desc: 'Official Yahboom G1 operating procedures.' },
                        { icon: Terminal, label: 'ROS 2 CLI Guide', desc: 'Command line interface for advanced debug.' },
                        { icon: FileText, label: 'Hardware Specs', desc: 'Mecanum wheel kinematics and motor data.' }
                    ].map((item, idx) => (
                        <div key={idx} className="bg-[#0f0f12]/60 border border-white/5 p-5 rounded-2xl flex items-center gap-4 hover:bg-white/5 transition-colors cursor-pointer group">
                            <item.icon className="text-indigo-400 w-5 h-5 group-hover:scale-110 transition-transform" />
                            <div>
                                <h4 className="text-sm font-bold text-slate-200">{item.label}</h4>
                                <p className="text-[11px] text-slate-500 font-medium">{item.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>

                <div className="bg-indigo-600 border border-indigo-500 rounded-[40px] p-10 flex flex-col justify-between shadow-2xl shadow-indigo-600/30 relative overflow-hidden">
                    <div className="absolute top-0 right-0 p-10 opacity-10"><MessageCircle size={150} /></div>
                    <div className="relative z-10">
                        <h2 className="text-2xl font-bold text-white mb-4">Request Support</h2>
                        <p className="text-indigo-100/80 text-sm font-medium leading-relaxed mb-8">
                            Encountered a hardware anomaly? Our technical team and AI diagnostics are 24/7.
                        </p>
                        <button className="px-8 py-3 bg-white text-indigo-600 rounded-xl text-xs font-bold uppercase tracking-widest">Open Ticket</button>
                    </div>
                    <div className="mt-12 flex items-center gap-3">
                        <div className="flex -space-x-2">
                            {[1, 2, 3].map(i => <div key={i} className="w-8 h-8 rounded-full border-2 border-indigo-600 bg-slate-800" />)}
                        </div>
                        <span className="text-[10px] font-bold text-indigo-100/60 uppercase tracking-widest">4 Engineers Online</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Help;
