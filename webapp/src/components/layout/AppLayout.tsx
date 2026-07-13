import { AnimatePresence, motion } from "framer-motion";
import { Loader2, RefreshCw, ShieldAlert, Square, Wifi, WifiOff } from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useState } from "react";
import { api } from "../../lib/api";
import { useBackendStore } from "../../lib/store";
import { useZoom } from "../../lib/use-zoom";
import Sidebar from "./Sidebar";

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [restarting, setRestarting] = useState(false);

  const [connection, setConnection] = useState<"online" | "offline" | "loading">("loading");
  const setOnline = useBackendStore((s) => s.setOnline);

  useZoom();

  const startBackend = useCallback(async () => {
    setRestarting(true);
    try {
      const { invoke } = await import("@tauri-apps/api/core");
      await invoke("start_backend");
    } catch {
      setRestarting(false);
    }
  }, []);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") {
            setOnline(true);
            setConnection("online");
            setRestarting(false);
          } else if (typeof event.payload === "string" && event.payload.startsWith("error:")) {
            setOnline(false);
            setConnection("offline");
            setRestarting(false);
          }
        });
      } catch {
        /* not in Tauri -- HTTP polling handles it */
      }
    })();
    return () => {
      if (unlisten) unlisten();
    };
  }, [setOnline]);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const health = await api.getHealth();
        setConnection(health.robot_connection.ros === "connected" ? "online" : "offline");
        setOnline(true);
      } catch {
        setConnection("offline");
        setOnline(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 5000);
    return () => clearInterval(interval);
  }, [setOnline]);

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
            <div className="flex items-center gap-3" data-testid="backend-dot">
              <ShieldAlert className="text-indigo-500 w-5 h-5 animate-pulse" />
              <span className="text-[10px] uppercase tracking-[0.3em] font-black text-slate-400">
                Boomy System Core
              </span>
            </div>

            <div
              data-testid="backend-dot"
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

            {connection === "offline" && (
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={startBackend}
                disabled={restarting}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-500/20 border border-indigo-500/30 text-xs font-bold text-indigo-300 hover:bg-indigo-500/30 transition-colors"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${restarting ? "animate-spin" : ""}`} />
                {restarting ? "Restarting..." : "Restart Backend"}
              </motion.button>
            )}
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
