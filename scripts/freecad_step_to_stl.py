"""Convert STEP using FreeCAD Gui-aware import."""
import FreeCAD, FreeCADGui, Import, Mesh, os

# Must enable Gui for proper STEP assembly import
try:
    FreeCADGui.showMainWindow(False)
except:
    pass

STEP = r"C:\Users\sandr\AppData\Local\Temp\raspbot_v2_step.STEP"
OUT = r"D:\Dev\repos\yahboom-mcp\webapp\public\assets\meshes"
os.makedirs(OUT, exist_ok=True)

# Use openDocument which triggers proper import pipeline
print("Opening STEP...", flush=True)
doc = FreeCAD.openDocument(STEP)
doc.recompute()
print(f"Objects: {len(doc.Objects)}", flush=True)

for i, obj in enumerate(doc.Objects):
    name = obj.Label or f"part_{i}"
    safe = "".join(c for c in name if c.isalnum() or c in "_-_.").strip() or f"part_{i:02d}"
    path = os.path.join(OUT, f"boomy_{i:02d}_{safe}.stl")
    try:
        Mesh.export([obj], path)
        sz = os.path.getsize(path) / 1024
        print(f"  [{i}] {name} — {sz:.0f} KB", flush=True)
    except Exception as e:
        print(f"  [{i}] {name} — {e}", flush=True)

FreeCAD.closeDocument(doc.Name)
print("Done.", flush=True)
