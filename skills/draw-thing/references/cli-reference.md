# Draw Things CLI — Flag Reference

Complete parameter reference for `draw-things-cli generate`. Load this file when building non-trivial commands or when the user asks about specific flags.

> **Verify uncertain flags.** This reference is based on known CLI design patterns and community documentation. If any flag behaves unexpectedly, run `draw-things-cli generate --help` for the authoritative list on your installed version.

---

## Core Flags

| Flag | Type | Default | Range / Notes |
|------|------|---------|---------------|
| `--model` | string | — | Path or filename of checkpoint. Required. |
| `--prompt` | string | — | Generation prompt. Required. |
| `--negative-prompt` | string | `""` | What to exclude. **Omit entirely for Flux.** |
| `--width` | int | model default | Pixels. Use model-native resolution. |
| `--height` | int | model default | Pixels. Use model-native resolution. |
| `--steps` | int | 25 | Diffusion steps. Flux Schnell: 4, Flux Dev: 30, SDXL/SD 1.5: 20–30. |
| `--guidance-scale` | float | 7.0 | CFG scale. Flux: 1.0, SDXL: 7.0, SD 1.5: 7.5. Higher = more literal. |
| `--sampler` | string | `"DPM++ 2M Karras"` | See sampler list below. |
| `--seed` | int | -1 | `-1` = random. Fixed value = reproducible output. |
| `--batch-count` | int | 1 | Number of images to generate (sequential, incrementing seeds). |
| `--batch-size` | int | 1 | Images per batch pass (parallel, same seed). Verify with `--help`. |

---

## img2img Flags

| Flag | Type | Default | Range / Notes |
|------|------|---------|---------------|
| `--image` | path | — | Input image for img2img, inpaint, and ControlNet. Verify exact flag name with `--help`. |
| `--strength` | float | 0.75 | Denoising strength. 0.0 = no change, 1.0 = full redraw. |
| `--image-guidance` | float | — | IP-Adapter or image guidance scale. Verify with `--help`. |

**Denoising strength guide:**

| Use case | `--strength` |
|----------|-------------|
| Subtle style transfer | 0.2–0.35 |
| Moderate edit | 0.5 |
| Significant change | 0.75 |
| Near-complete redraw | 0.9+ |
| Upscaling (preserve detail) | 0.2–0.4 |
| Inpainting | 0.6–0.85 |

---

