# Hardware Research: The Bumi-Attuned Mini-Claw

To evolve the **Butlerbot v0.1** beyond the heavy DOFBOT demonstrator, we are researching lightweight, ESP32-compatible grippers that preserve bipedal stability.

## 🎯 1. Requirements
- **Weight**: <100g (Total with servo) to minimize gait disturbance.
- **Actuator**: SG90 or MG90S (9g Micro Servo) for integration with Bumi's ESP32.
- **Payload**: Sufficient for a 10" Tablet or a Wurstsemmel Tray (~300g).

## 🛠️ 2. Recommended Options

| Option | Pros | Cons | Ideal Use |
| :--- | :--- | :--- | :--- |
| **Aluminum Mini-Claw** | Durable, Premium Look (~70g). | Slightly heavier than plastic. | **Tablet Holding** / Tray Service. |
| **Stopgap Toy Arms** | Ultra-Cheap ($50-$80), Fast-Ship. | Flimsy, Low-Payload (~150g). | **Software Prototyping** / Basic Handoff. |
| **3D-Printed Soft-Grip** | Ultralight (<50g), customizable. | Less durable, requires printing. | **Fruit/Delicate Object** handling. |
| **Plywood Laser-Cut** | Cheap, DIY friendly. | Aesthetics don't match Bumi VT. | Rapid prototyping. |

## 📜 3. Historical Precedent: The Dalek Principle

The **Dalek Plunger Arm** (BBC, 1963) remains one of the most effective "Affordable Industrialization" examples in robotics history.
- **The £5 Prop**: By using a domestic sink plunger, the BBC demonstrated that **High-Adhesion Vacuum** is a viable alternative to complex (and expensive) multi-fingered hands.
- **Modern SOTA (2026)**: We see this lineage in the **Universal Jamming Gripper** and professional vacuum suction hubs used in logistics. 
- **Application for Bumi**: A passive suction cup (The "Dalek Standard") offers a zero-power, fail-safe method for transporting smooth trays or tablets, perfectly aligning with the "Bumi-Attuned" lightweight requirement.

## 📐 4. Integration Path
1. **Mounting**: Use the existing passive claw mount point on Bumi's arm.
2. **Power**: External 5V rail (Common Ground with ESP32). Do NOT power from ESP32 3.3V pin.
3. **Control**: `ESP32Servo` library over PWM.

## 🚀 4. Next Steps
- [ ] Select **Aluminum Mini-Claw** for Industrial Beta.
- [ ] Draft 3D-printable adaptation bracket for Bumi's arm.
- [ ] Update **Butlerbot v0.1** roadmap.
