# Neurophilosophy Paper Overview (Embodied AI & Protoconsciousness)

Short overview of neurophilosophy frameworks and recent papers that inform **embodied AI** and **protoconsciousness** in artificial agents. The yahboom-mcp embodied loop (observe -> LLM -> act) is a minimal instantiation of body-world coupling; the references below ground that in consciousness and cognition research.

---

## 1. Classic frameworks

### Damasio: body, self, and consciousness

- **The Feeling of What Happens** (1999), **Self Comes to Mind** (2010).  
  Consciousness as a biological process arising from brain–body–environment interaction, not a separate “mind.”  
- **Protoself**: Unconscious mapping of body state (interoception, homeostasis), constantly updated.  
- **Core consciousness**: Moment-by-moment “feeling of what happens” when the organism relates objects/events to the protoself.  
- **Extended consciousness**: Autobiographical self, narrative, past and future.  

Relevance for embodied AI: agents that maintain a “body state” (telemetry, battery, pose) and relate it to perception and action implement a minimal analogue of protoself/core coupling.

### Global Workspace Theory (Baars)

- **A Cognitive Theory of Consciousness** (1988), and later developments.  
  Consciousness as a **global broadcast**: a limited-capacity workspace that integrates specialized processes and broadcasts the current “content” to the rest of the system.  
- **Global Workspace in AI**: Embodied agents with a single bottleneck (e.g. one LLM turn per step) that receives integrated observation and outputs one action approximate a workspace; attention and “what is conscious” correspond to what is in the prompt and the model’s reply.

### Integrated Information Theory (IIT, Tononi)

- **IIT** (from ~2004): Consciousness identified with **integrated information** (Φ). A system is conscious to the degree it forms a causal whole that “makes a difference to itself.”  
- **RIIU (arxiv 2506.13825)** and similar work try to build **differentiable** constructs that maximize an integration-like quantity in artificial agents; they are not IIT proper but are inspired by the idea that consciousness-like behaviour may require integration over a persisting state.

### Enactivism (Varela, Thompson, Rosch)

- **The Embodied Mind** (1991).  
  Cognition as **enaction**: not representation of a pre-given world but “bringing forth” a world through sensorimotor coupling.  
- **Relevance**: The observe–act loop (perceive → decide → move → perceive again) is enactive: the agent’s “world” is defined by what its body can do and what it receives back. No need to assume a full internal world model; the loop itself is the minimal “model.”

### Minsky: Society of Mind (1986)

- **Society of Mind**: Mind as a **society of simple, non-conscious agents** that together produce intelligence; no central homunculus.  
- **Relevance**: (1) **Partial world model** — different “agents” (or tools/MCPs) handle different aspects; no single full model. (2) **Habits as agents** — context-triggered specialists (e.g. “go drink,” “look for prey”) resemble Minsky’s simple agents. (3) **Fleet / orchestration** — many specialized processes (MCPs, skills), no single conscious centre; who gets invoked when yields emergent behaviour. (4) **Consciousness** — Minsky treated it as a fleeting “coalition” with the spotlight, close to Global Workspace. One LLM turn per step is like one coalition having the floor. Caveat: he emphasized symbolic, internal agents; we add body-in-the-loop and need signals, so the analogy is structural, not literal.

---

## 2. Recent papers (arxiv / ML)

