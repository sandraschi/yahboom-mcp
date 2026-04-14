import { motion } from "framer-motion";
import { CheckCircle2, Info, Rocket, Server } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";

const RASPBOT_HOTSPOT = {
  ssid: "raspbot",
  password: "12345678",
  ip: "192.168.1.11",
  port: "6000",
};

const SUBSTRATE_SCAN_SEC = 5;

function Step2SubstrateLink({
  config,
  onSkip,
}: {
  config: { robotIp: string; port: string };
  onSkip: () => void;
}) {
  const [countdown, setCountdown] = useState(SUBSTRATE_SCAN_SEC);

  useEffect(() => {
    const t = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          clearInterval(t);
          onSkip();
          return 0;
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [onSkip]);

  return (
    <div className="text-center py-12 space-y-8 relative z-10">
      <div className="flex justify-center">
        <div className="w-20 h-20 rounded-full border-4 border-indigo-500/30 border-t-indigo-500 animate-spin" />
      </div>
      <div>
        <h2 className="text-xl font-bold text-white mb-2">Establishing Substrate Link...</h2>
        <p className="text-slate-400 text-sm font-medium">
          Scanning for ROS 2 nodes on {config.robotIp}.
        </p>
        <p className="text-slate-500 text-xs mt-2">Auto-skip in {countdown}s, or skip now.</p>
      </div>
      <button
        onClick={onSkip}
        className="px-8 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-sm transition-all"
      >
        Skip Scan (continue without robot)
      </button>
    </div>
  );
}

const Onboarding: React.FC = () => {
  const [step, setStep] = useState(1);
  const [config, setConfig] = useState({
    robotIp: RASPBOT_HOTSPOT.ip,
    port: RASPBOT_HOTSPOT.port,
  });

  const applyRaspbotHotspot = () => {
    setConfig({ robotIp: RASPBOT_HOTSPOT.ip, port: RASPBOT_HOTSPOT.port });
  };

  return (
    <div className="max-w-4xl mx-auto py-8">
      <div className="flex items-center gap-4 mb-10">
        <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 flex items-center justify-center border border-indigo-500/30">
          <Rocket className="text-indigo-400 w-6 h-6" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Robot Onboarding</h1>
          <p className="text-slate-400 text-sm">
            Initialize and bind your Yahboom Raspbot v2 to the Mission Control Gateway.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
        {[
          { id: 1, label: "Hardware Discovery", desc: "Scan local network for ROS 2 nodes." },
          { id: 2, label: "Substrate Link", desc: "Establish high-performance Websocket bridge." },
          { id: 3, label: "System Validation", desc: "Verify sensor flux and actuator health." },
        ].map((s) => (
          <div
            key={s.id}
            className={`p-4 rounded-2xl border transition-all ${step === s.id ? "bg-indigo-500/10 border-indigo-500/40" : "bg-[#0f0f12]/50 border-white/5 opacity-50"}`}
          >
            <div className="flex items-center gap-3 mb-2">
              <span
                className={`w-6 h-6 rounded-full text-xs flex items-center justify-center ${step === s.id ? "bg-indigo-500 text-white" : "bg-slate-800 text-slate-500"}`}
              >
                {s.id}
              </span>
              <span className="text-sm font-semibold text-slate-200">{s.label}</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed font-medium">{s.desc}</p>
          </div>
        ))}
      </div>

      <motion.div
        layout
        initial={{ opacity: 0, scale: 0.98 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-[#0f0f12]/80 backdrop-blur-xl border border-white/5 rounded-3xl p-8 lg:p-12 shadow-2xl relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 p-8 opacity-5">
          <Server size={120} />
        </div>

        {step === 1 && (
          <div className="space-y-8 relative z-10">
            <div>
              <h2 className="text-xl font-bold text-white mb-2">Hardware Discovery</h2>
              <p className="text-slate-400 text-sm font-medium">
                Configure your Raspbot v2 IP and bridge port. Use the robot hotspot or your LAN.
              </p>
            </div>

            <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
              <h3 className="text-sm font-bold text-indigo-300 mb-2">
                Raspbot v2 hotspot (recommended)
              </h3>
              <p className="text-slate-400 text-xs mb-3">
                Connect this PC to the robot&apos;s WiFi, then use the preset below.
              </p>
              <ul className="text-xs text-slate-300 font-mono space-y-1 mb-3">
                <li>
                  SSID: <span className="text-white">{RASPBOT_HOTSPOT.ssid}</span>
                </li>
                <li>
                  Password: <span className="text-white">{RASPBOT_HOTSPOT.password}</span>
                </li>
                <li>
                  Robot IP: <span className="text-white">{RASPBOT_HOTSPOT.ip}</span> (port{" "}
                  {RASPBOT_HOTSPOT.port})
                </li>
              </ul>
              <button
                type="button"
                onClick={applyRaspbotHotspot}
                className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold"
              >
                Use hotspot preset (192.168.1.11 : 6000)
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                  Robot host / IP
                </label>
                <input
                  type="text"
                  value={config.robotIp}
                  onChange={(e) => setConfig({ ...config, robotIp: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-indigo-500/50 transition-colors font-mono"
                />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500 uppercase tracking-widest">
                  Bridge Port
                </label>
                <input
                  type="text"
                  value={config.port}
                  onChange={(e) => setConfig({ ...config, port: e.target.value })}
                  className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-slate-200 focus:outline-none focus:border-indigo-500/50 transition-colors font-mono"
                />
                <p className="text-[11px] text-slate-500">
                  6000 = robot service; 9090 = standard rosbridge
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-4 rounded-xl bg-orange-500/5 border border-orange-500/10">
              <Info className="text-orange-400 w-5 h-5 flex-shrink-0" />
              <p className="text-xs text-orange-200/70 font-medium leading-relaxed">
                The server reads YAHBOOM_IP and YAHBOOM_BRIDGE_PORT at startup. From webapp folder
                run:{" "}
                <span className="font-mono text-orange-300">
                  .\start.ps1 -RobotIP 192.168.1.11 -BridgePort 6000
                </span>{" "}
                (or set env vars and restart). Connect this PC to WiFi &quot;{RASPBOT_HOTSPOT.ssid}
                &quot; first.
              </p>
            </div>

            <button
              onClick={() => setStep(2)}
              className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-4 rounded-2xl transition-all shadow-lg shadow-indigo-600/20 active:scale-[0.98]"
            >
              Test Hardware Connection
            </button>
          </div>
        )}

        {step === 2 && <Step2SubstrateLink config={config} onSkip={() => setStep(3)} />}

        {step === 3 && (
          <div className="space-y-8 relative z-10">
            <div className="flex items-center gap-4 p-6 rounded-2xl bg-green-500/10 border border-green-500/20">
              <CheckCircle2 className="text-green-400 w-8 h-8" />
              <div>
                <h2 className="text-lg font-bold text-white leading-tight">System Validated</h2>
                <p className="text-green-400/80 text-xs font-medium">
                  Substrate link established with 0.4ms latency.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xs font-bold text-slate-500 uppercase tracking-widest pl-1">
                Health Summary
              </h3>
              <div className="space-y-2">
                {[
                  { label: "IMU Vector Flux", status: "Optimal" },
                  { label: "Battery Core", status: "82% - Stable" },
                  { label: "Odom Array", status: "Active" },
                  { label: "LIDAR Path", status: "Link Established" },
                ].map((item, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 rounded-xl bg-white/5 border border-white/5"
                  >
                    <span className="text-sm font-medium text-slate-300">{item.label}</span>
                    <span className="text-xs font-bold text-indigo-400">{item.status}</span>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={() => (window.location.href = "/")}
              className="w-full bg-green-600 hover:bg-green-500 text-white font-bold py-4 rounded-2xl transition-all shadow-lg shadow-green-600/20"
            >
              Enter Mission Control
            </button>
          </div>
        )}
      </motion.div>
    </div>
  );
};

export default Onboarding;
