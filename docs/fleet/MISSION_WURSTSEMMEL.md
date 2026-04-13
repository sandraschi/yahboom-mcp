# Federated Mission: The "Wurstsemmel Protocol"

This mission storyboard illustrates the high-fidelity synergy between the **Yahboom X3 Plus** and the **Noetix Bumi** android, representing a SOTA v16.15 benchmark for agentic federated robotics.

## 🍱 Mission Goal
Deliver a freshly plated "Wurstsemmel" (Austrian sausage roll) from the preparation area to the Client (Sandra) using zero-manual intervention.

---

## 🤖 The Robot Cast

### 🏗️ 1. The Chef: Yahboom ROSMASTER X3 PLUS (or DOFBOT)
- **Role**: Precision Plating & Preparation.
- **Hardware**: 6-DOF Mechanical Arm (Mobile on X3 Plus / Desktop on DOFBOT).
- **Logic**: Uses Inverse Kinematics (MoveIt!) to pick the Wurstsemmel and place it perfectly onto a customized **Bumi-Dockable Tray**. The **DOFBOT (~$340)** is the primary "Stationary Chef" choice for budget-conscious labs.

### 🚶 2. The Carrier: Noetix Bumi
- **Role**: Stabilized "Android" Delivery.
- **Hardware**: 21-DOF Bipedal Android.
- **Logic**: 
    - Navigates to the X3 Plus using shared fleet SLAM data.
    - Slides its **Passive Claw** into the Tray's tablet-style holder.
    - Executes a stabilized "Delivery Walk" to Sandra's coordinates.

---

## 🔄 Workflow Execution

1.  **Orchestration**: Sandra triggers the `wurstsemmel_request` workflow via the Dashboard.
2.  **Staging**: The X3 Plus confirms the tray is clear and uses its arm to plate the roll.
3.  **Coupling**: Bumi moves into a "Deep Crouch" and slides the passive arm into the tray mount.
4.  **Transit**: Bumi stands up and navigates to Sandra, using its 20kg weight to provide a stable, non-tipping bipedal gait.
5.  **Completion**: Sandra enjoys the Wurstsemmel.

---

## 🛠️ Infrastructure Requirements

- **Unified DDS Bridge**: Enables real-time transform sharing between the X3 Plus arm coordinates and the Bumi navigation base.
- **MCP Federated Search**: Allows Sandra's AI assistant to "find" which robot is currently equipped with the gripper arm and which is free for delivery.
- **Isaac Gym Prototype**: Currently being modeled in the **Bumi VT (Virtual Twin)** stack to ensure the passive-claw attachment is stable during bipedal locomotion.

> [!NOTE]
> This protocol highlights the "Passive Claw" advantage of the Bumi: by sliding into a fixed tablet holder, it bypasses the need for an active gripper while maintaining high transport stability.
