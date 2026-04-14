import { AnimatePresence, motion } from "framer-motion";
import { Loader2, ShieldAlert, Square, Wifi, WifiOff } from "lucide-react";
import type React from "react";
import { useEffect, useState } from "react";
import { api } from "../../lib/api";
import Sidebar from "./Sidebar";

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [stopping, setStopping] = useState(false);

  const [connection, setConnection] = useState<"online" | "offline" | "loading">("loading");

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await api.getHealth();
        setConnection(health.robot_connection.ros === "connected" ? "online" : "offline");
      } catch {
        setConnection("offline");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleEmergencyStop = async () => {
    setStopping(true);
    try {
      await api.postStopAll();
    } catch (err) {
      console.error("Stop All failed:", err);
    } finally {
      setTimeout(() => setStopping(false), 2000);
    }
  };

  return (
    <div className="flex w-screen h-screen bg-[#0a0a0c] text-slate-200 overflow-hidden font-sans selection:bg-indigo-500/30">
      {/* Retractable Sidebar */}
      <Sidebar isCollapsed={isCollapsed} onToggle={() => setIsCollapsed(!isCollapsed)} />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-hidden bg-[#0a0a0c] relative">
        {/* Global Header with Emergency Stop */}
        <header className="h-20 border-b border-white/5 flex items-center justify-between px-10 relative z-20 backdrop-blur-xl bg-slate-900/20">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
              <ShieldAlert className="text-indigo-500 w-5 h-5 animate-pulse" />
              <span className="text-[10px] uppercase tracking-[0.3em] font-black text-slate-400">
                Boomy System Core
              </span>
            </div>

            <div
              className={`flex items-center gap-2 px-3 py-1 rounded-full border ${
                connection === "online"
                  ? "bg-green-500/10 border-green-500/20 text-green-500"
                  : "bg-red-500/10 border-red-500/20 text-red-500"
              }`}
            >
              {connection === "online" ? (
                <Wifi className="w-3.5 h-3.5" />
              ) : (
                <WifiOff className="w-3.5 h-3.5" />
              )}
              <span className="text-[9px] font-bold uppercase tracking-wider">
                {connection === "online" ? "Link Active" : "Link Lost"}
              </span>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleEmergencyStop}
            disabled={stopping}
            className={`flex items-center gap-3 px-8 py-3 rounded-2xl font-black uppercase tracking-[0.2em] shadow-2xl transition-all border-2 
                           ${
                             stopping
                               ? "bg-red-900/50 border-red-500/50 text-red-500 cursor-not-allowed"
                               : "bg-red-600 border-red-500 text-white hover:bg-red-500 hover:shadow-red-500/50 active:bg-red-700"
                           }`}
          >
            {stopping ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Square className="fill-current w-5 h-5" />
            )}
            <span className="text-sm">{stopping ? "HALTING..." : "EMERGENCY STOP"}</span>
          </motion.button>
        </header>

        {/* Background Decorative Elements */}
        <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-indigo-600/5 blur-[120px] rounded-full -translate-y-1/2 translate-x-1/2 pointer-events-none" />
        <div className="absolute bottom-0 left-0 w-[400px] h-[400px] bg-purple-600/5 blur-[100px] rounded-full translate-y-1/2 -translate-x-1/2 pointer-events-none" />

        {/* Scrollable Page Content */}
        <div className="flex-1 overflow-y-auto relative z-10 p-6 lg:p-10 w-full">
          <AnimatePresence mode="wait">
            <motion.div
              key={window.location.pathname}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.3, ease: "easeOut" }}
              className="max-w-7xl mx-auto w-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
};

export default AppLayout;
