# Dashboard — 3D visualization (Viz page)

The **3D Visualization** page (`webapp/src/pages/viz/Viz.tsx`) renders the Raspbot from **STL meshes** (Yahboom / `automaticaddison/yahboom_rosmaster` URDF lineage) with **React Three Fiber** (Y-up world).

## Coordinate convention

- **Three.js** uses **Y as the vertical axis** (ground plane is typically XZ at `y = 0`).
- **URDF** uses **Z up**. Comments in the viz code that refer to joint `z` offsets must be mapped to **Y** when placing meshes.

## Wheel and chassis height

Wheel STLs are centered on the **axle**. If the axle is placed at `y = 0`, the tire extends to **`y = -WHEEL_RADIUS`**, so wheels appear **sunk into the floor**.

**Rule used in code:** set the wheel hub height to **`WHEEL_AXLE_Y = WHEEL_RADIUS`** so the tire bottom rests near **`y = 0`**. The chassis (`base_link`) sits **`WHEEL_RADIUS` above the wheel plane** (`BASE_LINK_Y = WHEEL_AXLE_Y + WHEEL_RADIUS`), matching the URDF idea that `base_link` sits one wheel radius above the wheel centers.

Accessories (LIDAR, camera, top-plate glow, heading line) are offset by **`WHEEL_AXLE_Y`** so they stay aligned with the corrected assembly.

## Constants (maintainer)

| Symbol | Role |
|--------|------|
| `WHEEL_RADIUS` | Nominal wheel radius (m), from URDF |
| `WHEEL_AXLE_Y` | World Y of wheel axles (tire contact at ground) |
| `BASE_LINK_Y` | World Y of `base_link` mesh origin |
| `WHEEL_X_OFF`, `WHEEL_Y_HALF` | Lateral wheel positions (X / Z in Three.js) |

If a specific STL has its origin off the geometric center, tweak **`BASE_LINK_Y`** (or the accessory offsets) slightly; the main fix is axle height, not mesh scale.

## Assets

Meshes live under `webapp/public/assets/meshes/` (e.g. `base_link_X3.STL`, `*_wheel_X3.STL`). The page loads them via `STLLoader`.
