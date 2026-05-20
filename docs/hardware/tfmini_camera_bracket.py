"""FreeCAD bracket: TFmini-S on top of PTZ camera module.

Run in FreeCAD Python console or:
  freecadcmd tfmini_camera_bracket.py

Output: tfmini_camera_bracket.stl

Dimensions:
- Camera module: 25 x 25 x 20mm (generic USB camera)
- TFmini-S:      42 x 15 x 16mm
- Screws:        M2.5 holes, 4x at corners of camera module
"""
import FreeCAD, Part, Mesh, math

DOC = FreeCAD.newDocument("TFminiBracket")

# ── Parameters ──────────────────────────────────────────────────────────────
CAM_W, CAM_D, CAM_H = 25, 25, 20   # camera module
TFM_W, TFM_D, TFM_H = 42, 15, 16   # TFmini-S
WALL = 2.0                          # wall thickness
GAP = 1.0                           # gap between cam and tfmini plate
LENS_HOLE_D = 12                    # camera lens hole diameter
MTG_HOLE_D = 2.5                    # M2.5 screw hole

# Compute overall bracket size
BASE_W = max(CAM_W, TFM_W) + 2 * WALL
BASE_D = CAM_D + 2 * WALL
BASE_H = WALL                        # base plate thickness
TFM_PLATE_H = WALL + GAP + TFM_H    # height of tfmini platform above base

# ── Helper ──────────────────────────────────────────────────────────────────
def box(name, x, y, z, w, d, h):
    """Create a box with position offset."""
    b = Part.makeBox(w, d, h)
    b.translate(FreeCAD.Vector(x, y, z))
    return b

def cylinder(name, x, y, z, r, h):
    """Create a cylinder."""
    c = Part.Circle()
    c.Radius = r / 2
    c.Center = FreeCAD.Vector(0, 0, 0)
    c.Axis = FreeCAD.Vector(0, 0, 1)
    w = c.toShape().extrude(FreeCAD.Vector(0, 0, h))
    w.translate(FreeCAD.Vector(x, y, z))
    return w

# ── Base shape: solid block ─────────────────────────────────────────────────
solid = box("base", 0, 0, 0, BASE_W, BASE_D, TFM_PLATE_H)

# ── Cut: camera recess (for the camera body) ────────────────────────────────
# Center the camera recess
cam_x = (BASE_W - CAM_W) / 2
cam_y = (BASE_D - CAM_D) / 2
cam_cut = box("cam_cut", cam_x, cam_y, 0, CAM_W, CAM_D, CAM_H)
solid = solid.cut(cam_cut)

# ── Cut: lens hole ──────────────────────────────────────────────────────────
# Lens hole goes through the back wall of the camera recess
hole = cylinder("lens_hole", cam_x + CAM_W / 2, cam_y, LENS_HOLE_D / 2, LENS_HOLE_D, WALL)
solid = solid.cut(hole)

# ── Cut: TFmini-S platform on top of camera ─────────────────────────────────
# The TFmini sits on top of the camera, centered over it
tfm_x = (BASE_W - TFM_W) / 2
tfm_y = (BASE_D - TFM_D) / 2
tfm_cut = box("tfm_cut", tfm_x, tfm_y, WALL + GAP, TFM_W, TFM_D, TFM_H)
solid = solid.cut(tfm_cut)

# ── Cut: M2.5 mounting holes at 4 corners of camera ─────────────────────────
hole_offsets = [
    (cam_x + 3, cam_y + 3),
    (cam_x + CAM_W - 3, cam_y + 3),
    (cam_x + 3, cam_y + CAM_D - 3),
    (cam_x + CAM_W - 3, cam_y + CAM_D - 3),
]
for hx, hy in hole_offsets:
    hole = cylinder("hole", hx, hy, 0, MTG_HOLE_D, BASE_H + GAP)
    solid = solid.cut(hole)

# ── Add bracket to document ────────────────────────────────────────────────
Part.show(solid)

# ── Export ──────────────────────────────────────────────────────────────────
Mesh.export([solid], __file__.replace(".py", ".stl"))
print("STL exported:", __file__.replace(".py", ".stl"))
