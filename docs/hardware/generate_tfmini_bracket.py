"""Generate TFmini-S + camera bracket STL for 3D printing.

Output: tfmini_bracket.stl

Dimensions (mm):
- Camera module: 25 x 25 (the visible face) 
- TFmini-S:      42 x 15 x 16
- Wall thickness: 2mm
- Screws:        M2.5 holes at camera corners
"""
import numpy as np
from stl import mesh

WALL = 2.0
GAP = 1.0
CAM_W, CAM_D, CAM_H = 25, 25, 20
TFM_W, TFM_D, TFM_H = 42, 15, 16
LENS_R = 6

BASE_W = max(CAM_W, TFM_W) + 2 * WALL
BASE_D = CAM_D + 2 * WALL
BASE_H = WALL + GAP + TFM_H  # total height

def _translate(m, x, y, z):
    m.translate(np.array([x, y, z]))
    return m

def box(w, d, h):
    vertices = np.array([
        [0,0,0], [w,0,0], [w,d,0], [0,d,0],
        [0,0,h], [w,0,h], [w,d,h], [0,d,h],
    ])
    faces = np.array([
        [0,3,1], [1,3,2],  # bottom
        [4,5,7], [5,6,7],  # top
        [0,1,5], [0,5,4],  # front
        [2,3,7], [2,7,6],  # back
        [0,4,7], [0,7,3],  # left
        [1,2,6], [1,6,5],  # right
    ])
    return mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype), remove_empty_areas=False) or mesh.Mesh(np.zeros(1)) or (lambda: (m := mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype)), setattr(m, 'vectors', vertices[faces]), m))()

# Simpler approach: create manually
vert = np.array([
    [0,0,0],[1,0,0],[1,1,0],[0,1,0],
    [0,0,1],[1,0,1],[1,1,1],[0,1,1],
])
faces = np.array([
    [0,1,2],[0,2,3],[1,5,6],[1,6,2],
    [4,6,5],[4,7,6],[0,4,5],[0,5,1],
    [2,6,7],[2,7,3],[0,3,7],[0,7,4],
])
# Scale to bracket size
faces = faces * BASE_W + ...  # This won't work well