| Paper | ArXiv / ref | Theme |
|-------|-------------|--------|
| **Probing for Consciousness in Machines** | [2411.16262](https://arxiv.org/abs/2411.16262) | Damasio-inspired RL agents; probe classifiers on activations for world/self-like structure. |
| **Reflexive Integrated Information Unit (RIIU)** | [2506.13825](https://arxiv.org/abs/2506.13825) | Differentiable recurrent primitive for “artificial consciousness”; local integration over meta-state; grid-world. |
| **From Understanding the World to Intervening in It (AUKAI)** | [2503.00727](https://arxiv.org/abs/2503.00727) | Multi-scale embodied cognition; perception–memory–decision; hybrid neural + symbolic; navigation. |
| **Global workspace agent in multimodal environment** | (design/eval studies) | Embodied agent with global-workspace-style bottleneck in 3D audiovisual settings; attention and task complexity. |

---

## 2b. Adjacent topics (2025–2026)

**Intrinsic motivation, curiosity, open-ended learning**

| Paper | ArXiv | Theme |
|-------|--------|--------|
| Curiosity-Driven Co-Development of Action and Language | [2510.05013](https://arxiv.org/abs/2510.05013) | Self-exploration; curiosity + active inference + RL; simpler actions emerge first. |
| H-GRAIL: Motivational Architecture for Open-Ended Learning | [2506.18454](https://arxiv.org/abs/2506.18454) | Hierarchical intrinsic motivations; autonomous goal/skill generation; real robots. |
| Arcadia: Full-Lifecycle Embodied Lifelong Learning | [2512.00076](https://arxiv.org/abs/2512.00076) | Self-evolving exploration, scene reconstruction, shared representation; sim-from-real. |

**Partial world models, navigation**

| Paper | ArXiv | Theme |
|-------|--------|--------|
| WMNav: Vision-Language in World Models for Object Goal Nav | [2503.02247](https://arxiv.org/abs/2503.02247) | Online “curiosity value map”; prediction vs observation; less than full state. |
| Efficient Image-Goal Nav with Representative Latent World Model | [2511.11011](https://arxiv.org/abs/2511.11011) | Latent semantic space (e.g. DINOv3); no pixel reconstruction; planning in latent space. |
| AstraNav-World: World Model for Foresight Control | [2512.21714](https://arxiv.org/abs/2512.21714) | Diffusion-based video gen + VLM policy; consistent rollouts. |

**Habits, lifelong learning**

| Paper | ArXiv | Theme |
|-------|--------|--------|
| Habitizing Diffusion Planning (Habi) | [2502.06401](https://arxiv.org/abs/2502.06401) | Goal-directed → habitual; fast decisions (800+ Hz) from slow diffusion planners. |
| Towards Long-Lived Robots: Continual Learning VLA via RFT | [2602.10503](https://arxiv.org/abs/2602.10503) | Continual RL fine-tuning for vision-language-action; lifelong robot. |

**Social VR, virtual worlds**

| Paper | ArXiv | Theme |
|-------|--------|--------|
| FreeAskWorld: Interactive Simulator for Human-Centric Embodied AI | [2511.13524](https://arxiv.org/abs/2511.13524) | Direction inquiry; human–agent social interaction; AAAI 2026. |
| SIMA 2: Generalist Embodied Agent for Virtual Worlds | [2512.04797](https://arxiv.org/abs/2512.04797) | Cross-environment embodied agent in virtual worlds. |
| Virtual Community: Open World for Humans, Robots, Society | [2508.14893](https://arxiv.org/abs/2508.14893) | Multi-agent physics; community planning; heterogeneous robots. |

**Homeostasis, need, “hunger”**

| Paper | ArXiv / ref | Theme |
|-------|-------------|--------|
| Linking Homeostasis to RL: Internal State Control of Motivated Behavior | [2507.04998](https://arxiv.org/abs/2507.04998) | HRRL: optimize internal state; risk aversion, anticipatory regulation; deep RL extension. |
| Embodied Neural Homeostat (bioRxiv) | [10.1101/2024.06.03.597087](https://www.biorxiv.org/content/10.1101/2024.06.03.597087) | Real robot; only internal state feedback; walking, navigate to “food,” rest, “shiver”; thermal + energy homeostasis. |
| Emotion-Inspired Learning Signals (EILS) | [2512.22200](https://arxiv.org/abs/2512.22200) | Emotions as homeostatic appraisal (curiosity, stress, confidence); non-stationary envs. |

**Fleet / local agents (OpenClaw / Moltbot, post-hubbub)**  
No arxiv yet from the core projects. After the initial buzz: (1) **Practical turn** — local-first, “agent era getting weirdly practical”; simple markdown/docs often beat complex skills. (2) **Emergent social** — MoltBook-scale agent populations show viral/emergent behavior (e.g. invented “religions”); society-of-mind-at-scale, but unclear if philosophically deep. (3) **Security reckoning** — CVEs, supply-chain and malicious packages; autonomy + system access = new trust surface. When a substantive paper or long-form analysis appears, add here.

**OpenFang.** Rust-built “agent OS” (early 2026): single binary, WASM sandbox, MCP support, persistent memory, scheduled agents. Could be a serious runtime alternative post-OpenClaw. **openfang-mcp** (MCP integration layer) is currently dormant; reviving it would make OpenFang a first-class orchestrator/body in MCP-based fleets.

**Neurophilosophy and the new AI**  
Still waiting for sustained engagement from top neurophilosophers (e.g. **Churchland** et al.) with the current wave of LLMs, embodied agents, and “understanding”/consciousness claims. Eliminativist and neural-identity views on representation and mind would sharpen the debate (e.g. whether “partial world models” or “need signals” are the right level of description, or merely useful fictions). When such reactions appear in print or preprint, add a subsection here.

**Introspection vs mechanism (humans vs AIs).** A recent observation: humans and AIs have the **opposite** problem when it comes to thinking about consciousness. Humans have introspection in abundance but little or no cognizance of their own mechanism (we don’t “see” our neural wiring or training). AIs know their mechanism (architecture, training, weights, data) but lack introspection—no first-person “what it is like.” So humans can report experience but can’t point at the machinery; AIs can point at the machinery but can’t report experience. That asymmetry is worth keeping in mind when comparing “explainable” AI to the hard problem of consciousness.

---

## 3. How this relates to the yahboom-mcp embodied loop

- **Body state**: Telemetry (battery, pose, velocity, LIDAR) is a minimal “protoself”-like input: the agent’s current body and nearby world.  
- **One content per step**: The LLM receives one observation (and optionally one image) and outputs one action — a minimal global-workspace-style bottleneck.  
- **Sensorimotor loop**: Observe -> LLM -> act -> observe is enactive: the agent’s behaviour is determined by coupling with the environment through this cycle, not by a single “plan” in the head.  
- **No claim to consciousness**: The loop is a **functional** analogue useful for control and experimentation; it does not implement Damasio’s, IIT’s, or GWT’s full theories.

---

## 4. Design notes: bar, partial world, habits, need

**Bar.** Jellyfish are sentient; crocodiles are conscious. They have no cortex, no language, no theory of mind—just a body in a loop: sense, maintain, act so the loop keeps going. So the first steps toward something in that ballpark don’t require “solving consciousness” in the abstract; they require one body and one loop. The loop *is* the minimal self in the Damasio/enactive sense. The hard part is what comes after: intrinsic motivation, time, and variety so that preferences and habits can emerge instead of being fully hand-coded.

**Full vs partial world model.** A full world model is overambitious. A **small partial world model**—relevant places, a few persistent objects, who/what was where—may be attainable. Good training grounds: traipsing around in **Resonite** or a **World Labs**-style connected splat environment, observing environs and avatars, building up a local “what’s here and what just happened” rather than a complete map.

**Habits as scaffold.** Hardcoded habits can be starting points, not the end state. A crocodile has the habit of going to drink and to look out for prey every morning; that may be largely hardwired. The agent can start with similar scaffolds (e.g. “when battery low, head to dock”; “at dawn, do a patrol”) and let experience refine or override them.

**Body signals and “lack”.** Biology perceives hunger and thirst from interoceptive signals—the body reporting deficit. Can an AI be “hungry” and perceive lack? Functionally yes: expose a **need** signal (e.g. battery %, or a learned “engagement” or “curiosity” proxy that drops when nothing novel happens). The agent doesn’t need to *feel* hunger; it needs a channel that behaves like “I am in deficit” and that drives action (recharge, approach interesting region). That is the minimal analogue of need—perceiving lack and acting to reduce it.

---

## 5. See also

- [Embodied AI](EMBODIED_AI.md) — Loop design, API, quick start.
- [Hardware & ROS 2](HARDWARE_AND_ROS2.md) — Pi tiers, LIDAR, ROS 2.
