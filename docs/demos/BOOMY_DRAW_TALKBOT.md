# Boomy show-floor demos — draw & talkbot

**Boomy** (not Noomy) — Yahboom Raspbot v2 mecanum platform.

## Floor drawer (`boomy_draw`)

Spring-loaded chalk or marker on the chassis; Boomy drives the path (open-loop odometry).

### Patterns

| ID | Colors | Description |
|----|--------|-------------|
| `smiley` | 2 | Face circle + eyes, then smile arc |
| `heart` | 2 | Heart outline + inner highlight |
| `boomy_b` | 1 | Stylised letter B |

### MCP

```
yahboom_demo(operation='describe')
yahboom_demo(operation='draw', pattern='smiley')
yahboom_demo(operation='draw_status')
yahboom_demo(operation='draw_stop')
```

Mission alias: `POST /api/v1/missions/run/boomy_draw`

### REST

- `GET /api/v1/demo` — describe both demos
- `POST /api/v1/demo/draw` — body: `{ "pattern": "smiley", "skip_color_swap_pause": false }`
- `GET /api/v1/demo/draw/status`
- `POST /api/v1/demo/draw/stop`

### Two-color workflow

1. Layer 1 draws (e.g. white chalk outline)
2. `pen_up` + 8s pause + beep → swap chalk
3. Layer 2 draws (colored fill)

Set `skip_color_swap_pause=true` for CI/mock runs.

### Hardware

- Mount: ~15° angled bracket, spring down-force
- Optional: `YAHBOOM_PEN_SERVO=1` when a lift servo is wired
- Tune: `YAHBOOM_DRAW_SPEED=0.06` (m/s)

---

## Talkbot (`boomy_talkbot`)

Approach → PTZ wiggle → *"Hi, I am Boomy. Who are you?"* → listen/reply loop.

### MCP

```
yahboom_demo(operation='talkbot', max_turns=3)
yahboom_demo(operation='talkbot_status')
```

Scripted CI run:

```
yahboom_demo(
  operation='talkbot',
  use_speech_mcp=False,
  scripted_user_lines=['My name is Sandra', 'Can you draw?']
)
```

Mission alias: `POST /api/v1/missions/run/boomy_talkbot`

### REST

- `POST /api/v1/demo/talkbot`
- `GET /api/v1/demo/talkbot/status`
- `POST /api/v1/demo/talkbot/stop`

### Speech stack

| Step | Primary | Fallback |
|------|---------|----------|
| TTS | speech-mcp `POST /api/v1/tts` (FunASR fleet host) | Pi `espeak-ng` via `yahboom_tool(operation='say')` |
| STT | Voice module `listen` | Scripted lines for demos |

Env: `YAHBOOM_SPEECH_MCP_URL=http://127.0.0.1:10909`

### Choreography

1. Warm white lightstrip
2. Slow approach until ultrasonic &lt; 0.55 m (`YAHBOOM_TALKBOT_APPROACH=1`)
3. PTZ: tilt up, pan wiggle
4. Opening line (cached path recommended for snappy first impression)
5. Up to `YAHBOOM_TALKBOT_TURNS` (default 3) listen/reply cycles
6. Farewell + lights off

---

## Combined show (90 s)

1. `yahboom_demo(operation='talkbot', max_turns=2)`
2. *"Ask me to draw"* branch in talkbot replies
3. `yahboom_demo(operation='draw', pattern='smiley')`
4. PTZ looks down; *"I drew that."*

## vla-mcp integration

After a live draw or talkbot run, ingest telemetry via `vla_pipeline(operation='run', live=True)` on the workstation.
