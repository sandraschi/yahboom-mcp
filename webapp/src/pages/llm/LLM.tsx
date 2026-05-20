import { motion } from "framer-motion";
import {
	Activity as ActivityIcon,
	CheckCircle2,
	Cpu,
	Database,
	Loader2,
	Thermometer,
	Unplug,
	Zap,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

interface GpuStatus {
	detected: boolean;
	gpu_name?: string | null;
	vram_total_gb?: number | null;
	vram_used_gb?: number | null;
	temp_c?: number | null;
	utilization_pct?: number | null;
}

interface LlmInfo {
	provider: string;
	model: string;
	ollama_connected: boolean;
	lmstudio_connected: boolean;
}

async function fetchJson<T>(url: string): Promise<T | null> {
	try {
		const res = await fetch(url);
		if (!res.ok) return null;
		return res.json() as Promise<T>;
	} catch {
		return null;
	}
}

const LLM: React.FC = () => {
	const [gpu, setGpu] = useState<GpuStatus | null>(null);
	const [llm, setLlm] = useState<LlmInfo | null>(null);
	const [loading, setLoading] = useState(true);

	const load = useCallback(async () => {
		setLoading(true);
		const [gpuData, llmSettings, ollamaStatus, lmstudioStatus] =
			await Promise.all([
				fetchJson<GpuStatus>("/api/v1/settings/gpu"),
				fetchJson<{ provider: string; model: string }>("/api/v1/settings/llm"),
				fetchJson<{ connected: boolean }>("/api/v1/settings/ollama/status"),
				fetchJson<{ connected: boolean }>("/api/v1/settings/lmstudio/status"),
			]);
		setGpu(gpuData);
		setLlm({
			provider: llmSettings?.provider || "ollama",
			model: llmSettings?.model || "(none)",
			ollama_connected: ollamaStatus?.connected ?? false,
			lmstudio_connected: lmstudioStatus?.connected ?? false,
		});
		setLoading(false);
	}, []);

	useEffect(() => {
		load();
	}, [load]);

	const anyProvider = llm && (llm.ollama_connected || llm.lmstudio_connected);

	return (
		<div className="space-y-8 py-4 px-4 sm:px-6">
			<div className="flex items-center gap-4">
				<Cpu className="text-indigo-400 w-8 h-8" />
				<div>
					<h1 className="text-3xl font-bold text-white tracking-tight">
						Local Intelligence
					</h1>
					<p className="text-slate-400 text-sm">
						GPU-accelerated LLM orchestration.
					</p>
				</div>
			</div>

			{/* GPU Status Card */}
			<motion.div
				initial={{ opacity: 0, y: 8 }}
				animate={{ opacity: 1, y: 0 }}
				className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 lg:p-12 shadow-2xl relative overflow-hidden backdrop-blur-xl"
			>
				<div className="flex flex-col lg:flex-row gap-12 items-center">
					<div className="flex-1 space-y-8 relative z-10 text-center lg:text-left">
						{gpu?.detected ? (
							<>
								<div>
									<div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold uppercase tracking-widest border border-indigo-500/20 mb-4">
										<Zap size={10} /> GPU Detected
									</div>
									<h2 className="text-2xl lg:text-3xl font-bold text-white leading-tight mb-4">
										{gpu.gpu_name || "NVIDIA GPU"}
									</h2>
								</div>
								<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
									{[
										{
											icon: Thermometer,
											label: "Temp",
											value: gpu.temp_c != null ? `${gpu.temp_c}°C` : "--",
											color: "text-orange-400",
										},
										{
											icon: Database,
											label: "VRAM",
											value:
												gpu.vram_used_gb != null && gpu.vram_total_gb != null
													? `${gpu.vram_used_gb} / ${gpu.vram_total_gb} GB`
													: "--",
											color: "text-indigo-400",
										},
										{
											icon: CheckCircle2,
											label: "Provider",
											value: llm
												? anyProvider
													? "Connected"
													: "Offline"
												: "--",
											color: anyProvider ? "text-green-400" : "text-red-400",
										},
										{
											icon: ActivityIcon,
											label: "Utilization",
											value:
												gpu.utilization_pct != null
													? `${gpu.utilization_pct}%`
													: "--",
											color: "text-yellow-400",
										},
									].map((stat) => (
										<div
											key={stat.label}
											className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5"
										>
											<stat.icon
												className={`${stat.color} w-5 h-5 flex-shrink-0`}
											/>
											<div>
												<span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">
													{stat.label}
												</span>
												<span className="text-sm font-bold text-slate-200">
													{stat.value}
												</span>
											</div>
										</div>
									))}
								</div>
							</>
						) : loading ? (
							<div className="flex items-center gap-3 text-slate-400">
								<Loader2 className="w-5 h-5 animate-spin" />
								<span>Probing GPU and LLM providers...</span>
							</div>
						) : (
							<div>
								<div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 text-amber-400 text-[10px] font-bold uppercase tracking-widest border border-amber-500/20 mb-4">
									<Unplug size={10} /> No GPU Found
								</div>
								<h2 className="text-2xl lg:text-3xl font-bold text-white leading-tight mb-4">
									GPU not detected
								</h2>
								<p className="text-slate-400 text-sm lg:text-base leading-relaxed font-medium">
									nvidia-smi did not report a GPU. LLM inference runs on CPU via
									Ollama or LM Studio. For GPU acceleration, ensure NVIDIA
									drivers are installed and the GPU is available.
								</p>
							</div>
						)}

						<div className="flex flex-wrap gap-3">
							<Link
								to="/settings"
								className="w-full lg:w-auto px-8 py-3 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-2xl transition-all shadow-lg shadow-indigo-600/20 text-sm text-center"
							>
								LLM Settings
							</Link>
							<Link
								to="/chat"
								className="w-full lg:w-auto px-8 py-3 bg-white/5 border border-white/10 hover:bg-white/10 text-slate-300 font-bold rounded-2xl transition-all text-sm text-center"
							>
								Open Chat
							</Link>
						</div>
					</div>

					<div className="w-full lg:w-1/3 flex justify-center relative">
						<div className="w-64 h-64 rounded-3xl bg-indigo-600/10 border border-indigo-500/20 relative flex items-center justify-center group overflow-hidden">
							<div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/10" />
							<Cpu
								size={100}
								className="text-indigo-500/40 group-hover:scale-110 transition-transform duration-700"
							/>
							{gpu?.detected && (
								<div className="absolute inset-0 border-2 border-indigo-500 animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite] opacity-10 rounded-3xl" />
							)}
						</div>
					</div>
				</div>
			</motion.div>

			{/* Provider status summary */}
			{llm && (
				<div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
					<div className="bg-[#0f0f12]/80 border border-white/5 rounded-2xl p-5 backdrop-blur-xl">
						<div className="flex items-center justify-between">
							<div className="flex items-center gap-3">
								{llm.ollama_connected ? (
									<CheckCircle2 className="w-5 h-5 text-emerald-400" />
								) : (
									<Unplug className="w-5 h-5 text-slate-500" />
								)}
								<div>
									<span className="text-sm font-bold text-white">Ollama</span>
									<p className="text-[10px] text-slate-500">localhost:11434</p>
								</div>
							</div>
							<span
								className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
									llm.ollama_connected
										? "bg-emerald-500/20 text-emerald-400"
										: "bg-slate-700/50 text-slate-500"
								}`}
							>
								{llm.ollama_connected ? "Online" : "Offline"}
							</span>
						</div>
					</div>
					<div className="bg-[#0f0f12]/80 border border-white/5 rounded-2xl p-5 backdrop-blur-xl">
						<div className="flex items-center justify-between">
							<div className="flex items-center gap-3">
								{llm.lmstudio_connected ? (
									<CheckCircle2 className="w-5 h-5 text-emerald-400" />
								) : (
									<Unplug className="w-5 h-5 text-slate-500" />
								)}
								<div>
									<span className="text-sm font-bold text-white">
										LM Studio
									</span>
									<p className="text-[10px] text-slate-500">localhost:1234</p>
								</div>
							</div>
							<span
								className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
									llm.lmstudio_connected
										? "bg-emerald-500/20 text-emerald-400"
										: "bg-slate-700/50 text-slate-500"
								}`}
							>
								{llm.lmstudio_connected ? "Online" : "Offline"}
							</span>
						</div>
					</div>
				</div>
			)}
		</div>
	);
};

export default LLM;
