import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
    HelpCircle, Terminal, Cpu, Wifi, Wrench, AlertTriangle,
    ChevronDown, ExternalLink, Copy, Check, BookOpen, Zap,
    Activity, Radio, Play, Package
} from 'lucide-react'

// ── tiny code block with copy ─────────────────────────────────────────────────
const Code = ({ children }: { children: string }) => {
    const [copied, setCopied] = useState(false)
    const copy = () => { navigator.clipboard.writeText(children); setCopied(true); setTimeout(() => setCopied(false), 1500) }
    return (
        <div className="relative group/code mt-2">
            <pre className="bg-black/60 border border-white/10 rounded-xl px-4 py-3 text-xs text-slate-300 font-mono overflow-x-auto whitespace-pre-wrap break-all">{children}</pre>
            <button onClick={copy} className="absolute top-2 right-2 opacity-0 group-hover/code:opacity-100 transition-opacity p-1.5 rounded-lg bg-white/10 hover:bg-white/20">
                {copied ? <Check size={12} className="text-green-400" /> : <Copy size={12} className="text-slate-400" />}
            </button>
        </div>
    )
}

// ── collapsible accordion item ────────────────────────────────────────────────
const Accordion = ({ title, icon: Icon, color, children }: { title: string; icon: any; color: string; children: React.ReactNode }) => {
    const [open, setOpen] = useState(false)
    return (
        <div className={`border rounded-2xl overflow-hidden transition-all ${open ? `border-${color}-500/40 bg-${color}-500/5` : 'border-white/5 bg-[#0f0f12]/60'}`}>
            <button onClick={() => setOpen(o => !o)} className="w-full flex items-center justify-between px-5 py-4 text-left">
                <div className="flex items-center gap-3">
                    <Icon className={`w-4 h-4 text-${color}-400`} />
                    <span className="text-sm font-bold text-slate-200">{title}</span>
                </div>
                <ChevronDown className={`w-4 h-4 text-slate-500 transition-transform ${open ? 'rotate-180' : ''}`} />
            </button>
            <AnimatePresence>
                {open && (
                    <motion.div initial={{ height: 0 }} animate={{ height: 'auto' }} exit={{ height: 0 }}
                        className="overflow-hidden">
                        <div className="px-5 pb-5 space-y-3 text-sm text-slate-400 leading-relaxed">
                            {children}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    )
}

// ── API endpoint row ───────────────────────────────────────────────────────────
const ApiRow = ({ method, path, desc }: { method: string; path: string; desc: string }) => {
    const colors: Record<string, string> = { GET: 'text-green-400 bg-green-500/10', POST: 'text-blue-400 bg-blue-500/10' }
    return (
        <div className="flex items-start gap-3 p-3 rounded-xl bg-white/5 border border-white/5">
            <span className={`text-[10px] font-black px-2 py-0.5 rounded-md uppercase tracking-widest flex-shrink-0 mt-0.5 ${colors[method] ?? 'text-slate-400 bg-white/5'}`}>{method}</span>
            <div className="min-w-0">
                <div className="text-xs font-mono text-slate-200 truncate">{path}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{desc}</div>
            </div>
        </div>
    )
}

// ── MCP tool row ───────────────────────────────────────────────────────────────
const ToolRow = ({ call, desc, example }: { call: string; desc: string; example?: string }) => (
    <div className="space-y-1">
        <div className="flex items-start gap-3 p-3 rounded-xl bg-white/5 border border-white/5">
            <Radio size={13} className="text-indigo-400 mt-0.5 flex-shrink-0" />
            <div className="min-w-0 flex-1">
                <div className="text-xs font-mono text-slate-200">{call}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">{desc}</div>
            </div>
        </div>
        {example && <Code>{example}</Code>}
    </div>
)

// ── tabs ───────────────────────────────────────────────────────────────────────
const TABS = [
    { id: 'hardware', label: 'Yahboom & Raspbot', icon: Package },
    { id: 'quickstart', label: 'Quick Start', icon: Play },
    { id: 'tools', label: 'MCP Tools', icon: Cpu },
    { id: 'api', label: 'REST API', icon: Terminal },
    { id: 'connect', label: 'Connection', icon: Wifi },
    { id: 'trouble', label: 'Troubleshooting', icon: AlertTriangle },
]

const TabHardware = () => (
    <div className="space-y-6">
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-amber-300 mb-2">Yahboom</h3>
            <p className="text-[13px] text-slate-400 leading-relaxed mb-2">
                Yahboom builds ROS-based educational and research robots, expansion boards, and kits. Product lines include the <strong className="text-slate-300">Raspbot</strong> (Raspberry Pi + ROS 2), <strong className="text-slate-300">G1</strong> (humanoid/other), and the <strong className="text-slate-300">ROSMASTER</strong> expansion board used on many of their wheeled bots. This dashboard targets the <strong className="text-amber-200">Raspbot v2</strong>.
            </p>
            <a href="https://www.yahboom.net" target="_blank" rel="noopener noreferrer" className="text-xs font-bold text-amber-400 hover:text-amber-300 inline-flex items-center gap-1">
                yahboom.net <ExternalLink size={10} />
            </a>
        </div>

        <div className="space-y-3">
            <h3 className="text-sm font-bold text-slate-200">Raspbot v2 — at a glance</h3>
            <ul className="text-[13px] text-slate-400 space-y-2 list-disc list-inside">
                <li><strong className="text-slate-300">SBC:</strong> Raspberry Pi 5 (recommended) or Pi 4</li>
                <li><strong className="text-slate-300">OS image:</strong> Yahboom Raspbot image with ROS 2 Humble (and usually rosbridge_suite) pre-installed</li>
                <li><strong className="text-slate-300">Chassis:</strong> Mecanum wheels; motion via <code className="text-indigo-400">/cmd_vel</code> (Twist)</li>
                <li><strong className="text-slate-300">Low-level control:</strong> ROSMASTER expansion board (STM32F103) — motors, encoders, 9-axis IMU, UART to Pi</li>
                <li><strong className="text-slate-300">Sensors (typical):</strong> IMU (heading/pitch/roll), wheel encoders (odometry), optional USB/CSI camera, optional LIDAR (e.g. MS200) on <code className="text-indigo-400">/scan</code></li>
                <li><strong className="text-slate-300">Network:</strong> WiFi (AP or STA); default robot IP often 192.168.0.250 (Ethernet) or 192.168.1.x (WiFi)</li>
                <li><strong className="text-slate-300">ROSBridge:</strong> WebSocket on port 9090; this dashboard connects from your PC to that port</li>
            </ul>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="border border-white/10 rounded-2xl p-4 bg-white/5">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">ROSMASTER board (STM32)</h4>
                <p className="text-[12px] text-slate-400 leading-relaxed">
                    STM32F103RCT6 (ARM Cortex-M3, 72 MHz). Runs firmware/RTOS only — no Linux. Handles motor PID, encoders, IMU, servos, UART to Pi. Camera and LIDAR run on the Pi, not on the STM32.
                </p>
            </div>
            <div className="border border-white/10 rounded-2xl p-4 bg-white/5">
                <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Pi tiers</h4>
                <p className="text-[12px] text-slate-400 leading-relaxed">
                    <strong className="text-slate-300">Full Pi (Pi 5):</strong> ROS 2 + rosbridge on robot, camera, optional LIDAR. <strong className="text-slate-300">Minimal Pi:</strong> camera/stream only. <strong className="text-slate-300">Pi-less:</strong> chassis + ESP32; PC does all compute (no camera/LIDAR on bot).
                </p>
            </div>
        </div>

        <div className="space-y-2">
            <h3 className="text-sm font-bold text-slate-200">MS200 LIDAR addon (optional)</h3>
            <p className="text-[13px] text-slate-400">
                Yahboom MS200 TOF LIDAR — 360°, ~0.03–12 m, USB/serial. ~$139 USD. ROS 2 driver publishes <code className="text-indigo-400">/scan</code>; dashboard Lidar Map and telemetry use it. See <strong className="text-slate-300">Lidar addon</strong> page and <a href="https://www.yahboom.net/study/MS200" target="_blank" rel="noopener noreferrer" className="text-indigo-400 hover:underline">yahboom.net/study/MS200</a>.
            </p>
        </div>

        <div className="text-[12px] text-slate-500">
            More: <strong className="text-slate-400">docs/HARDWARE_AND_ROS2.md</strong> (Pi tiers, ROS 2 interaction, LIDAR), <strong className="text-slate-400">docs/CONNECTIVITY.md</strong> (WiFi, robot IP, ROSBridge at boot).
        </div>
    </div>
)

const TabQuickStart = () => (
    <div className="space-y-5">
        <div className="bg-indigo-500/10 border border-indigo-500/30 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-indigo-300 mb-1">Prerequisites</h3>
            <ul className="text-[13px] text-slate-400 space-y-1 list-disc list-inside">
                <li>Yahboom Raspbot v2 powered on and on same LAN (or PC on robot WiFi)</li>
                <li>Raspberry Pi on robot running ROS 2 Humble (pre-installed on stock image)</li>
                <li>ROSBridge WebSocket server on the robot (pre-installed; starts at boot if you ran the one-time script)</li>
                <li>Python ≥ 3.11 + Node.js ≥ 18 (on workstation)</li>
            </ul>
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Step 1 — ROSBridge on the robot</p>
            <p className="text-[12px] text-slate-500">Stock Raspbot image already has rosbridge. If it is not set to start at boot, run once on the Pi:</p>
            <Code>ros2 launch rosbridge_server rosbridge_websocket_launch.xml</Code>
            <p className="text-[12px] text-slate-500">To start automatically at boot, use the one-time script in <strong className="text-slate-400">docs/ROSBRIDGE_AT_BOOT.md</strong>.</p>
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Step 2 — Configure robot IP (if needed)</p>
            <Code>$env:YAHBOOM_IP = "192.168.1.100"
                $env:YAHBOOM_BRIDGE_PORT = "9090"</Code>
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Step 3 — Launch (Windows)</p>
            <Code>.\start.ps1      # or double-click start.bat</Code>
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Alternative — manual launch</p>
            <Code>uv run yahboom-mcp --mode dual --robot-ip 192.168.1.100 --port 10892</Code>
        </div>
        <div className="bg-green-500/10 border border-green-500/30 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-green-300 mb-1">Verify it's working</h3>
            <p className="text-[13px] text-slate-400 mb-2">Open the health endpoint — <code className="text-green-400">connected: true</code> means the bot is linked.</p>
            <Code>curl http://localhost:10892/api/v1/health</Code>
        </div>
        <div className="grid grid-cols-2 gap-4">
            {[
                { label: 'MCP Server', url: 'http://localhost:10892/docs', icon: Terminal },
                { label: 'Dashboard', url: 'http://localhost:10793/', icon: Activity },
            ].map(l => (
                <a key={l.label} href={l.url} target="_blank" rel="noopener noreferrer"
                    className="flex items-center gap-3 p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-indigo-500/40 hover:bg-indigo-500/10 transition-all group">
                    <l.icon size={16} className="text-indigo-400" />
                    <div>
                        <div className="text-sm font-bold text-slate-200 group-hover:text-white">{l.label}</div>
                        <div className="text-[11px] text-slate-500">{l.url}</div>
                    </div>
                    <ExternalLink size={12} className="text-slate-600 ml-auto" />
                </a>
            ))}
        </div>
    </div>
)

const TabTools = () => (
    <div className="space-y-6">
        <div className="bg-[#0f0f12]/60 border border-white/5 rounded-2xl p-5">
            <p className="text-sm text-slate-400 leading-relaxed">
                All MCP tools are available via AI clients pointed at <code className="text-indigo-400">http://localhost:10892/sse</code>.
                The main tool is <span className="text-white font-bold">yahboom()</span> — a portmanteau with an <code className="text-indigo-400">action</code> parameter that routes to sub-operations.
            </p>
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Motion Control</p>
            <ToolRow call='yahboom(action="move", linear=0.2, angular=0.0)' desc="Move forward at 0.2 m/s" example='yahboom(action="move", linear=0.3, angular=0.0)   # forward
yahboom(action="move", linear=0.0, angular=0.5)   # turn left
yahboom(action="move", linear=0.0, angular=0.0)   # STOP' />
            <ToolRow call='yahboom(action="move_to", x=1.5, y=0.0)' desc="Autonomous waypoint navigation (requires odometry)" />
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Sensors & Diagnostics</p>
            <ToolRow call='yahboom(action="read_imu")' desc="Returns heading (°), pitch, roll from 9-axis IMU" />
            <ToolRow call='yahboom(action="health")' desc="Returns bridge connection state and battery percentage" />
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Help System (drill-down)</p>
            <ToolRow call='yahboom_help()' desc="List all help categories" example='yahboom_help()                              # list categories
yahboom_help(category="motion")             # list topics in motion
yahboom_help(category="motion", topic="mecanum")  # full detail' />
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">MCP Client config (mcp_config.json)</p>
            <Code>{`{
  "mcpServers": {
    "yahboom": {
      "url": "http://localhost:10892/sse",
      "transport": "sse"
    }
  }
}`}</Code>
        </div>
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-2xl p-4 text-[13px] text-slate-400">
            <span className="text-amber-300 font-bold">Velocity limits: </span>
            linear ±1.0 m/s · angular ±2.0 rad/s. Values outside range are clamped by firmware — no hard errors.
        </div>
    </div>
)

const TabApi = () => (
    <div className="space-y-6">
        <div className="space-y-2">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Base URL</p>
            <Code>http://localhost:10892</Code>
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Endpoints</p>
            <ApiRow method="GET" path="/api/v1/health" desc="Service health + ROS 2 connection state" />
            <ApiRow method="GET" path="/api/v1/telemetry" desc="Battery %, IMU heading, wheel velocity (bridge must be connected)" />
            <ApiRow method="POST" path="/api/v1/control/move" desc="Direct motion: ?linear=0.2&angular=0.0" />
            <ApiRow method="GET" path="/stream" desc="MJPEG video stream — embed as <img src>" />
            <ApiRow method="GET" path="/sse" desc="MCP over Server-Sent Events — for AI client connections" />
            <ApiRow method="GET" path="/docs" desc="Interactive Swagger UI for all REST endpoints" />
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Health response shape</p>
            <Code>{`{
  "status": "ok",
  "service": "yahboom-mcp",
  "connected": false,
  "timestamp": "2026-03-04T05:00:00"
}`}</Code>
        </div>
        <div className="space-y-3">
            <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Example — move via curl</p>
            <Code>curl -X POST "http://localhost:10892/api/v1/control/move?linear=0.2&angular=0.0"</Code>
        </div>
        <a href="http://localhost:10892/docs" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-3 p-4 rounded-2xl bg-white/5 border border-white/10 hover:border-indigo-500/40 hover:bg-indigo-500/10 transition-all group">
            <Wrench size={16} className="text-indigo-400" />
            <div>
                <div className="text-sm font-bold text-slate-200 group-hover:text-white">Open Swagger UI</div>
                <div className="text-[11px] text-slate-500">http://localhost:10892/docs</div>
            </div>
            <ExternalLink size={12} className="text-slate-600 ml-auto" />
        </a>
    </div>
)

const TabConnect = () => (
    <div className="space-y-5">
        <Accordion title="What's needed on the robot side?" icon={Cpu} color="indigo">
            <p>Yahboom Raspbot v2 (Raspberry Pi 5 or 4) with stock image: ROS 2 Humble and rosbridge_suite are pre-installed. ROSBridge must be running (at boot or manually):</p>
            <Code>ros2 launch rosbridge_server rosbridge_websocket_launch.xml</Code>
            <p>Default port: <strong className="text-slate-300">9090</strong>. Robot and workstation must be on the same subnet.</p>
        </Accordion>
        <Accordion title="How do I set the robot IP?" icon={Wifi} color="indigo">
            <p>Set environment variables before running the server:</p>
            <Code>$env:YAHBOOM_IP = "192.168.1.100"
                $env:YAHBOOM_BRIDGE_PORT = "9090"</Code>
            <p>Or pass via CLI flag:</p>
            <Code>uv run yahboom-mcp --mode dual --robot-ip 192.168.1.100</Code>
            <p>Or use the <strong className="text-slate-300">Onboarding</strong> page in the webapp to save these settings.</p>
        </Accordion>
        <Accordion title="What do the server run modes mean?" icon={Terminal} color="indigo">
            <ul className="space-y-2">
                <li><strong className="text-slate-300">stdio</strong> — MCP only (default for AI client use via mcp_config.json)</li>
                <li><strong className="text-slate-300">http</strong> — FastAPI + SSE only (REST + MCP, no stdio)</li>
                <li><strong className="text-slate-300">dual</strong> — both stdio and HTTP. Used by start.ps1</li>
            </ul>
        </Accordion>
        <Accordion title="How do AI clients connect?" icon={Radio} color="indigo">
            <p>Point your <code className="text-indigo-400">mcp_config.json</code> to the SSE endpoint:</p>
            <Code>{`"yahboom": { "url": "http://localhost:10892/sse", "transport": "sse" }`}</Code>
            <p>Works with Claude Desktop, Cursor, Antigravity, and any FastMCP 3.0-compatible client.</p>
        </Accordion>
    </div>
)

const TabTrouble = () => (
    <div className="space-y-4">
        {[
            {
                icon: AlertTriangle, color: 'amber', title: '"Robot Not Connected" banner showing',
                body: 'Backend is up but ROSBridge is unreachable.',
                fix: ['1. Confirm robot is powered on', '2. SSH to Pi and run rosbridge: ros2 launch rosbridge_server rosbridge_websocket_launch.xml', '3. Ping the robot IP from your workstation', '4. Check firewall rules for port 9090'],
            },
            {
                icon: Zap, color: 'red', title: '"Server Down" banner / cannot reach port 10892',
                body: 'Python backend has not started or crashed.',
                fix: ['Run .\\start.ps1 (or start.bat)', 'Check terminal for Python tracebacks', 'Test: curl http://localhost:10892/api/v1/health', 'Port conflict: netstat -ano | Select-String 10892 — kill the PID'],
            },
            {
                icon: Terminal, color: 'red', title: 'npm Win32 error during start',
                body: 'Vite cannot start because npm.cmd is not a Win32 exe — start.ps1 must invoke it via cmd /c.',
                fix: ['In start.ps1 the line must be: Start-Process cmd -ArgumentList "/c", "npm", "run", "dev"'],
            },
            {
                icon: Activity, color: 'indigo', title: 'Dashboard blank / black after first load',
                body: 'A TypeError inside a React component is unmounting the tree.',
                fix: ['Open browser DevTools (F12) → Console → find red TypeError', 'Common cause: .toFixed() on undefined telemetry field', 'Ensure main.tsx wraps App in <BrowserRouter>'],
            },
            {
                icon: BookOpen, color: 'indigo', title: 'FastMCP AttributeError: no attribute .app',
                body: 'FastMCP 3.0 removed the .app property.',
                fix: ['Use FastAPI-first pattern: create app = FastAPI(...) then mcp = FastMCP.from_fastapi(app)'],
            },
        ].map((item, i) => (
            <Accordion key={i} title={item.title} icon={item.icon} color={item.color}>
                <p>{item.body}</p>
                <ul className="mt-2 space-y-1 text-[12px] text-slate-400">
                    {item.fix.map((f, j) => <li key={j} className="font-mono">{f}</li>)}
                </ul>
            </Accordion>
        ))}
    </div>
)

// ── Main ───────────────────────────────────────────────────────────────────────
const Help = () => {
    const [tab, setTab] = useState('hardware')

    const content: Record<string, React.ReactNode> = {
        hardware: <TabHardware />,
        quickstart: <TabQuickStart />,
        tools: <TabTools />,
        api: <TabApi />,
        connect: <TabConnect />,
        trouble: <TabTrouble />,
    }

    return (
        <div className="space-y-6 py-4 max-w-4xl">
            {/* Header */}
            <div className="flex items-center gap-4">
                <HelpCircle className="text-indigo-400 w-8 h-8" />
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Mission Support</h1>
                    <p className="text-slate-400 text-sm">Complete reference for the Yahboom ROS 2 MCP server and dashboard.</p>
                </div>
            </div>

            {/* Tab bar */}
            <div className="flex gap-1 p-1 bg-white/5 border border-white/5 rounded-2xl w-fit">
                {TABS.map(t => {
                    const active = tab === t.id
                    return (
                        <button
                            key={t.id}
                            onClick={() => setTab(t.id)}
                            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold uppercase tracking-widest transition-all ${active ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/30' : 'text-slate-500 hover:text-slate-300'
                                }`}
                        >
                            <t.icon size={13} />
                            <span className="hidden sm:inline">{t.label}</span>
                        </button>
                    )
                })}
            </div>

            {/* Tab content */}
            <AnimatePresence mode="wait">
                <motion.div
                    key={tab}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                    transition={{ duration: 0.15 }}
                >
                    {content[tab]}
                </motion.div>
            </AnimatePresence>
        </div>
    )
}

export default Help
