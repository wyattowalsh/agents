# ControlNet Guide

Reference for ControlNet modules, weights, step scheduling, and multi-control setups with `draw-things-cli`. Load when running ControlNet mode or building `--controls` JSON.

---

## What ControlNet Does

ControlNet conditions generation on a **structural input image** (edges, depth map, pose skeleton, etc.) while the text prompt drives style and content. It is distinct from LoRA: ControlNet controls *structure*, LoRA controls *style/subject*.

**CLI flag:** `--controls '<json array>'` — always single-quote the JSON to prevent shell expansion.

---

## `--controls` JSON Schema

```json
[
  {
    "file": "<controlnet_model_filename>",
    "weight": 0.6,
    "guidanceStart": 0.0,
    "guidanceEnd": 1.0,
    "controlMode": "Balanced"
  }
]
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `file` | string | required | ControlNet model filename (`.ckpt` or `.safetensors`) in models dir |
| `weight` | float | 0.6 | Influence strength (0.0–2.0, typical 0.4–0.9) |
| `guidanceStart` | float | 0.0 | Fraction of steps where control begins (0.0 = from the start) |
| `guidanceEnd` | float | 1.0 | Fraction of steps where control ends (1.0 = to the end) |
| `controlMode` | string | `"Balanced"` | `"Balanced"` \| `"Prompt"` \| `"Control"` |
| `inputOverride` | string | (auto) | Force a specific preprocessor (see Preprocessors table below) |

> **Verify field names and supported values** with `draw-things-cli generate --help` — exact schema may differ between versions.

---

## Control Modes

| Mode | Behavior | When to Use |
|------|----------|-------------|
| `"Balanced"` | Equal weight between prompt and control input | Default — most use cases |
| `"Prompt"` | Prompt dominates; control provides soft structure | Creative freedom with loose structure |
| `"Control"` | Control input dominates; prompt provides color/style | Strict structural adherence required |

---

## Module Reference

### Primary Modules

| Module | Best For | Typical Weight | Notes |
|--------|----------|----------------|-------|
| **Canny** | Hard edges, architecture, line art, product design | 0.6–0.8 | Needs full duration (`guidanceEnd: 1.0`). Too high → stiff, over-literal |
| **Depth** | Spatial layout, scene composition, foreground/background separation | 0.5–0.7 | Less strict than Canny; works well for organic subjects |
| **Pose** (OpenPose) | Human figures, body position, character angles | 0.6–0.8 | Can end early (`guidanceEnd: 0.5–0.7`) after pose is established |
| **Scribble** | Rough sketches, layout from hand-drawn input | 0.7–0.9 | Tolerant of messy input; high weight needed for fidelity |
| **Tile** | Detail upscaling, texture enhancement | 0.4–0.6 | Used in upscaling pipelines; lower weight preserves original content |
| **Normal Map** | Surface detail, bump/relief guidance | 0.5–0.7 | More technical — use when geometry detail matters |
| **Color** | Color palette transfer from a reference image | 0.4–0.6 | Soft control; use low weight to avoid washed-out results |
| **IP-Adapter** | Style/content transfer from a reference image | 0.5–0.8 | More flexible than LoRA for one-shot style guidance |
| **Inpainting** | Inpaint-specific conditioning | 0.8–1.0 | Use in inpainting mode, not general generation |

---

## Step Scheduling (`guidanceStart` / `guidanceEnd`)

Step scheduling controls *which portion of the diffusion steps* ControlNet is active.

| Use Case | `guidanceStart` | `guidanceEnd` | Effect |
|----------|-----------------|---------------|--------|
| Full structural control | 0.0 | 1.0 | Control active for all steps (default) |
| Pose lock, creative finish | 0.0 | 0.5–0.6 | Pose established early, prompt refines detail freely |
| Late-stage detail add | 0.5 | 1.0 | Structure from prompt, ControlNet adds detail at end |
| Gentle overall influence | 0.2 | 0.8 | Skip noisy early steps, stop before final refinement |

**Rules of thumb:**
- **Canny / Depth**: keep `guidanceEnd` at 1.0 — these need the full duration to maintain structural fidelity.
- **Pose**: ending at 0.5–0.7 often gives better results; once the pose is baked in, the model refines naturally.
- **Tile / Color**: a narrower window (e.g., 0.2–0.8) avoids over-dominating the output.

---

## Weight Guidelines

### Single ControlNet

| Weight Range | Effect |
|-------------|--------|
| 0.3–0.5 | Subtle structural suggestion; prompt has most control |
| 0.5–0.7 | Balanced — recommended starting point |
| 0.7–0.9 | Strong structural adherence; useful for strict layouts |
| 1.0+ | Extreme adherence; risk of artifacts; use only if 0.9 isn't enough |

### Multiple ControlNets

When stacking multiple controls, **total influence adds up** — reduce individual weights to avoid over-conditioning.

| Config | Recommended Per-Control Weight | Combined ~Total |
|--------|-------------------------------|-----------------|
| 2 controls | 0.4–0.5 each | ~0.8–1.0 |
| 3 controls | 0.3–0.4 each | ~0.9–1.2 |
| Dominant + subtle | 0.6 + 0.3 | ~0.9 |

---

## Preprocessors (`inputOverride`)

Preprocessors transform your input image into the control signal before it reaches the model. If you provide a pre-processed control image (e.g., an already-extracted edge map), you can omit `inputOverride`.

The following 17 preprocessor types are available (verify exact string values with `draw-things-cli generate --help` — these are the conceptual names; CLI strings may differ):

| Preprocessor | Input → Output | Typical Use |
|-------------|---------------|-------------|
| `canny` | Photo → Edge map | Architecture, objects |
| `depth_midas` | Photo → Depth map | Scene composition |
| `depth_zoe` | Photo → Depth map (high quality) | Detailed depth |
| `openpose` | Photo → Skeleton | Human pose |
| `openpose_hand` | Photo → Skeleton + hands | Detailed hand control |
| `openpose_faceonly` | Photo → Face landmarks | Facial expression |
| `openpose_full` | Photo → Full body + hands + face | Complete figure |
| `scribble_hed` | Photo → Soft edges/scribble | Sketch-like input |
| `scribble_pidinet` | Photo → Cleaner scribble | Sketch refinement |
| `normal_bae` | Photo → Normal map | Surface detail |
| `mlsd` | Photo → Straight-line segments | Architecture, rooms |
| `lineart` | Photo → Line art | Illustration style |
| `lineart_coarse` | Photo → Coarse lines | Bold illustration |
| `lineart_anime` | Photo → Anime lineart | Anime images |
| `shuffle` | Photo → Shuffled colors | Content/color reference |
| `tile` | Photo → Tiled content | Upscaling enhancement |
| `inpaint` | Image + mask → Control | Inpainting conditioning |

> **Important:** If Draw Things performs preprocessing automatically based on the module type, you may not need `inputOverride`. Verify with `draw-things-cli generate --help` before forcing a preprocessor.

---

## Complete Examples

### Canny Edge Control (full duration)
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/reference-building.png \
  --prompt "futuristic skyscraper, cyberpunk city, neon lights, rain, night" \
  --controls '[{"file": "control_canny_xl.safetensors", "weight": 0.7, "guidanceStart": 0.0, "guidanceEnd": 1.0, "controlMode": "Balanced"}]' \
  --width 1024 --height 1024 \
  --steps 25 --guidance-scale 7.0
```

