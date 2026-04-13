# Environmental Design: The Robot-Amenable Home

This document codifies the "Android-First" approach to household architecture. Instead of over-engineering robot torque, we modify the environment to accommodate autonomous agents.

## 🏗️ 1. The Amenability Principle
The most successful domestic robots do not fight the environment; they collaborate with it. We prioritize **Low-Obstacle Infrastructure** to reduce the mechanical requirements of the fleet.

## 🛠️ 2. Key Household Modifications

### 🧊 A. The "Easy-Open" Fridge Standard
Standard fridge seals require high pull-force (~15-30N). 
- **The Mod**: Retrofitting magnetic seals or push-to-release mechanisms that allow a Level 1 (Mini-Claw) robot to initiate opening.
- **The Android Rule**: A fridge is an "Object Hub," not a "Fortress."

### 🚪 B. Unlocked/Push-to-Open Cupboards
Robots struggle with traditional door handles.
- **The Mod**: Replacing complex handles with standardized **Magnetic Push-Latches**.
- **The Android Rule**: Any cupboard containing robot-accessible tools (Cleaning supplies, Battery spares) must be "Handle-Neutral."

### 🧽 C. Open Tool Accessibility
- **The Mod**: Storing "Utility Objects" (Feather dusters, Trays, Tablets) in open **Reception Docks** rather than enclosed spaces.
- **The Android Rule**: If the robot cannot see the tool's interaction handle, the tool does not exist for the autonomous agent.

## 🌐 3. Interaction Standards
- **Digital Handshakes**: High-torque appliances should inform the robot of their state (Open/Closed/Locked) via MQTT/Matter to prevent "Dead-Lock" scenarios.
- **Path Clearance**: Maintaining a 50cm "Bumi-Corridor" in living spaces to ensure 100% navigation uptime.

---
*Document Version: SOTA v16.16*
