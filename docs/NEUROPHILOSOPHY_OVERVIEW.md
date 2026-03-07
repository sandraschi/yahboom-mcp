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

---

## 2. Recent papers (arxiv / ML)

| Paper | ArXiv / ref | Theme |
|-------|-------------|--------|
| **Probing for Consciousness in Machines** | [2411.16262](https://arxiv.org/abs/2411.16262) | Damasio-inspired RL agents; probe classifiers on activations for world/self-like structure. |
| **Reflexive Integrated Information Unit (RIIU)** | [2506.13825](https://arxiv.org/abs/2506.13825) | Differentiable recurrent primitive for “artificial consciousness”; local integration over meta-state; grid-world. |
| **From Understanding the World to Intervening in It (AUKAI)** | [2503.00727](https://arxiv.org/abs/2503.00727) | Multi-scale embodied cognition; perception–memory–decision; hybrid neural + symbolic; navigation. |
| **Global workspace agent in multimodal environment** | (design/eval studies) | Embodied agent with global-workspace-style bottleneck in 3D audiovisual settings; attention and task complexity. |

---

## 3. How this relates to the yahboom-mcp embodied loop

- **Body state**: Telemetry (battery, pose, velocity, LIDAR) is a minimal “protoself”-like input: the agent’s current body and nearby world.  
- **One content per step**: The LLM receives one observation (and optionally one image) and outputs one action — a minimal global-workspace-style bottleneck.  
- **Sensorimotor loop**: Observe -> LLM -> act -> observe is enactive: the agent’s behaviour is determined by coupling with the environment through this cycle, not by a single “plan” in the head.  
- **No claim to consciousness**: The loop is a **functional** analogue useful for control and experimentation; it does not implement Damasio’s, IIT’s, or GWT’s full theories.

---

## 4. See also

- [Embodied AI](EMBODIED_AI.md) — Loop design, API, quick start.  
- [Hardware & ROS 2](HARDWARE_AND_ROS2.md) — Pi tiers, LIDAR, ROS 2.
