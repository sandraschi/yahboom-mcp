import type { StackOverview } from "../lib/api";

function badge(ok: boolean) {
  return ok ? (
    <span className="rounded px-2 py-0.5 text-[10px] font-black bg-emerald-950/80 text-emerald-300 border border-emerald-600/40">
      OK
    </span>
  ) : (
    <span className="rounded px-2 py-0.5 text-[10px] font-black bg-red-950/80 text-red-300 border border-red-600/40">
      FAIL
    </span>
  );
}

function layerStateBadge(ok: boolean, rowId: string, restartLoop: boolean) {
  if (rowId === "ros_container" && restartLoop) {
    return (
      <span className="rounded px-2 py-0.5 text-[10px] font-black bg-amber-950/90 text-amber-200 border border-amber-500/70 uppercase tracking-wide">
        Loop
      </span>
    );
  }
  return badge(ok);
}

export default function StackStatusTable({ stack }: { stack: StackOverview }) {
  const g = stack.goliath_to_robot;
  const pi = stack.pi_host;
  const dk = stack.docker_engine;
  const ctr = stack.ros_container;
  const rb = stack.rosbridge_from_pc;

  const restartLoop =
    ctr.restart_loop === true ||
    ctr.lifecycle?.phase === "restart_loop" ||
    (ctr.docker_state ?? "").toLowerCase().includes("restarting");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-slate-500">
        <span>
          Stack probe <span className="text-slate-300">{stack.probed_at}</span>
        </span>
        <span>cache TTL {stack.cache_ttl_sec}s</span>
      </div>

      {restartLoop ? (
        <div
          className="rounded-xl border-2 border-amber-500/85 bg-amber-950/45 px-4 py-3 shadow-[0_0_24px_rgba(245,158,11,0.12)]"
          role="status"
        >
          <div className="text-xs font-black tracking-widest text-amber-200 uppercase">Restart loop</div>
          <p className="mt-1.5 text-[11px] text-amber-100/95 leading-relaxed">
            Docker keeps starting this ROS container and it exits immediately each time. Check{" "}
            <span className="font-mono text-amber-200">docker logs</span> on the Pi for the repeating error. The stack
            table row below is highlighted.
          </p>
        </div>
      ) : null}

      <div className="overflow-x-auto rounded-xl border border-slate-700/80 bg-black/35">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-slate-700/80 text-slate-500 font-mono uppercase tracking-wide">
              <th className="p-2.5 w-[44%]">Layer</th>
              <th className="p-2.5 w-24">State</th>
              <th className="p-2.5">Detail</th>
            </tr>
          </thead>
          <tbody>
            {(stack.layers ?? []).map((row) => (
              <tr
                key={row.id}
                className={
                  row.id === "ros_container" && restartLoop
                    ? "border-b border-amber-900/50 bg-amber-950/25 last:border-0"
                    : "border-b border-slate-800/80 last:border-0"
                }
              >
                <td className="p-2.5 align-top text-slate-200 font-medium">{row.title}</td>
                <td className="p-2.5 align-top">{layerStateBadge(row.ok, row.id, restartLoop)}</td>
                <td className="p-2.5 align-top text-slate-400 leading-snug">{row.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 font-mono text-[10px] text-slate-400 space-y-1">
          <div className="text-slate-500 font-bold uppercase tracking-wide mb-2">TCP from this PC</div>
          <div>
            <span className="text-slate-500">:22</span>{" "}
            {g.tcp_ssh_port_22?.ok ? (
              <span className="text-emerald-400">open</span>
            ) : (
              <span className="text-red-400">closed ({g.tcp_ssh_port_22?.error ?? "?"})</span>
            )}
          </div>
          <div>
            <span className="text-slate-500">:{g.rosbridge_tcp_port} (rosbridge)</span>{" "}
            {g.tcp_rosbridge_port?.ok ? (
              <span className="text-emerald-400">open</span>
            ) : (
              <span className="text-red-400">closed ({g.tcp_rosbridge_port?.error ?? "?"})</span>
            )}
          </div>
          <p className="text-slate-500 pt-1 leading-relaxed">{g.summary}</p>
        </div>

        <div className="rounded-lg border border-slate-800 bg-slate-950/50 p-3 font-mono text-[10px] text-slate-400 space-y-1">
          <div className="text-slate-500 font-bold uppercase tracking-wide mb-2">Pi &amp; Docker</div>
          <div>
            <span className="text-slate-500">hostname</span> {pi.hostname ?? "—"}
          </div>
          <div>
            <span className="text-slate-500">primary IP</span> {pi.primary_ip ?? "—"}
          </div>
          <div>
            <span className="text-slate-500">Wi‑Fi</span>{" "}
            <span className="text-slate-300">{pi.wifi?.state ?? "—"}</span>
            {pi.wifi?.ssid ? (
              <>
                {" "}
                <span className="text-indigo-300">SSID {pi.wifi.ssid}</span>
              </>
            ) : null}
          </div>
          <div>
            <span className="text-slate-500">docker systemd</span>{" "}
            <span className={dk.systemd_active === "active" ? "text-emerald-400" : "text-amber-400"}>
              {dk.systemd_active}
            </span>
            {dk.server_version ? (
              <>
                {" "}
                <span className="text-slate-500">engine</span> {dk.server_version}
              </>
            ) : null}
          </div>
          <div>
            <span className="text-slate-500">container</span> {ctr.name}{" "}
            <span className={ctr.running ? "text-emerald-400" : restartLoop ? "text-amber-200 font-semibold" : "text-amber-300"}>
              {ctr.docker_state}
            </span>
            {restartLoop ? (
              <span className="ml-2 inline-block rounded px-1.5 py-0.5 text-[9px] font-black uppercase tracking-wide bg-amber-600/30 text-amber-200 border border-amber-500/50">
                restart loop
              </span>
            ) : null}
            {ctr.exit_code != null ? (
              <>
                {" "}
                <span className="text-slate-500">exit</span>{" "}
                <span className={ctr.exit_code === 137 ? "text-red-400" : "text-slate-300"}>{ctr.exit_code}</span>
              </>
            ) : null}
            {ctr.oom_killed ? (
              <>
                {" "}
                <span className="text-red-400">OOM</span>
              </>
            ) : null}
          </div>
          {ctr.alternate_running_container ? (
            <p className="text-amber-300/90 leading-relaxed pt-1">
              Another container <span className="text-amber-200">{ctr.alternate_running_container}</span> is Up —
              set <span className="text-slate-300">YAHBOOM_ROS2_CONTAINER</span> if the app is probing the wrong name.
            </p>
          ) : null}
          {ctr.lifecycle?.label ? (
            <div
              className={
                restartLoop
                  ? "mt-2 space-y-1 rounded-md border border-amber-600/45 bg-amber-950/30 px-2.5 py-2"
                  : "mt-2 pt-2 border-t border-slate-800/90 space-y-1"
              }
            >
              <div className={restartLoop ? "text-amber-500/95 uppercase tracking-wide font-bold" : "text-slate-500 uppercase tracking-wide"}>
                Run history{restartLoop ? " · restart loop" : ""}
              </div>
              <div className="text-slate-100 font-medium leading-snug">{ctr.lifecycle.label}</div>
              <p className={restartLoop ? "text-amber-100/85 leading-relaxed" : "text-slate-400 leading-relaxed"}>{ctr.lifecycle.detail}</p>
            </div>
          ) : null}
        </div>
      </div>

      {(ctr.docker_logs_preview || ctr.docker_logs_error) && (
        <div className="rounded-lg border border-slate-600/60 bg-slate-950/60 p-3 space-y-2">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
            Docker log preview
            {ctr.docker_logs_truncated ? (
              <span className="ml-2 font-mono normal-case text-amber-400/90">(truncated)</span>
            ) : null}
            {ctr.docker_logs_lines_fetched ? (
              <span className="ml-2 font-mono normal-case text-slate-500">
                ~{ctr.docker_logs_lines_fetched} lines
              </span>
            ) : null}
          </div>
          {ctr.docker_logs_error ? (
            <p className="text-[10px] text-red-300/95 font-mono leading-relaxed">{ctr.docker_logs_error}</p>
          ) : null}
          {ctr.docker_logs_preview ? (
            <pre className="text-[9px] text-slate-300 whitespace-pre-wrap font-mono leading-relaxed max-h-64 overflow-y-auto border border-slate-800/90 rounded p-2 bg-black/45">
              {ctr.docker_logs_preview}
            </pre>
          ) : null}
        </div>
      )}

      {(ctr.remediation_steps && ctr.remediation_steps.length > 0) || ctr.docker_ps_preview ? (
        <div className="rounded-lg border border-amber-900/50 bg-amber-950/20 p-3 space-y-2">
          <div className="text-[10px] font-bold text-amber-600/90 uppercase tracking-wide">
            ROS container{restartLoop ? " · restart loop" : ""}
          </div>
          {ctr.remediation_steps && ctr.remediation_steps.length > 0 ? (
            <ul className="text-[10px] text-amber-100/90 list-disc pl-4 space-y-1 leading-relaxed">
              {ctr.remediation_steps.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          ) : null}
          {ctr.docker_ps_preview ? (
            <pre className="text-[9px] text-slate-500 whitespace-pre-wrap font-mono leading-relaxed max-h-36 overflow-y-auto border border-slate-800/80 rounded p-2 bg-black/30">
              {ctr.docker_ps_preview}
            </pre>
          ) : null}
        </div>
      ) : null}

      {(pi.interfaces_preview || pi.wifi?.raw_preview) && (
        <div className="rounded-lg border border-slate-800 bg-black/40 p-3">
          <div className="text-[10px] font-bold text-slate-500 uppercase tracking-wide mb-2">
            Pi interfaces (preview)
          </div>
          {pi.interfaces_preview ? (
            <pre className="text-[10px] text-slate-400 whitespace-pre-wrap font-mono leading-relaxed max-h-32 overflow-y-auto">
              {pi.interfaces_preview}
            </pre>
          ) : null}
          {pi.wifi?.raw_preview ? (
            <pre className="text-[10px] text-slate-500 whitespace-pre-wrap font-mono leading-relaxed max-h-24 overflow-y-auto mt-2">
              {pi.wifi.raw_preview}
            </pre>
          ) : null}
        </div>
      )}

      <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3 font-mono text-[10px] text-slate-400">
        <span className="text-slate-500">rosbridge WebSocket (this app)</span>{" "}
        <span className={rb.websocket_to_rosbridge === "connected" ? "text-emerald-400" : "text-red-400"}>
          {rb.websocket_to_rosbridge}
        </span>
        {" · "}
        <span className="text-slate-500">cmd_vel on bridge</span>{" "}
        {rb.cmd_vel_advertised_on_bridge ? (
          <span className="text-emerald-400">yes</span>
        ) : (
          <span className="text-amber-400">no</span>
        )}
      </div>
    </div>
  );
}
