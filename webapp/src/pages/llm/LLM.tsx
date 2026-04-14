import { Activity as ActivityIcon, Cpu, Database, Shield, Thermometer, Zap } from "lucide-react";
import type React from "react";

const LLM: React.FC = () => {
  return (
    <div className="space-y-8 py-4 px-4 sm:px-6">
      <div className="flex items-center gap-4">
        <Cpu className="text-indigo-400 w-8 h-8" />
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Local Intelligence</h1>
          <p className="text-slate-400 text-sm">RTX 4090 Hardware-accelerated LLM orchestration.</p>
        </div>
      </div>

      <div className="bg-[#0f0f12]/80 border border-white/5 rounded-3xl p-8 lg:p-12 shadow-2xl relative overflow-hidden backdrop-blur-xl">
        <div className="flex flex-col lg:flex-row gap-12 items-center">
          <div className="flex-1 space-y-8 relative z-10 text-center lg:text-left">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 text-[10px] font-bold uppercase tracking-widest border border-indigo-500/20 mb-4">
                <Zap size={10} /> GPU Opportunity Detected
              </div>
              <h2 className="text-2xl lg:text-3xl font-bold text-white leading-tight mb-4">
                RTX 4090 Optimization Active
              </h2>
              <p className="text-slate-400 text-sm lg:text-base leading-relaxed font-medium">
                Your high-end GPU is recognized. We have automatically initialized mixed-precision
                quantization (FP16) with Flash Attention for sub-10ms response times on local
                directives.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {[
                { icon: Thermometer, label: "Temp", value: "54°C", color: "text-orange-400" },
                { icon: Database, label: "VRAM", value: "2.4 / 24 GB", color: "text-indigo-400" },
                { icon: Shield, label: "Model", value: "Mistral 7B", color: "text-green-400" },
                { icon: ActivityIcon, label: "Latency", value: "4ms", color: "text-yellow-400" },
              ].map((stat, i) => (
                <div
                  key={i}
                  className="flex items-center gap-4 p-4 rounded-2xl bg-white/5 border border-white/5"
                >
                  <stat.icon className={`${stat.color} w-5 h-5 flex-shrink-0`} />
                  <div>
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block">
                      {stat.label}
                    </span>
                    <span className="text-sm font-bold text-slate-200">{stat.value}</span>
                  </div>
                </div>
              ))}
            </div>

            <button className="w-full lg:w-auto px-10 py-4 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-2xl transition-all shadow-lg shadow-indigo-600/20">
              Manage Local Inference Grid
            </button>
          </div>

          <div className="w-full lg:w-1/3 flex justify-center relative">
            <div className="w-64 h-64 rounded-3xl bg-indigo-600/10 border border-indigo-500/20 relative flex items-center justify-center group overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/10 via-transparent to-purple-500/10" />
              <Cpu
                size={100}
                className="text-indigo-500/40 group-hover:scale-110 transition-transform duration-700"
              />
              <div className="absolute inset-0 border-2 border-indigo-500 animate-[ping_3s_cubic-bezier(0,0,0.2,1)_infinite] opacity-10 rounded-3xl" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LLM;
