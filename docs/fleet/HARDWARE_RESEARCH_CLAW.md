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
| **3D-Printed Soft-Grip** | Ultralight (<50g), customizable. | Less durable, requires printing. | **Fruit/Delicate Object** handling. |
| **Plywood Laser-Cut** | Cheap, DIY friendly. | Aesthetics don't match Bumi VT. | Rapid prototyping. |

## 📐 3. Integration Path
1. **Mounting**: Use the existing passive claw mount point on Bumi's arm.
2. **Power**: External 5V rail (Common Ground with ESP32). Do NOT power from ESP32 3.3V pin.
3. **Control**: `ESP32Servo` library over PWM.

## 🚀 4. Next Steps
- [ ] Select **Aluminum Mini-Claw** for Industrial Beta.
- [ ] Draft 3D-printable adaptation bracket for Bumi's arm.
- [ ] Update **Butlerbot v0.1** roadmap.
