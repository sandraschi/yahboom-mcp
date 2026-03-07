# Embodied AI Loop (Protoconscious / Perception–Action)

Minimal **observe -> LLM -> act** loop using yahboom-mcp as the body and Ollama as the brain. One abstraction (REST telemetry + snapshot + move) so the same loop can target real robot, sim, or (with adapters) other MCPs.

---

## Quick start

1. Start the robot stack: `.\webapp\start.ps1` (or Pi-less: `-Connection esp32`).
2. Ensure Ollama is running and a model is pulled (e.g. `ollama pull llava` for vision).
3. Run the embodied loop:

```powershell
cd D:\Dev\repos\yahboom-mcp
$env:YAHBOOM_BASE_URL = "http://localhost:10792"
$env:OLLAMA_BASE_URL = "http://127.0.0.1:11434"
python scripts/embodied_loop.py --instruction "go forward" --max-steps 60
```

With camera (vision model):

```powershell
python scripts/embodied_loop.py --use-vision --model llava --instruction "avoid obstacles"
```

---

## Architecture

- **Observe**: `GET /api/v1/telemetry` (battery, pose, velocity, LIDAR summary), optionally `GET /api/v1/snapshot` (one JPEG).
- **Brain**: Ollama chat (text-only or vision); system prompt restricts output to one action: `FORWARD | BACK | TURN_LEFT | TURN_RIGHT | STRAFE_LEFT | STRAFE_RIGHT | STOP`.
- **Act**: `POST /api/v1/control/move?linear=&angular=&linear_y=`.

Loop runs at configurable interval (default 1 Hz). Start in sim or with the robot in a safe area.

---

## Body abstraction

Same REST contract can be backed by:

- **Yahboom (rosbridge or ESP32)** — this repo.
- **Sim** — e.g. a Gazebo/virtualization adapter that exposes `/api/v1/telemetry`, `/api/v1/snapshot`, `/api/v1/control/move` so the same script drives the sim.

---

## Neurophilosophy & recent papers

For a short **neurophilosophy paper overview** (Damasio, Global Workspace, IIT, enactivism, and how they connect to embodied AI), see **[Neurophilosophy overview](NEUROPHILOSOPHY_OVERVIEW.md)**.

Recent arxiv (protoconscious / embodied):

| Paper | ArXiv | Theme |
|-------|--------|--------|
| Probing for Consciousness in Machines | [2411.16262](https://arxiv.org/abs/2411.16262) | Damasio-inspired RL; world/self probes. |
| Reflexive Integrated Information Unit (RIIU) | [2506.13825](https://arxiv.org/abs/2506.13825) | Differentiable integration primitive; grid-world. |
| From Understanding the World to Intervening in It (AUKAI) | [2503.00727](https://arxiv.org/abs/2503.00727) | Multi-scale embodied cognition; hybrid neural + symbolic. |

---

## See also

- [Neurophilosophy overview](NEUROPHILOSOPHY_OVERVIEW.md) — Frameworks and papers (Damasio, GWT, IIT, enactivism).
- [Hardware & ROS 2](HARDWARE_AND_ROS2.md) — Pi tiers, LIDAR, ROS 2 interaction.
- [Pi-less Setup](PI_LESS_SETUP.md) — ESP32 body, ~$100 bot.
