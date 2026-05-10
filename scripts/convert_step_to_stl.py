"""Convert STEP to STL using trimesh."""
import trimesh, os
STEP = r"C:\Users\sandr\Downloads\5.3D_Model_File-20260507T061121Z-3-001\5.3D_Model_File\Raspbot-V2.STEP"
OUT = r"D:\Dev\repos\yahboom-mcp\webapp\public\assets\meshes"
os.makedirs(OUT, exist_ok=True)

print("Loading...", flush=True)
m = trimesh.load(STEP, force=None)
print(f"Type: {type(m).__name__}", flush=True)

if isinstance(m, trimesh.Scene):
    print(f"Scene with {len(m.geometry)} geometries", flush=True)
    for i, (name, geom) in enumerate(m.geometry.items()):
        safe = "".join(c for c in name if c.isalnum() or c in "_-").strip() or f"part_{i}"
        p = os.path.join(OUT, f"boomy_{i:02d}_{safe}.stl")
        geom.export(p)
        print(f"  {os.path.basename(p)} — {os.path.getsize(p)/1024:.0f} KB", flush=True)
elif hasattr(m, "export"):
    m.export(os.path.join(OUT, "boomy.stl"))
    sz = os.path.getsize(os.path.join(OUT, "boomy.stl")) / 1024
    print(f"  boomy.stl — {sz:.0f} KB", flush=True)
elif isinstance(m, dict):
    for name, geom in m.items():
        p = os.path.join(OUT, f"{name}.stl")
        geom.export(p)
        print(f"  {name}.stl", flush=True)
print("Done.", flush=True)
