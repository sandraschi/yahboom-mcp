import React from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Globe, Shield, Bell, Save } from 'lucide-react';

const Settings: React.FC = () => {
    return (
        <div className="space-y-8 py-4 px-4 sm:px-6 max-w-4xl mx-auto">
            <div className="flex items-center gap-4">
                <SettingsIcon className="text-indigo-400 w-8 h-8" />
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">System Settings</h1>
                    <p className="text-slate-400 text-sm">Configure Mission Control parameters and security protocols.</p>
                </div>
            </div>

            <div className="space-y-6">
                {[
                    { icon: Globe, label: 'Gateway Config', desc: 'Manage SSE transport and API endpoints.' },
                    { icon: Shield, label: 'Security & Auth', desc: 'Link encryption and hardware binding keys.' },
                    { icon: Bell, label: 'Notifications', desc: 'Hardware event alerts and telemetry thresholds.' }
                ].map((section, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.1 }}
                        className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 lg:p-8 backdrop-blur-xl shadow-xl flex items-center justify-between group hover:border-indigo-500/20 transition-all cursor-pointer"
                    >
                        <div className="flex items-center gap-6">
                            <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/10">
                                <section.icon className="text-indigo-400 w-6 h-6" />
                            </div>
                            <div>
                                <h3 className="text-lg font-bold text-white leading-tight mb-1">{section.label}</h3>
                                <p className="text-slate-500 text-sm font-medium">{section.desc}</p>
                            </div>
                        </div>
                        <div className="w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center text-slate-500 group-hover:text-indigo-400 transition-colors">
                            <Save size={18} />
                        </div>
                    </motion.div>
                ))}
            </div>
        </div>
    );
};

export default Settings;
