import { useRef, useEffect, useState, Suspense, useMemo } from 'react'
import { Canvas, useFrame, useLoader } from '@react-three/fiber'
import { OrbitControls, Grid, Environment, Text, Line } from '@react-three/drei'
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js'
import * as THREE from 'three'
import { motion } from 'framer-motion'
import { Box, Activity, Compass, Battery, Wifi, WifiOff } from 'lucide-react'

// ─────────────────────────────────────────────────────────────────────────────
// Telemetry polling hook
// ─────────────────────────────────────────────────────────────────────────────
interface TelemetryData {
    battery?: number
    imu?: { heading: number }
    velocity?: { linear: number; angular: number }
}

function useTelemetry() {
    const [data, setData] = useState<TelemetryData | null>(null)
    const [connected, setConnected] = useState(false)

    useEffect(() => {
        let alive = true
        const poll = async () => {
            try {
                const r = await fetch('http://localhost:10792/api/v1/telemetry', { signal: AbortSignal.timeout(1500) })
                if (!alive) return
                const j = await r.json()
                if (!j.error && j.battery !== undefined) {
                    setData(j)
                    setConnected(true)
                } else {
                    setConnected(false)
                }
            } catch {
                if (alive) setConnected(false)
            }
        }
        poll()
        const id = setInterval(poll, 800)
        return () => { alive = false; clearInterval(id) }
    }, [])

    return { data, connected }
}

// ─────────────────────────────────────────────────────────────────────────────
// URDF-derived constants (in metres)
// Source: automaticaddison/yahboom_rosmaster URDF
// ─────────────────────────────────────────────────────────────────────────────
const WHEEL_RADIUS = 0.0325
const WHEEL_X_OFF = 0.08
const WHEEL_Y_HALF = 0.169 / 2 + (-0.01)  // 0.0745m

