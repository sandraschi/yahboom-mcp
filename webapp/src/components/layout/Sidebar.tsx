import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
    LayoutDashboard,
    Settings,
    HelpCircle,
    MessageSquare,
    Wrench,
    Cpu,
    Rocket,
    ChevronLeft,
    ChevronRight,
    Monitor,
    Activity,
    Box
} from 'lucide-react';

interface SidebarProps {
    isCollapsed: boolean;
    onToggle: () => void;
}

const navItems = [
    { path: '/', label: 'Mission Control', icon: LayoutDashboard },
    { path: '/onboarding', label: 'Onboarding', icon: Rocket },
    { path: '/analytics', label: 'Analytics', icon: Activity },
    { path: '/chat', label: 'AI Companion', icon: MessageSquare },
    { path: '/tools', label: 'MCP Tools', icon: Wrench },
    { path: '/apps', label: 'Apps Hub', icon: Box },
    { path: '/llm', label: 'Local LLM', icon: Cpu },
    { path: '/settings', label: 'Settings', icon: Settings },
    { path: '/help', label: 'Help', icon: HelpCircle },
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
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="flex flex-col"
                        >
                            <span className="text-lg font-bold tracking-tight text-white leading-tight">G1 MISSION</span>
                            <span className="text-[10px] font-medium text-indigo-400/80 uppercase tracking-widest leading-none">Industrial Console</span>
                        </motion.div>
                    )}
                </div>
            </div>

            {/* Navigation Links */}
            <nav className="flex-1 px-4 space-y-1.5 overflow-y-auto scrollbar-none">
                {navItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) => `
              flex items-center gap-4 px-3 py-3 rounded-xl transition-all duration-200 group
              ${isActive
                                ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 shadow-lg shadow-indigo-500/5'
                                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200 border border-transparent'}
            `}
                    >
                        <item.icon className={`w-5 h-5 flex-shrink-0 transition-transform duration-300 ${isCollapsed ? '' : 'group-hover:scale-110'}`} />
                        {!isCollapsed && (
                            <motion.span
                                initial={{ opacity: 0, x: -10 }}
                                animate={{ opacity: 1, x: 0 }}
                                className="text-sm font-medium"
                            >
                                {item.label}
                            </motion.span>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* Footer / Toggle */}
            <div className="p-4 border-t border-white/5">
                <button
                    onClick={onToggle}
                    className="w-full flex items-center justify-center py-2.5 rounded-xl text-slate-500 hover:text-slate-200 hover:bg-white/5 transition-colors"
                >
                    {isCollapsed ? <ChevronRight size={20} /> : <div className="flex items-center gap-3 w-full px-2"><ChevronLeft size={20} /><span className="text-sm font-medium">Collapse</span></div>}
                </button>
            </div>
        </motion.aside>
    );
};

export default Sidebar;
