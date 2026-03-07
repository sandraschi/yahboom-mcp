import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Settings as SettingsIcon, Globe, Shield, Bell, Save, Cpu, RefreshCw, Loader2 } from 'lucide-react';
import { api, type OllamaStatus, type OllamaModel, type LLMSettings } from '../../lib/api';

const Settings: React.FC = () => {
    const [ollamaStatus, setOllamaStatus] = useState<OllamaStatus | null>(null);
    const [models, setModels] = useState<OllamaModel[]>([]);
    const [llmSettings, setLlmSettings] = useState<LLMSettings | null>(null);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const load = useCallback(async () => {
        setError(null);
        setLoading(true);
        try {
            const [status, modelsRes, llm] = await Promise.all([
                api.getOllamaStatus(),
                api.getOllamaModels(),
                api.getLlmSettings(),
            ]);
            setOllamaStatus(status);
            setModels(modelsRes.models || []);
            setLlmSettings(llm);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to load settings');
            setOllamaStatus(null);
            setModels([]);
            setLlmSettings(null);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        load();
    }, [load]);

    const handleModelChange = async (model: string) => {
        if (!llmSettings) return;
        setSaving(true);
        setError(null);
        try {
            const updated = await api.putLlmSettings(model);
            setLlmSettings(updated);
        } catch (e) {
            setError(e instanceof Error ? e.message : 'Failed to save model');
        } finally {
            setSaving(false);
        }
    };

    return (
        <div className="space-y-8 py-4 px-4 sm:px-6 max-w-4xl mx-auto">
            <div className="flex items-center gap-4">
                <SettingsIcon className="text-indigo-400 w-8 h-8" />
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">System Settings</h1>
                    <p className="text-slate-400 text-sm">Configure Mission Control parameters and local LLM (Ollama).</p>
                </div>
            </div>

            {error && (
                <div className="bg-red-500/10 border border-red-500/20 rounded-2xl px-4 py-3 text-red-400 text-sm">
                    {error}
                </div>
            )}

            {/* Ollama / LLM */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-6 lg:p-8 backdrop-blur-xl shadow-xl"
            >
                <div className="flex items-center gap-6 mb-6">
                    <div className="w-12 h-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center border border-indigo-500/10">
                        <Cpu className="text-indigo-400 w-6 h-6" />
                    </div>
                    <div className="flex-1">
                        <h3 className="text-lg font-bold text-white leading-tight mb-1">Local LLM (Ollama)</h3>
                        <p className="text-slate-500 text-sm">Model discovery and selection for the Chat page.</p>
                    </div>
                    <button
                        type="button"
                        onClick={load}
                        disabled={loading}
                        className="p-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                        title="Refresh"
                    >
                        {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <RefreshCw className="w-5 h-5" />}
                    </button>
                </div>
                {loading && !ollamaStatus ? (
                    <div className="flex items-center gap-2 text-slate-500 text-sm">
                        <Loader2 className="w-4 h-4 animate-spin" /> Loading…
                    </div>
                ) : (
                    <div className="space-y-4">
                        <div className="flex items-center gap-2">
                            <span className="text-slate-400 text-sm">Status:</span>
                            <span
                                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                                    ollamaStatus?.connected ? 'bg-emerald-500/20 text-emerald-400' : 'bg-amber-500/20 text-amber-400'
                                }`}
                            >
                                {ollamaStatus?.connected ? 'Connected' : 'Unreachable'}
                            </span>
                            {ollamaStatus?.base_url && (
                                <span className="text-slate-500 text-xs">{ollamaStatus.base_url}</span>
                            )}
                        </div>
                        <div>
                            <label className="block text-slate-400 text-sm mb-2">Model</label>
                            <select
                                value={llmSettings?.model ?? ''}
                                onChange={(e) => handleModelChange(e.target.value)}
                                disabled={saving || !ollamaStatus?.connected}
                                className="w-full max-w-md bg-slate-800 border border-white/10 rounded-xl px-4 py-2.5 text-slate-100 text-sm focus:outline-none focus:border-indigo-500/50 disabled:opacity-50 [color-scheme:dark]"
                            >
                                <option value="">Select a model</option>
                                {models.map((m) => (
                                    <option key={m.name} value={m.name} className="bg-slate-800 text-slate-100">
                                        {m.name}
                                    </option>
                                ))}
                            </select>
                            {saving && (
                                <span className="ml-2 text-slate-500 text-xs inline-flex items-center gap-1">
                                    <Loader2 className="w-3 h-3 animate-spin" /> Saving…
                                </span>
                            )}
                        </div>
                    </div>
                )}
            </motion.div>

            {/* Placeholder sections */}
            <div className="space-y-6">
                {[
                    { icon: Globe, label: 'Gateway Config', desc: 'Manage SSE transport and API endpoints.' },
                    { icon: Shield, label: 'Security & Auth', desc: 'Link encryption and hardware binding keys.' },
                    { icon: Bell, label: 'Notifications', desc: 'Hardware event alerts and telemetry thresholds.' },
                ].map((section, idx) => (
                    <motion.div
                        key={idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: (idx + 1) * 0.1 }}
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