### Pose-Guided Character (early end)
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/pose-reference.png \
  --prompt "a warrior in ornate golden armor, forest background, dramatic lighting" \
  --controls '[{"file": "control_openpose_xl.safetensors", "weight": 0.75, "guidanceStart": 0.0, "guidanceEnd": 0.6, "controlMode": "Balanced"}]' \
  --width 1024 --height 1536 \
  --steps 25 --guidance-scale 7.0
```

### Depth + Pose Combined (two controls)
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/scene-reference.png \
  --prompt "fantasy tavern interior, warm candlelight, medieval decor" \
  --controls '[
    {"file": "control_depth_xl.safetensors", "weight": 0.45, "guidanceStart": 0.0, "guidanceEnd": 1.0, "controlMode": "Balanced"},
    {"file": "control_openpose_xl.safetensors", "weight": 0.45, "guidanceStart": 0.0, "guidanceEnd": 0.6, "controlMode": "Balanced"}
  ]' \
  --width 1024 --height 1024 \
  --steps 25 --guidance-scale 7.0
```

> **Note:** Multi-control JSON must be valid. Single-quote the entire array. Verify with a JSON linter if the command errors out.

### Tile for Upscaling Enhancement
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/original-512.png \
  --prompt "high resolution version, sharp details, photorealistic" \
  --controls '[{"file": "control_tile_xl.safetensors", "weight": 0.5, "guidanceStart": 0.1, "guidanceEnd": 0.9, "controlMode": "Control"}]' \
  --width 2048 --height 2048 \
  --strength 0.3 \
  --steps 30
```

---

## ControlNet + LoRA Together

ControlNet and LoRA can stack. Apply LoRA for style/character, ControlNet for structure:

```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/pose.png \
  --prompt "anime character, detailed face, school uniform" \
  --controls '[{"file": "control_openpose_xl.safetensors", "weight": 0.7, "guidanceStart": 0.0, "guidanceEnd": 0.6, "controlMode": "Balanced"}]' \
  --loras '[{"file": "anime_style_xl.safetensors", "weight": 0.7}]' \
  --width 1024 --height 1024 \
  --steps 25
```

---

## Model Compatibility Notes

| ControlNet Family | Compatible Base Models |
|------------------|----------------------|
| SD 1.5 ControlNet (`control_*.ckpt`) | SD 1.5 checkpoints only |
| SDXL ControlNet (`control_*_xl.safetensors`) | SDXL checkpoints only |
| Flux ControlNet | Flux-specific modules (verify availability) |

> ControlNet model filenames in your local directory may differ from the examples above. Always check `ls "$DRAWTHINGS_MODELS_DIR"` for actual filenames before constructing the command.

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Structure ignored | Weight too low | Raise weight (try 0.8) or change `controlMode` to `"Control"` |
| Output looks stiff / robotic | Weight too high | Lower weight (0.5–0.6) or end earlier (`guidanceEnd: 0.7`) |
| Face/hands still deformed despite pose | Pose model not loaded correctly | Verify filename with `ls "$DRAWTHINGS_MODELS_DIR"` |
| JSON parse error | Shell expansion on quotes | Always **single-quote** the JSON: `--controls '[...]'` |
| Unexpected model error | ControlNet/base model mismatch | Use SD 1.5 ControlNet with SD 1.5 models, SDXL with SDXL |

