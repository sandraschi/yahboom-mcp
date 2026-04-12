# Understanding Mecanum Wheels: Omnidirectional Movement

The Yahboom Raspbot v2 uses **Mecanum wheels**, which are significantly more advanced than standard wheels or tank tracks. 

## 1. How they work (The "45-Degree" Secret)

A Mecanum wheel is not just a standard wheel. It has a series of **rollers** attached around its circumference, angled at exactly **45 degrees** to the plane of the wheel.

- **Standard Wheels**: Force is only applied forward or backward.
- **Mecanum Wheels**: Because of the 45-degree rollers, part of the force is directed **sideways**.

## 2. "Tank Control" vs. "Omnidirectional Control"

You are correct that they are controlled individually (one motor per wheel), but it's not just "lubrication." By changing the direction of rotation for each wheel, the side-forces either cancel each other out or add up to move the robot in any direction.

### Motion Patterns

| Direction | Front-Left | Front-Right | Rear-Left | Rear-Right | Net Force Vector |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Forward** | ⬆️ | ⬆️ | ⬆️ | ⬆️ | All 4 wheels push forward. |
| **Backward** | ⬇️ | ⬇️ | ⬇️ | ⬇️ | All 4 wheels push backward. |
| **Strafe Left** | ⬇️ | ⬆️ | ⬆️ | ⬇️ | Side-forces push the bot left. |
| **Strafe Right** | ⬆️ | ⬇️ | ⬇️ | ⬆️ | Side-forces push the bot right. |
| **Diagonal** | ⬆️ | 🛑 | 🛑 | ⬆️ | Only two wheels spin. |
| **Turn (Tank)** | ⬆️ | ⬇️ | ⬆️ | ⬇️ | Pivot around the center. |

## 3. The "X" and "O" Configuration

Mecanum wheels must be installed in a specific pattern. If you look at the rollers from above, they should form an **"X"** shape. 
- If they form an "O", the robot will still move forward/back but won't be able to strafe sideways correctly.

## 4. Why it matters for your Fleet

Mecanum wheels allow the robot to:
1.  **Navigate Tight Spaces**: Spin in place or slide sideways through narrow gaps without turning.
2.  **Precision Docking**: Move sideways to align with a charging dock or a target perfectly.
3.  **Smooth Motion**: Transitions between directions are seamless because the rollers handle the "friction" of changing vectors.

In many ways, it's like a "hovercraft" on wheels!
