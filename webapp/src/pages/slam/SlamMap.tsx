import { AlertTriangle, Compass, Layers, RefreshCw, Target } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { api } from "../../lib/api";

const MAP_POLL_MS = 5000;
const DATA_POLL_MS = 500;

const SlamMap: React.FC = () => {
	const navigate = useNavigate();
	const canvasRef = useRef<HTMLCanvasElement>(null);
	const mapImgRef = useRef<HTMLImageElement | null>(null);
	const [mapReady, setMapReady] = useState(false);
	const [data, setData] = useState<{
		robot: { x: number; y: number; heading: number };
		scan_points: { x: number; y: number }[];
		map_available: boolean;
	} | null>(null);
	const [scale, setScale] = useState(1);
	const [mapDims, setMapDims] = useState({ w: 0, h: 0 });
	const [showScan, setShowScan] = useState(true);
	const [connected, setConnected] = useState(false);

	// Load map image
	useEffect(() => {
		let alive = true;
		const loadMap = async () => {
			try {
				const url = api.getSlamMapUrl();
				const res = await fetch(url);
				if (!res.ok) {
					if (alive) setMapReady(false);
					return;
				}
				const blob = await res.blob();
				if (!alive) return;
				const img = new Image();
				img.onload = () => {
					if (!alive) return;
					mapImgRef.current = img;
					setMapDims({ w: img.naturalWidth, h: img.naturalHeight });
					setMapReady(true);
				};
				img.src = URL.createObjectURL(blob);
			} catch {
				if (alive) setMapReady(false);
			}
		};
		loadMap();
		const id = setInterval(loadMap, MAP_POLL_MS);
		return () => {
			alive = false;
			clearInterval(id);
		};
	}, []);

	// Poll pose + scan data
	useEffect(() => {
		let alive = true;
		const poll = async () => {
			try {
				const d = await api.getSlamData();
				if (!alive) return;
				setData({
					robot: d.robot,
					scan_points: d.scan_points,
					map_available: d.map_available,
				});
				setConnected(d.success ?? false);
				if (d.map_available && !mapReady) {
					setMapDims({ w: d.width, h: d.height });
				}
			} catch {
				if (alive) setConnected(false);
			}
		};
		poll();
		const id = setInterval(poll, DATA_POLL_MS);
		return () => {
			alive = false;
			clearInterval(id);
		};
	}, [mapReady]);

	// Render overlay canvas
	useEffect(() => {
		const canvas = canvasRef.current;
		if (!canvas) return;
		const ctx = canvas.getContext("2d");
		if (!ctx) return;

		const img = mapImgRef.current;
		const cw = img ? img.naturalWidth : mapDims.w || 800;
		const ch = img ? img.naturalHeight : mapDims.h || 800;
		canvas.width = cw;
		canvas.height = ch;

		ctx.clearRect(0, 0, cw, ch);

		// Draw map as background
		if (img) {
			ctx.drawImage(img, 0, 0, cw, ch);
		}

		if (!data) return;

		const { robot, scan_points } = data;
		const res = 0.05; // metres per pixel (standard)

		// Convert robot world coords to pixel coords
		const originX = cw / 2;
		const originY = ch / 2;

		const rpx = originX + robot.x / res;
		const rpy = originY - robot.y / res;

		// Draw LIDAR scan points
		if (showScan && scan_points.length > 0) {
			ctx.fillStyle = "rgba(99, 102, 241, 0.5)";
			for (const p of scan_points) {
				const px = originX + p.x / res;
				const py = originY - p.y / res;
				if (px >= 0 && px < cw && py >= 0 && py < ch) {
					ctx.fillRect(px - 1, py - 1, 3, 3);
				}
			}
		}

		// Draw robot heading arrow
		const headingRad = (robot.heading * Math.PI) / 180;
		const arrowLen = Math.max(20, cw * 0.03);

		ctx.beginPath();
		ctx.arc(rpx, rpy, 8, 0, Math.PI * 2);
		ctx.fillStyle = "#6366f1";
		ctx.fill();
		ctx.strokeStyle = "#a5b4fc";
		ctx.lineWidth = 2;
		ctx.stroke();

		const tipX = rpx + arrowLen * Math.sin(headingRad);
		const tipY = rpy - arrowLen * Math.cos(headingRad);
		ctx.beginPath();
		ctx.moveTo(rpx, rpy);
		ctx.lineTo(tipX, tipY);
		ctx.strokeStyle = "#22d3ee";
		ctx.lineWidth = 3;
		ctx.stroke();
	}, [data, mapReady, showScan, mapDims]);

	// Zoom controls
	const zoomIn = useCallback(() => setScale((s) => Math.min(s + 0.25, 4)), []);
	const zoomOut = useCallback(() => setScale((s) => Math.max(s - 0.25, 0.25)), []);
	const resetZoom = useCallback(() => setScale(1), []);

	const noMap = !mapReady && data?.map_available === false;

	return (
		<div className="flex flex-col h-full py-4 px-4 sm:px-6 max-w-6xl mx-auto">
			{/* Header */}
			<div className="flex items-center justify-between mb-4">
				<div className="flex items-center gap-4">
					<Layers className="text-indigo-400 w-8 h-8" />
					<div>
						<h1 className="text-2xl font-bold text-white tracking-tight">SLAM Map</h1>
						<p className="text-slate-400 text-sm">
							Real-time occupancy grid from slam_toolbox with robot pose + LIDAR overlay
						</p>
					</div>
				</div>
				<div className="flex items-center gap-2">
					{connected ? (
						<span className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-green-500/40 bg-green-500/10 text-green-400 text-xs font-bold uppercase">
							<Compass size={12} /> Live
						</span>
					) : (
						<span className="flex items-center gap-2 px-3 py-1.5 rounded-xl border border-amber-500/40 bg-amber-500/10 text-amber-400 text-xs font-bold uppercase">
							<AlertTriangle size={12} /> Offline
						</span>
					)}
				</div>
			</div>

			{noMap && (
				<div className="mb-4 rounded-2xl border border-amber-500/30 bg-amber-950/20 p-4">
					<div className="flex items-center gap-3">
						<AlertTriangle className="text-amber-400 w-5 h-5 flex-shrink-0" />
						<div>
							<p className="text-amber-300 font-semibold text-sm">
								No map data yet
							</p>
							<p className="text-slate-400 text-xs mt-1">
								Run the "explore_and_map" mission to start mapping, or verify
								slam_toolbox is publishing /map.
							</p>
						</div>
						<button
							type="button"
							onClick={() => navigate("/missions")}
							className="ml-auto px-4 py-2 rounded-xl border border-indigo-500/30 bg-indigo-500/10 text-indigo-300 hover:bg-indigo-500/20 text-sm font-medium"
						>
							Go to Missions
						</button>
					</div>
				</div>
			)}

			{/* Map canvas */}
			<div
				className="relative flex-1 bg-[#0f0f12]/80 border border-white/10 rounded-2xl p-4 overflow-auto min-h-0"
			>
				<div
					style={{
						transform: `scale(${scale})`,
						transformOrigin: "top left",
					}}
				>
					<canvas
						ref={canvasRef}
						className="rounded-xl border border-white/5 bg-[#0a0a0e]"
						style={{ imageRendering: "pixelated" }}
					/>
				</div>

				{/* Zoom controls overlay */}
				<div className="absolute bottom-4 right-4 flex flex-col gap-1">
					<button
						type="button"
						onClick={zoomIn}
						className="w-9 h-9 rounded-lg bg-[#1e1e2e] border border-white/10 text-white hover:bg-[#2e2e3e] text-lg font-bold"
					>
						+
					</button>
					<button
						type="button"
						onClick={zoomOut}
						className="w-9 h-9 rounded-lg bg-[#1e1e2e] border border-white/10 text-white hover:bg-[#2e2e3e] text-lg font-bold"
					>
						−
					</button>
					<button
						type="button"
						onClick={resetZoom}
						className="w-9 h-9 rounded-lg bg-[#1e1e2e] border border-white/10 text-white hover:bg-[#2e2e3e] text-xs font-bold"
					>
						1:1
					</button>
				</div>
			</div>

			{/* Controls bar */}
			<div className="mt-4 flex items-center justify-between">
				<div className="flex items-center gap-4 text-slate-400 text-sm">
					{data && (
						<>
							<span>
								Robot:{" "}
								<span className="text-white font-mono">
									({data.robot.x.toFixed(2)}, {data.robot.y.toFixed(2)}){" "}
									{data.robot.heading.toFixed(1)}°
								</span>
							</span>
							<span>
								Scan pts:{" "}
								<span className="text-white font-mono">{data.scan_points.length}</span>
							</span>
						</>
					)}
				</div>
				<div className="flex gap-2">
					<button
						type="button"
						onClick={() => setShowScan((s) => !s)}
						className={`flex items-center gap-2 px-3 py-2 rounded-xl border text-sm font-medium transition-colors ${
							showScan
								? "border-indigo-500/30 bg-indigo-500/10 text-indigo-300"
								: "border-white/10 bg-white/5 text-slate-400"
						}`}
					>
						<Target size={14} />
						Scan overlay
					</button>
					<button
						type="button"
						onClick={() => navigate("/missions")}
						className="flex items-center gap-2 px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-slate-400 hover:text-slate-200 hover:bg-white/10 text-sm"
					>
						<RefreshCw size={14} />
						Start mapping
					</button>
				</div>
			</div>
		</div>
	);
};

export default SlamMap;