## Upscaler Flags

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--upscaler` | string | — | Upscaler model filename. |
| `--upscaler-scale-factor` | int | 2 | `2` or `4`. |

**Available upscalers:**

| Model | Filename | Scale | Best for |
|-------|----------|-------|----------|
| Real-ESRGAN X2+ | `realesrgan_x2plus_f16.ckpt` | 2× | General, moderate upscale |
| Real-ESRGAN X4+ | `realesrgan_x4plus_f16.ckpt` | 4× | General, default choice |
| Real-ESRGAN X4+ Anime | `realesrgan_x4plus_anime_6b_f16.ckpt` | 4× | Illustrations, anime |
| Remacri | `remacri_4x_f16.ckpt` | 4× | Detailed textures |
| 4x UltraSharp | `4x_ultrasharp_f16.ckpt` | 4× | Architecture, fine detail |

Default: `realesrgan_x4plus_f16.ckpt`

---

## Inpainting Flags

| Flag | Type | Default | Range / Notes |
|------|------|---------|---------------|
| `--mask` | path | — | Mask image. White = repaint, black = keep. Verify exact flag name with `--help`. |
| `--mask-blur` | int | 4 | Feather mask edges. Range: 0–25. Increase if seams are visible. |
| `--mask-blur-outset` | int | 0 | Extend mask boundary. Range: −100 to 1000. |
| `--preserve-original-after-inpaint` | bool | `true` | Composites result back onto original outside mask. |

---

## ControlNet Flags

| Flag | Type | Notes |
|------|------|-------|
| `--controls` | JSON array | One or more ControlNet config objects. Single-quote on the shell. |

### ControlNet JSON Schema

```json
[
  {
    "file": "<controlnet_model_filename>",
    "weight": 0.6,
    "guidanceStart": 0.0,
    "guidanceEnd": 1.0,
    "controlMode": "Balanced",
    "inputOverride": "none"
  }
]
```

**`controlMode` values:**

| Value | Effect |
|-------|--------|
| `"Balanced"` | Equal weight between prompt and control (default) |
| `"Prompt"` | Prompt takes priority; control is weaker |
| `"Control"` | Control image takes strict priority |

**`inputOverride` preprocessor types** (pass `"none"` to use the image as-is):

`none`, `canny`, `hed`, `scribble`, `mlsd`, `depth`, `depth-and-normal`, `openpose`, `openpose-with-hand`, `color`, `tile`, `blur`, `gray`, `low-quality`, `inpainting`, `ip-adapter`, `ip-adapter-face`

**Step scheduling tips:**

| Module | Guidance start | Guidance end | Rationale |
|--------|---------------|-------------|-----------|
| Pose | 0.0 | 0.5 | Structure set early; free later steps for detail |
| Canny / Depth | 0.0 | 1.0 | Edge/depth guidance needed throughout |
| Tile | 0.0 | 1.0 | Texture guidance for full duration |

**Multi-ControlNet:** sum of all weights should total ~0.8–1.0 to avoid over-constrained outputs.

---

## LoRA Flags

| Flag | Type | Notes |
|------|------|-------|
| `--loras` | JSON array | One or more LoRA config objects. Single-quote on the shell. |

### LoRA JSON Schema

```json
[
  {
    "file": "<lora_filename>",
    "weight": 0.8,
    "mode": "All"
  }
]
```

**Fields:**

| Field | Type | Default | Range / Values |
|-------|------|---------|----------------|
| `file` | string | — | LoRA filename (relative to models dir) |
| `weight` | float | 0.6 | −1.5 to 2.5. Typical: 0.5–1.0. |
| `mode` | string | `"All"` | `"All"`, `"Base"`, `"Refiner"` |

Multiple LoRAs: add additional objects to the array.

```json
[
  {"file": "style_lora.safetensors", "weight": 0.7, "mode": "All"},
  {"file": "character_lora.safetensors", "weight": 0.6, "mode": "All"}
]
```

---

## Hi-Res Fix Flags

Two-pass generation: generate at native resolution, then upscale with denoising.

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--hires-fix` | bool | `false` | Enable hi-res fix. |
| `--hires-fix-width` | int | — | Target width for hi-res pass. |
| `--hires-fix-height` | int | — | Target height for hi-res pass. |
| `--hires-fix-strength` | float | 0.7 | Denoising for hi-res pass. Lower = preserve more. |

Verify exact flag names with `draw-things-cli generate --help`.

---

## Refiner / SDXL Stage-2 Flags

Used for SDXL's two-stage pipeline (base → refiner).

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--stage-2-steps` | int | — | Steps for refiner pass. |
| `--stage-2-guidance` | float | — | CFG for refiner pass. |
| `--stage-2-shift` | float | — | Noise schedule shift for refiner. |

Verify with `draw-things-cli generate --help`.

---

## Advanced SDXL Flags

Conditioning flags for SDXL aesthetic quality improvement.

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--clip-skip` | int | 1 | Layers to skip in CLIP. SD 1.5 anime: 2. |
| `--clip-weight` | float | 1.0 | CLIP encoder weight. |
| `--original-width` | int | — | Training-time original width conditioning. |
| `--original-height` | int | — | Training-time original height conditioning. |
| `--crop-top` | int | 0 | Crop offset top conditioning. |
| `--crop-left` | int | 0 | Crop offset left conditioning. |
| `--target-width` | int | — | Target width conditioning. |
| `--target-height` | int | — | Target height conditioning. |

Verify with `draw-things-cli generate --help`.

---

## Tiling Flags

For seamless textures or processing images larger than VRAM allows.

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--tiled-decoding` | bool | `false` | Decode VAE in tiles (reduces VRAM). |
| `--tiled-diffusion` | bool | `false` | Run diffusion in tiles (enables huge canvases). |
| `--tile-overlap` | int | — | Pixel overlap between tiles. |
| `--tile-width` | int | — | Width of each tile. |
| `--tile-height` | int | — | Height of each tile. |

Verify exact flag names with `draw-things-cli generate --help`.

---

## Performance / Caching Flags

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--tea-cache` | bool | `false` | Enable TEA-Cache for faster inference on supported models. |
| `--causal-inference` | bool | `false` | Causal attention optimization (Flux). |
| `--cfg-zero-init-steps` | int | 0 | CFG zero-init steps for conditioning warm-up. |

Verify with `draw-things-cli generate --help`.

---

## Output Flags

| Flag | Type | Default | Notes |
|------|------|---------|-------|
| `--output` | path | — | Output directory or file path. Verify exact behaviour with `--help`. |

Default output directory (skill convention): `~/Pictures/draw-thing/`

---

## Samplers

