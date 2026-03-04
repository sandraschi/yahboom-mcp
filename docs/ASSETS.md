# Yahboom G1 Robot Assets: 3D Models & Drawings

For simulation (Unity/Gazebo), visualization (Rviz), or custom modifications (Blender/3D Printing), you can find the following assets:

## 1. Official ROS 2 Description Package
Yahboom provides the `yahboomcar_description` package which contains the **URDF** (Unified Robot Description Format) and **STL** meshes.

- **GitHub Repository**: [YahboomTechnology/yahboomcar_ros2_ws](https://github.com/YahboomTechnology/yahboomcar_ros2_ws)
- **Asset Path**: `src/yahboomcar_description/meshes/`
- **Key Files**:
    - `STM32-V2-V1.SLDASM.urdf` (The core definition file)
    - `.STL` files for the chassis, wheels, and camera mount.

## 2. 3D Model Resources
If you need high-fidelity models for Blender or CAD:

- **Thingiverse**: [Yahboom G1 Smart Car](https://www.thingiverse.com/thing:4658145) (Includes STL files for many components).
- **Format Conversion**: 
    - The STLs can be imported directly into **Blender**.
    - For CAD (STEP/IGES), you may need to use **Fusion 360** to convert the mesh files if Yahboom hasn't provided the raw STEP files in their "Annex" repositories.

## 3. Technical Drawings
Yahboom usually includes PDF schematics and mechanical drawings in their product "Annex" or "Materials" zip files.

- **Download Center**: [Yahboom Resource Center](http://www.yahboom.net/manual/G1)
- **Note**: Look for the "Hardware manual" or "Schematic" sections.

## 4. Usage in Simulators
If you are planning to use these in **Unity** (as part of your Robotics Fleet), you can use the **URDF Importer** package to bring the `yahboomcar_description` directly into your scene, which will automatically place the meshes and set up the joint transforms.
