import { motion } from "framer-motion";
import {
  Activity,
  Box,
  ChevronLeft,
  ChevronRight,
  Cpu,
  Gamepad2,
  Gauge,
  HelpCircle,
  Layers,
  LayoutDashboard,
  Lightbulb,
  Map,
  MessageSquare,
  Mic,
  Monitor,
  Package,
  Play,
  Rocket,
  ScanLine,
  ScrollText,
  Settings,
  Shield,
  Sparkles,
  Wrench,
} from "lucide-react";
import type React from "react";
import { NavLink } from "react-router-dom";

interface SidebarProps {
  isCollapsed: boolean;
  onToggle: () => void;
}

const navGroups = [
  {
    id: "primary",
    label: "Operations",
    icon: LayoutDashboard,
    items: [
      { path: "/", label: "Dashboard", icon: LayoutDashboard },
      { path: "/analytics", label: "Analytics", icon: Activity },
      { path: "/viz", label: "Visualization", icon: ScanLine },
      { path: "/map", label: "Map", icon: Map },
      { path: "/lidar-map", label: "Lidar Map", icon: Layers },
    ],
  },
  {
    id: "hardware",
    label: "Chassis & Payload",
    icon: Box,
    items: [
      { path: "/movement", label: "Movement", icon: Gamepad2 },
      { path: "/sensors", label: "Sensors", icon: Gauge },
      { path: "/peripherals", label: "Peripherals",    icon: Lightbulb },
      { path: "/voice",       label: "Voice & Audio",  icon: Mic       },
      { path: "/voice-upgrade", label: "Voice Upgrade", icon: Sparkles },
      { path: "/lidar-addon", label: "Lidar Addon",    icon: Package   },
    ],
  },
  {
    id: "intelligence",
    label: "Intelligence",
    icon: Cpu,
    items: [
      { path: "/chat", label: "AI Companion", icon: MessageSquare },
      { path: "/llm", label: "Local LLM", icon: Cpu },
      { path: "/workflows", label: "Workflows", icon: Play },
    ],
  },
  {
    id: "system",
    label: "System Hub",
    icon: Wrench,
    items: [
      { path: "/diagnostics", label: "Diagnostic Hub", icon: Shield },
      { path: "/logs", label: "Server logs", icon: ScrollText },
      { path: "/tools", label: "MCP Tools", icon: Wrench },
      { path: "/apps", label: "Apps Hub", icon: Box },
      { path: "/settings", label: "Settings", icon: Settings },
      { path: "/onboarding", label: "Onboarding", icon: Rocket },
      { path: "/help", label: "Help", icon: HelpCircle },
    ],
  },
];

const Sidebar: React.FC<SidebarProps> = ({ isCollapsed, onToggle }) => {
  return (
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 80 : 280 }}
      className="relative flex flex-col bg-[#0f0f12] border-r border-white/5 z-50 overflow-hidden"
    >
      {/* Brand Section */}
      <div className="h-20 flex items-center px-6 mb-4">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Monitor className="text-white w-6 h-6" />
          </div>
          {!isCollapsed && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex flex-col">
              <span className="text-lg font-bold tracking-tight text-white leading-tight">
                BOOMY CONTROL
              </span>
              <span className="text-[10px] font-medium text-indigo-400/80 uppercase tracking-widest leading-none">
                Industrial Control
              </span>
            </motion.div>
          )}
        </div>
      </div>

      {/* Navigation Groups */}
      <nav className="flex-1 px-4 space-y-4 overflow-y-auto scrollbar-none py-2">
        {navGroups.map((group) => (
          <div key={group.id} className="space-y-1">
            {!isCollapsed && (
              <div className="px-3 py-1 flex items-center justify-between text-[10px] font-black text-slate-500 uppercase tracking-widest">
                {group.label}
              </div>
            )}
            <div className="space-y-1">
              {group.items.map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={({ isActive }) => `
                                        flex items-center gap-4 px-3 py-2.5 rounded-xl transition-all duration-200 group
                                        ${
                                          isActive
                                            ? "bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-lg shadow-indigo-500/5"
                                            : "text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent"
                                        }
                                    `}
                >
                  <item.icon
                    className={`w-4 h-4 flex-shrink-0 transition-transform duration-300 ${isCollapsed ? "" : "group-hover:scale-110"}`}
                  />
                  {!isCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="text-xs font-semibold"
                    >
                      {item.label}
                    </motion.span>
                  )}
                </NavLink>
              ))}
            </div>
            {!isCollapsed && <div className="h-px bg-white/5 mx-3 mt-4 mb-2" />}
          </div>
        ))}
      </nav>

      {/* Footer / Toggle */}
      <div className="p-4 border-t border-white/5">
        <button
          onClick={onToggle}
          className="w-full flex items-center justify-center py-2.5 rounded-xl text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors"
        >
          {isCollapsed ? (
            <ChevronRight size={20} />
          ) : (
            <div className="flex items-center gap-3 w-full px-2">
              <ChevronLeft size={20} />
              <span className="text-sm font-medium">Collapse</span>
            </div>
          )}
        </button>
      </div>
    </motion.aside>
  );
};

export default Sidebar;