19 sampler types. Use the exact string shown below for `--sampler`.

| Sampler | Notes |
|---------|-------|
| `"DPMPP 2M Karras"` | Default for SD 1.5 and SDXL. Excellent quality/speed. |
| `"DPMPP 2M AYS"` | AYS schedule variant. Flux Klein default. |
| `"DPMPP SDE Karras"` | Stochastic; richer details, slower. |
| `"DPMPP 2S a Karras"` | Ancestral variant. |
| `"DPMPP 3M SDE Karras"` | High-quality, 3rd-order. |
| `"Euler a"` | Euler ancestral. Default for Flux Schnell/Dev. Fast and reliable. |
| `"Euler"` | Euler (non-ancestral). Deterministic. |
| `"DDIM"` | Classic; good for inpainting. Deterministic. |
| `"PLMS"` | Pseudo-linear multistep. |
| `"DPM2 Karras"` | 2nd-order DPM with Karras schedule. |
| `"DPM2 a Karras"` | Ancestral variant of DPM2 Karras. |
| `"DPM++ 2M"` | DPM++ 2M without Karras schedule. |
| `"DPM++ SDE"` | Stochastic without Karras. |
| `"LCM"` | Latent Consistency Model sampler. Very fast (4–8 steps). |
| `"TCD"` | Trajectory Consistency Distillation. |
| `"UniPC"` | Unified Predictor-Corrector. |
| `"Restart"` | Restart sampler. |
| `"DEIS"` | Diffusion Exponential Integrator Sampler. |
| `"DDPM"` | Original DDPM. Slow; rarely used for inference. |

> Verify exact strings with `draw-things-cli generate --help` if a sampler is rejected.

---

## Seed Modes

| Mode | `--seed-mode` value | Behaviour |
|------|---------------------|-----------|
| Legacy | `"Legacy"` | Original Draw Things seed handling. |
| Torch CPU Compatible | `"TorchCpuCompatible"` | Matches PyTorch CPU seed output. |
| Scale-Alike | `"ScaleAlike"` | Consistent across different output resolutions. |
| NVIDIA GPU Compatible | `"NvidiaGpuCompatible"` | Matches NVIDIA CUDA seed output. |

Default mode is `"Legacy"`. Use `"ScaleAlike"` when generating the same composition at multiple resolutions. Verify flag name with `--help`.

---

## Shell Quoting Rules

- **Always single-quote** JSON values for `--loras` and `--controls` to prevent shell expansion:
  ```bash
  --loras '[{"file": "my_lora.safetensors", "weight": 0.8}]'
  ```
- Use double-quotes for `--prompt` and `--negative-prompt`.
- Escape internal double-quotes in prompts with `\"` if using double-quote wrappers, or switch to single-quote wrappers.

---

## Quick Command Templates

### Minimal txt2img (Flux Schnell)
```bash
draw-things-cli generate \
  --model flux_1_schnell_q5p.ckpt \
  --prompt "your prompt here" \
  --width 1024 --height 1024 \
  --steps 4 \
  --guidance-scale 1.0 \
  --sampler "Euler a" \
  --seed -1
```

### txt2img with LoRA (SD 1.5)
```bash
draw-things-cli generate \
  --model v1-5-pruned-emaonly.ckpt \
  --prompt "portrait of a woman, professional photo, studio lighting" \
  --negative-prompt "blurry, low quality, extra limbs" \
  --width 512 --height 512 \
  --steps 25 \
  --guidance-scale 7.5 \
  --sampler "DPMPP 2M Karras" \
  --loras '[{"file": "portrait_lora.safetensors", "weight": 0.8}]' \
  --seed 42
```

### img2img
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image input.png \
  --prompt "same scene, golden hour lighting" \
  --strength 0.5 \
  --steps 25 \
  --guidance-scale 7.0 \
  --sampler "DPMPP 2M Karras"
```

### Upscale 4×
```bash
draw-things-cli generate \
  --model v1-5-pruned-emaonly.ckpt \
  --image input.png \
  --upscaler realesrgan_x4plus_f16.ckpt \
  --upscaler-scale-factor 4 \
  --strength 0.25 \
  --steps 30
```

### ControlNet (Canny)
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image edge_image.png \
  --prompt "architectural render, modern building" \
  --controls '[{"file": "canny_controlnet.safetensors", "weight": 0.6, "guidanceStart": 0.0, "guidanceEnd": 1.0, "controlMode": "Balanced", "inputOverride": "canny"}]' \
  --width 1024 --height 1024 \
  --steps 25
```
