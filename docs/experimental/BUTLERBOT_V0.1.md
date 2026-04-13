# Experimental Prototype: Butlerbot v0.1

The **Butlerbot v0.1** is a composite bipedal manipulator formed by mounting a **Yahboom DOFBOT** (6-DOF) into the **Noetix Bumi's** passive chassis claw. 

## ⚖️ Equilibrium Analysis

| Spec | Value | Analysis |
| :--- | :--- | :--- |
| **Bumi Mass** | 20.0 kg | Base stabilization platform. |
| **DOFBOT Mass** | 1.25 kg | Offset load (approx. 6.25% of total mass). |
| **Lever Arm** | ~15-20 cm | Distance from vertical center of gravity to the claw mount. |
| **Equilibrium Shift** | Central -> Fore-Lean | The robot must adjust its "Zero Moment Point" (ZMP) to compensate for the forward weight. |

## 🛠️ Implementation Logic

1.  **Passive Docking**: The DOFBOT base slides into the Bumi's tablet/holder slot (Passive Claw).
2.  **Dynamic Counter-Balance**: 
    *   When the DOFBOT arm extends forward, Bumi must lean backward slightly to keep the COM (Center of Mass) within its footprint.
    *   **Equilibrium Guard**: A real-time IMU feedback loop that triggers a "Deep Crouch" if pitch exceeds safety thresholds (e.g., >12°).
3.  **Communication**: The DOFBOT is powered by Bumi's internal power bus and controlled via the same ROS 2 Humble network, appearing as a namespaced `mani_arm` node in the robot graph.

## 🍱 Use Case: Mobile Wurstsemmel Service
Unlike the standard [Wurstsemmel Protocol](../fleet/MISSION_WURSTSEMMEL.md) (which uses stationary prep), the **Butlerbot** can prep the roll while in motion, providing a "Viennese Coffee House" style mobile service.

> [!WARNING]
> High center-of-gravity configurations increase the risk of "Faceplant Events." Initial gait testing should be conducted with the **Bumi VT (Virtual Twin)** before physical deployment.
