import {
  Activity,
  AlertCircle,
  ChevronRight,
  HardDrive,
  ListFilter,
  Play,
  Power,
  RefreshCw,
  Search,
  Terminal as TerminalIcon,
  Trash2,
} from "lucide-react";
import type React from "react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import StackStatusTable from "../../components/StackStatusTable";
import { api, type DiagStackResponse, type DriverStackSnapshot, type Health } from "../../lib/api";

interface RosTopic {
  name: string;
  type: string;
}

const Diagnostics: React.FC = () => {
  const [stack, setStack] = useState<DiagStackResponse | null>(null);
  const [topics, setTopics] = useState<RosTopic[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [shellOutput, setShellOutput] = useState<string[]>([]);
  const [command, setCommand] = useState("");
  const [executing, setExecuting] = useState(false);
  const [health, setHealth] = useState<Health | null>(null);
  const [topicFetchError, setTopicFetchError] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const fetchData = useCallback(async () => {
    try {
      const [stackData, topicData, healthData] = await Promise.all([
        api.getDiagStack(),
        api.getRosTopics(),
        api.getHealth(),
      ]);
      setStack(stackData);
      setHealth(healthData);
      if (topicData.success && topicData.topics) {
        setTopicFetchError(null);
        const formattedTopics = topicData.topics.map((t: any) => ({
          name: Array.isArray(t) ? t[0] : t.name,
          type: Array.isArray(t) ? t[1] : t.type,
        }));
        setTopics(formattedTopics);
      } else {
        setTopics([]);
        setTopicFetchError(
          topicData.success ? null : (topicData.error ?? "Topic list unavailable"),
        );
      }
    } catch (error) {
      console.error("Diagnostic fetch failed:", error);
      setTopicFetchError("Request failed — is the backend on :10892 running?");
    }
  }, []);

  const handleRestartBringup = async () => {
    if (!confirm("This will force a native ROS 2 bringup via SSH. Continue?")) return;
    setExecuting(true);
    try {
      const res = await api.postRestartRos();
      setShellOutput((prev) => [...prev, `[SYSTEM] ${res.message}`]);
      setTimeout(fetchData, 8000);
    } catch (_error) {
      setShellOutput((prev) => [...prev, "Error triggering native bringup."]);
    } finally {
      setExecuting(false);
    }
  };

  const handleResyncRos = async () => {
    setExecuting(true);
    try {
      const res = await api.postResyncRos();
      if (res.success) {
        setShellOutput((prev) => [...prev, "[SYSTEM] Sensory re-synchronization successful."]);
        fetchData();
      } else {
        setShellOutput((prev) => [...prev, "[SYSTEM] Re-sync failed. Check bridge logs."]);
      }
    } catch (_error) {
      setShellOutput((prev) => [...prev, "Error during sensory re-sync."]);
    } finally {
      setExecuting(false);
    }
  };

  const handleExecute = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!command.trim() || executing) return;
    setExecuting(true);
    try {
      const res = await api.postExecCommand(command);
      setShellOutput((prev) => [...prev, `$ ${command}`, res.stdout || res.stderr || "No output"]);
      setCommand("");
    } finally {
      setExecuting(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const filteredTopics = topics.filter(
    (t) =>
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.type.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  const rosLive =
    health?.robot_connection?.ros === "connected" ||
    stack?.service_status === "rosbridge_connected";

  const driverStack: DriverStackSnapshot | undefined =
    health?.robot_connection?.driver_stack ?? stack?.driver_stack;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Activity className="w-8 h-8 text-blue-500" />
            ROS 2 Insight Hub
          </h1>
          <p className="text-gray-400 mt-1 text-sm flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="font-mono text-gray-300">
              Robot {health?.robot_connection.ip ?? "—"}
            </span>
            <span className="text-slate-600">·</span>
            <span className={rosLive ? "text-emerald-400 font-mono" : "text-amber-400 font-mono"}>
              ROS {health?.robot_connection.ros ?? stack?.service_status ?? "…"}
            </span>
            <span className="text-slate-600">·</span>
            <span
              className={
                health?.robot_connection.ssh === "connected"
                  ? "text-emerald-400 font-mono"
                  : "text-amber-400 font-mono"
              }
            >
              SSH {health?.robot_connection?.ssh ?? "…"}
            </span>
            {!rosLive && (
              <>
                <span className="text-slate-600">·</span>
                <Link to="/logs" className="text-indigo-400 hover:underline text-xs font-sans">
                  Server logs
                </Link>
              </>
            )}
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleResyncRos}
            disabled={executing}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 rounded-lg transition-all border border-blue-500/30 font-bold text-sm"
          >
            <RefreshCw className={`w-4 h-4 ${executing ? "animate-spin" : ""}`} />
            System Re-Sync
          </button>
          <button
            onClick={handleRestartBringup}
            disabled={executing}
            className="flex items-center gap-2 px-4 py-2 bg-red-600/10 hover:bg-red-600/20 text-red-500 rounded-lg transition-all border border-red-500/30 font-bold text-sm"
          >
            <Power className="w-4 h-4" />
            Hard Reset
          </button>
        </div>
      </div>

      {health?.stack ? (
        <div className="rounded-xl border border-slate-700/80 bg-gray-900/40 p-4">
          <h2 className="text-sm font-black text-white uppercase tracking-wide mb-3 flex items-center gap-2">
            <HardDrive className="w-4 h-4 text-indigo-400" />
            Full stack status
          </h2>
          <StackStatusTable stack={health.stack} />
        </div>
      ) : (
        driverStack && (
          <div
            className={`rounded-xl border px-4 py-3 text-sm ${
              driverStack.status === "running"
                ? "border-emerald-500/35 bg-emerald-950/30"
                : driverStack.status === "absent"
                  ? "border-amber-500/40 bg-amber-950/35"
                  : driverStack.status === "ssh_offline"
                    ? "border-slate-600/50 bg-slate-900/50"
                    : "border-red-500/35 bg-red-950/30"
            }`}
          >
            <div className="flex flex-wrap items-center gap-2 font-mono text-xs text-white">
              <HardDrive className="w-4 h-4 text-indigo-400 shrink-0" />
              <span className="font-black tracking-tight">Docker driver stack</span>
              <span className="text-slate-500">({driverStack.container})</span>
              <span
                className={
                  driverStack.status === "running"
                    ? "text-emerald-400"
                    : driverStack.status === "absent"
                      ? "text-amber-300"
                      : "text-slate-400"
                }
              >
                {driverStack.status.toUpperCase().replace("_", " ")}
              </span>
              <span className="text-slate-500">
                nodes: {driverStack.ros_node_line_count}
                {driverStack.matched_nodes?.length
                  ? ` · drivers: ${driverStack.matched_nodes.join(", ")}`
                  : " · drivers: —"}
              </span>
              <span className="text-slate-500">
                rosbridge in graph:{" "}
                {driverStack.rosbridge_node_seen === null
                  ? "—"
                  : driverStack.rosbridge_node_seen
                    ? "yes"
                    : "no"}
              </span>
            </div>
            {driverStack.detail && (
              <p className="mt-2 text-xs text-slate-400 leading-relaxed">{driverStack.detail}</p>
            )}
          </div>
        )
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Topic Explorer (Main Panel) */}
        <div className="lg:col-span-8 space-y-6">
          <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden flex flex-col h-[600px]">
            <div className="p-4 border-b border-gray-800 flex items-center justify-between bg-gray-800/30">
              <div className="flex items-center gap-2 text-white font-semibold">
                <ListFilter className="w-5 h-5 text-green-500" />
                Native Topic Explorer
              </div>
              <div className="relative w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                <input
                  type="text"
                  placeholder="Filter topics..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full bg-black/40 border border-gray-700 rounded-lg py-1.5 pl-10 pr-4 text-sm text-white focus:ring-1 focus:ring-blue-500 transition-all font-mono"
                />
              </div>
            </div>
            <div className="flex-1 overflow-y-auto custom-scrollbar">
              <table className="w-full text-left font-mono text-xs">
                <thead className="bg-black/50 sticky top-0 text-gray-400 uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3">Topic Path</th>
                    <th className="px-4 py-3">Message Type</th>
                    <th className="px-4 py-3 w-20 text-center">Pulse</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800/50">
                  {filteredTopics.map((topic, i) => (
                    <tr key={i} className="hover:bg-blue-500/5 group transition-colors">
                      <td className="px-4 py-3 text-blue-400 font-bold truncate">{topic.name}</td>
                      <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{topic.type}</td>
                      <td className="px-4 py-3 text-center">
                        <div className="w-2 h-2 rounded-full bg-green-500/50 animate-pulse mx-auto shadow-[0_0_8px_rgba(34,197,94,0.4)]" />
                      </td>
                    </tr>
                  ))}
                  {filteredTopics.length === 0 && (
                    <tr>
                      <td colSpan={3} className="px-4 py-12 align-top">
                        {topicFetchError ? (
                          <div className="rounded-lg border border-red-500/30 bg-red-500/5 p-4 text-left">
                            <p className="text-red-400 font-semibold text-sm">Topic list error</p>
                            <p className="text-red-300/80 font-mono text-xs mt-1">{topicFetchError}</p>
                          </div>
                        ) : topics.length > 0 ? (
                          <p className="text-center text-gray-500 italic">
                            No topics match &quot;{searchTerm}&quot;.
                          </p>
                        ) : !rosLive ? (
                          <div className="max-w-xl mx-auto space-y-3 text-left">
                            <p className="text-amber-400 font-semibold text-sm">
                              ROS bridge is not connected
                            </p>
                            <p className="text-gray-400 text-xs leading-relaxed">
                              The topic table stays empty until{" "}
                              <span className="font-mono text-gray-300">roslibpy</span> can reach
                              WebSocket rosbridge on the Pi (default{" "}
                              <span className="font-mono">YAHBOOM_BRIDGE_PORT=9090</span>
                              ). The hub is still talking to this PC&apos;s gateway; the Raspberry
                              at <span className="font-mono">{health?.robot_connection.ip ?? "—"}</span>{" "}
                              is not on the graph.
                            </p>
                            <ul className="text-gray-500 text-xs list-disc list-inside space-y-1">
                              <li>Robot powered, same LAN, correct IP in start script / YAHBOOM_IP</li>
                              <li>On the Pi: rosbridge running (e.g. rosbridge_websocket launch)</li>
                              <li>Firewall allows TCP to the bridge port from this host</li>
                            </ul>
                            <p className="text-xs text-slate-500">
                              Host-side errors (SSH, connect timeout) appear in{" "}
                              <Link to="/logs" className="text-indigo-400 hover:underline">
                                Server logs
                              </Link>
                              .
                            </p>
                          </div>
                        ) : (
                          <p className="text-center text-gray-500 text-sm">
                            ROS reports connected but no topics were returned (no rosapi on
                            rosbridge, SSH down, or no publishers). Try{" "}
                            <span className="font-mono">System Re-Sync</span>, ensure SSH to the
                            Pi works for topic fallback, or add rosapi to your rosbridge launch.
                          </p>
                        )}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <div className="p-3 bg-black/40 border-t border-gray-800 flex justify-between text-[10px] text-gray-500 font-mono">
              <span>TOTAL: {topics.length} TOPICS DISCOVERED</span>
              <span className="text-blue-500">ROS 2 FOXY / HUMBLE COMPATIBLE</span>
            </div>
          </div>

          <div className="bg-black border border-gray-800 rounded-xl overflow-hidden flex flex-col h-[280px]">
            <div className="p-3 border-b border-gray-800 flex items-center justify-between bg-gray-900/50">
              <div className="flex items-center gap-2 text-xs text-gray-400 font-mono">
                <TerminalIcon className="w-4 h-4" />
                SSH DIAGNOSTIC SHELL
              </div>
              <button
                onClick={() => setShellOutput([])}
                className="text-[10px] text-gray-600 hover:text-white transition-colors uppercase"
              >
                Clear
              </button>
            </div>
            <div className="flex-1 p-4 font-mono text-[11px] overflow-y-auto custom-scrollbar text-green-500/90 leading-tight">
              {shellOutput.map((l, i) => (
                <div key={i}>{l}</div>
              ))}
              <div ref={logEndRef} />
            </div>
            <form onSubmit={handleExecute} className="p-2 bg-gray-900 flex gap-2">
              <span className="text-blue-500 font-mono pl-2">$</span>
              <input
                type="text"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                className="flex-1 bg-transparent border-none text-white focus:ring-0 font-mono text-sm"
                placeholder="Execute raw command..."
              />
            </form>
          </div>
        </div>

        {/* Right Column */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-gray-800 flex items-center gap-2 bg-gray-800/30">
              <HardDrive className="w-5 h-5 text-blue-500" />
              <h2 className="font-semibold text-white">Active Nodes</h2>
            </div>
            <div className="p-4 space-y-2 max-h-[400px] overflow-y-auto custom-scrollbar">
              {stack?.ros_nodes && stack.ros_nodes.length > 0 ? (
                stack.ros_nodes.map((node, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-2.5 bg-black/40 rounded-lg border border-gray-800/50 group hover:border-blue-500/30 transition-all"
                  >
                    <div className="flex items-center gap-3">
                      <ChevronRight className="w-3 h-3 text-gray-700" />
                      <span className="text-xs text-gray-300 font-mono truncate max-w-[200px]">
                        {node}
                      </span>
                    </div>
                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_5px_rgba(34,197,94,0.5)]" />
                  </div>
                ))
              ) : (
                <div className="p-10 text-center">
                  <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                  <p className="text-red-400 font-mono text-xs">CRITICAL: No Active Nodes</p>
                </div>
              )}
            </div>
          </div>

          <div className="bg-gray-900/50 backdrop-blur-md border border-gray-800 rounded-xl overflow-hidden">
            <div className="p-4 border-b border-gray-800 flex items-center gap-2 bg-gray-800/30">
              <Activity className="w-5 h-5 text-orange-500" />
              <h2 className="font-semibold text-white">System Actions</h2>
            </div>
            <div className="p-4 grid grid-cols-1 gap-3">
              <button
                onClick={handleRestartBringup}
                className="flex items-center gap-3 p-3 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 rounded-lg border border-blue-500/20 transition-all text-sm group"
              >
                <Play className="w-4 h-4 group-hover:scale-110 transition-transform" />
                <div className="text-left">
                  <div className="font-bold">Sync Native Topics</div>
                  <div className="text-[10px] opacity-70">Force Yahboom car bringup</div>
                </div>
              </button>
              <button className="flex items-center gap-3 p-3 bg-purple-600/10 hover:bg-purple-600/20 text-purple-400 rounded-lg border border-purple-500/20 transition-all text-sm group">
                <Trash2 className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                <div className="text-left">
                  <div className="font-bold">Purge ROS Logs</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Diagnostics;