// ─────────────────────────────────────────────────────────────────────────────
// STL mesh helper — loads one STL file and returns a mesh with material
// ─────────────────────────────────────────────────────────────────────────────
function StlPart({
    url,
    color = '#3a3a5c',
    metalness = 0.4,
    roughness = 0.6,
    position = [0, 0, 0] as [number, number, number],
    rotation = [0, 0, 0] as [number, number, number],
    scale = 1,
    emissive,
    emissiveIntensity = 0,
}: {
    url: string
    color?: string
    metalness?: number
    roughness?: number
    position?: [number, number, number]
    rotation?: [number, number, number]
    scale?: number
    emissive?: string
    emissiveIntensity?: number
}) {
    const geometry = useLoader(STLLoader, url)
    const mat = useMemo(() => new THREE.MeshStandardMaterial({
        color,
        metalness,
        roughness,
        emissive: emissive ? new THREE.Color(emissive) : undefined,
        emissiveIntensity,
    }), [color, metalness, roughness, emissive, emissiveIntensity])

    return (
        <mesh
            geometry={geometry}
            material={mat}
            position={position}
            rotation={rotation}
            scale={scale}
            castShadow
            receiveShadow
        />
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Single spinning wheel (loads real STL, spins on X axis)
// URDF visual origin rpy = pi/2, 0, 0
// ─────────────────────────────────────────────────────────────────────────────
function WheelMesh({
    url,
    position,
    spin,
    flip = false,
}: {
    url: string
    position: [number, number, number]
    spin: number
    flip?: boolean
}) {
    const groupRef = useRef<THREE.Group>(null!)
    useFrame((_, delta) => {
        groupRef.current.rotation.y += delta * spin
    })
    return (
        <group ref={groupRef} position={position}>
            {/* URDF visual rpy = pi/2,0,0  +  optional y-flip for left/right mirror */}
            <StlPart
                url={url}
                rotation={[Math.PI / 2, 0, flip ? Math.PI : 0]}
                color="#222222"
                metalness={0.3}
                roughness={0.8}
            />
        </group>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// LIDAR: real STL + spinning beam overlay
// URDF: xyz_offset 0 0 0.0825, mesh_rpy_offset -pi/2 0 0
// ─────────────────────────────────────────────────────────────────────────────
function LidarMesh() {
    const beamRef = useRef<THREE.Mesh>(null!)
    useFrame((_, delta) => {
        beamRef.current.rotation.y += delta * 5
    })
    return (
        <group position={[0, 0.1, 0.0825]}>
            <StlPart
                url="/assets/meshes/laser_link.STL"
                rotation={[-Math.PI / 2, 0, 0]}
                color="#1a1a2e"
                metalness={0.8}
                roughness={0.2}
            />
            {/* Spinning laser beam — layered on top */}
            <mesh ref={beamRef} position={[0, 0.01, 0]}>
                <mesh position={[0.08, 0, 0]} rotation={[0, 0, Math.PI / 2]}>
                    <cylinderGeometry args={[0.001, 0.001, 0.16, 4]} />
                    <meshStandardMaterial
                        color="#ff0000"
                        emissive="#ff0000"
                        emissiveIntensity={4}
                        transparent
                        opacity={0.8}
                    />
                </mesh>
            </mesh>
        </group>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Camera: real STL
// URDF: xyz_offset 0.105 0 0.05 from base_link, rpy -0.50 rad pitch
// ─────────────────────────────────────────────────────────────────────────────
function CameraMesh() {
    return (
        <group position={[0.105, 0.1, 0.05]} rotation={[0, -0.5, 0]}>
            <StlPart
                url="/assets/meshes/camera_link.STL"
                color="#111111"
                metalness={0.6}
                roughness={0.4}
            />
            {/* Lens glow */}
            <mesh position={[0.002, 0, 0.02]}>
                <circleGeometry args={[0.008, 12]} />
                <meshStandardMaterial color="#001133" emissive="#00aaff" emissiveIntensity={0.7} />
            </mesh>
        </group>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Full robot assembled from real STL parts + URDF joint positions
// base_footprint → base_link: z = +wheel_radius = 0.0325
// ─────────────────────────────────────────────────────────────────────────────
function G1Robot({ yaw, linearVel }: { yaw: number; linearVel: number }) {
    const rootRef = useRef<THREE.Group>(null!)
    const targetYaw = useRef(yaw)

    useEffect(() => { targetYaw.current = (yaw * Math.PI) / 180 }, [yaw])

    useFrame((_, delta) => {
        rootRef.current.rotation.y = THREE.MathUtils.lerp(
            rootRef.current.rotation.y,
            targetYaw.current,
            delta * 4
        )
        rootRef.current.position.y = Math.sin(Date.now() * 0.001) * 0.005
    })

    const wheelSpin = linearVel * 20

    // Wheel positions from URDF joint xyz (relative to base_link):
    // x = x_reflect * 0.08, y = y_reflect * 0.0745, z = -wheel_radius = -0.0325
    // base_link is at z = WHEEL_RADIUS above ground, so wheels sit at z=0
    return (
        <group ref={rootRef}>
            {/* ── Base body ─────────────────────────────────── */}
            <StlPart
                url="/assets/meshes/base_link_X3.STL"
                position={[0, WHEEL_RADIUS, 0]}
                color="#1e3a5f"
                metalness={0.5}
                roughness={0.5}
            />

            {/* ── Indigo accent top-plate glow ──────────────── */}
            <mesh position={[0, 0.14, 0]}>
                <boxGeometry args={[0.28, 0.003, 0.16]} />
                <meshStandardMaterial color="#6366f1" emissive="#6366f1" emissiveIntensity={0.8} transparent opacity={0.6} />
            </mesh>

            {/* ── LIDAR ──────────────────────────────────────── */}
            <LidarMesh />

            {/* ── Camera ─────────────────────────────────────── */}
            <CameraMesh />

            {/* ── Wheels (URDF joint positions) ─────────────── */}
            {/* front_left:  x=+0.08, y=+0.0745, z=−0.0325 */}
            <WheelMesh
                url="/assets/meshes/front_left_wheel_X3.STL"
                position={[WHEEL_X_OFF, 0, WHEEL_Y_HALF]}
                spin={wheelSpin}
            />
            {/* front_right: x=+0.08, y=−0.0745, z=−0.0325 */}
            <WheelMesh
                url="/assets/meshes/front_right_wheel_X3.STL"
                position={[WHEEL_X_OFF, 0, -WHEEL_Y_HALF]}
                spin={-wheelSpin}
                flip
            />
            {/* back_left:   x=−0.08, y=+0.0745, z=−0.0325 */}
            <WheelMesh
                url="/assets/meshes/back_left_wheel_X3.STL"
                position={[-WHEEL_X_OFF, 0, WHEEL_Y_HALF]}
                spin={wheelSpin}
            />
            {/* back_right:  x=−0.08, y=−0.0745, z=−0.0325 */}
            <WheelMesh
                url="/assets/meshes/back_right_wheel_X3.STL"
                position={[-WHEEL_X_OFF, 0, -WHEEL_Y_HALF]}
                spin={-wheelSpin}
                flip
            />

            {/* ── Heading arrow ─────────────────────────────── */}
            <Line
                points={[[0, 0.15, 0], [0, 0.15, 0.25]]}
                color="#6366f1"
                lineWidth={2}
            />
        </group>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Ground plane with grid
// ─────────────────────────────────────────────────────────────────────────────
function Floor() {
    return (
        <>
            <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.001, 0]} receiveShadow>
                <planeGeometry args={[8, 8]} />
                <meshStandardMaterial color="#080810" />
            </mesh>
            <Grid
                position={[0, 0, 0]}
                args={[8, 8]}
                cellSize={0.25}
                cellThickness={0.4}
                cellColor="#1e1e3a"
                sectionSize={1}
                sectionThickness={0.8}
                sectionColor="#2d2d6a"
                fadeDistance={6}
                fadeStrength={1.5}
                infiniteGrid
            />
        </>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Axis labels
// ─────────────────────────────────────────────────────────────────────────────
function AxisLabels() {
    return (
        <>
            <Text position={[1.5, 0.02, 0]} fontSize={0.08} color="#ef4444" anchorX="center" anchorY="middle">+X</Text>
            <Text position={[0, 0.02, 1.5]} fontSize={0.08} color="#22d3ee" anchorX="center" anchorY="middle">+Z</Text>
        </>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// Loading fallback — coloured ghost chassis while STLs stream in
// ─────────────────────────────────────────────────────────────────────────────
function RobotFallback() {
    return (
        <group>
            <mesh position={[0, 0.08, 0]}>
                <boxGeometry args={[0.28, 0.1, 0.18]} />
                <meshStandardMaterial color="#1e3a5f" transparent opacity={0.4} wireframe />
            </mesh>
            <Text position={[0, 0.25, 0]} fontSize={0.04} color="#6366f1" anchorX="center">
                Loading meshes…
            </Text>
        </group>
    )
}

// ─────────────────────────────────────────────────────────────────────────────
// HUD stat pill
// ─────────────────────────────────────────────────────────────────────────────
const Stat = ({ icon: Icon, label, value, color }: { icon: React.ComponentType<{ size?: number; className?: string }>; label: string; value: string; color: string }) => (
    <div className="flex items-center gap-2 px-4 py-2.5 rounded-xl border bg-black/60 backdrop-blur border-white/10">
        <Icon size={14} className={`text-${color}-400 flex-shrink-0`} />
        <div>
            <div className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">{label}</div>
            <div className={`text-sm font-bold text-${color}-300 tabular-nums`}>{value}</div>
        </div>
    </div>
)

// ─────────────────────────────────────────────────────────────────────────────
// Main page
// ─────────────────────────────────────────────────────────────────────────────
const Viz = () => {
    const { data, connected } = useTelemetry()
    const yaw = data?.imu?.heading ?? 0
    const battery = data?.battery ?? 0
    const linearVel = data?.velocity?.linear ?? 0
    const angularVel = data?.velocity?.angular ?? 0

    return (
        <div className="flex flex-col" style={{ height: 'calc(100vh - 120px)' }}>
            {/* Header */}
            <div className="flex items-center justify-between px-1 pb-4">
                <div className="flex items-center gap-3">
                    <Box className="text-indigo-400 w-6 h-6" />
                    <div>
                        <h1 className="text-2xl font-bold text-white tracking-tight">3D Visualization</h1>
                        <p className="text-slate-400 text-xs">
                            ROSMASTER X3 — real STL meshes from URDF
                            {' · '}
                            <a
                                href="https://github.com/automaticaddison/yahboom_rosmaster"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-indigo-400 hover:underline"
                            >
                                source
                            </a>
                        </p>
                    </div>
                </div>
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs font-bold uppercase tracking-widest ${connected
                    ? 'border-green-500/40 bg-green-500/10 text-green-400'
                    : 'border-amber-500/40 bg-amber-500/10 text-amber-400'
                    }`}>
                    {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
                    {connected ? 'Live' : 'Simulated'}
                </div>
            </div>

            {/* 3D Canvas */}
            <div className="flex-1 rounded-2xl overflow-hidden border border-white/10 bg-[#050508] relative min-h-0">
                <Canvas
                    shadows
                    camera={{ position: [0.5, 0.4, 0.8], fov: 45, near: 0.001, far: 50 }}
                    gl={{ antialias: true }}
                >
                    <color attach="background" args={['#050508']} />
                    <fog attach="fog" args={['#050508', 3, 10]} />

                    {/* Lighting: key + fill + rim so robot reads clearly */}
                    <ambientLight intensity={0.55} />
                    <hemisphereLight args={['#404060', '#0a0a12', 0.6]} />
                    <directionalLight
                        position={[1.2, 1.8, 1.2]}
                        intensity={2.2}
                        castShadow
                        shadow-mapSize={[1024, 1024]}
                        shadow-bias={-0.0001}
                    />
                    <directionalLight position={[-0.8, 0.6, -0.6]} intensity={0.7} />
                    <pointLight position={[-0.5, 0.5, -0.5]} intensity={0.6} color="#6366f1" />
                    <pointLight position={[0.5, 0.25, 0.5]} intensity={0.4} color="#93c5fd" />

                    <Suspense fallback={<RobotFallback />}>
                        <Environment preset="night" />
                        <Floor />
                        <AxisLabels />
                        <G1Robot yaw={yaw} linearVel={linearVel} />
                    </Suspense>

                    <OrbitControls
                        enablePan
                        enableZoom
                        enableRotate
                        minDistance={0.2}
                        maxDistance={3}
                        minPolarAngle={0.05}
                        maxPolarAngle={Math.PI / 2.1}
                        dampingFactor={0.08}
                        enableDamping
                    />
                </Canvas>

                {/* Controls hint */}
                <div className="absolute bottom-3 right-3 text-[10px] text-slate-600 font-medium">
                    Left drag = orbit · Scroll = zoom · Right drag = pan
                </div>
            </div>

            {/* HUD strip */}
            <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 pt-4 flex-wrap"
            >
                <Stat icon={Compass} label="Heading" value={`${yaw.toFixed(1)}°`} color="indigo" />
                <Stat icon={Battery} label="Battery" value={`${battery.toFixed(0)}%`} color={battery < 20 ? 'red' : 'green'} />
                <Stat icon={Activity} label="Lin. Vel" value={`${linearVel.toFixed(2)} m/s`} color="cyan" />
                <Stat icon={Activity} label="Ang. Vel" value={`${angularVel.toFixed(2)} r/s`} color="purple" />
            </motion.div>
        </div>
    )
}

export default Viz
