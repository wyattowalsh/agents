# Draw Things CLI — Flag Reference

Primary parameter reference for `draw-things-cli generate`. Load this file when building non-trivial commands or when the user asks about specific flags.

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
| `--upscaler-scale` | int | 2 | `2` or `4`. |

See SKILL.md Mode: Upscale section for available upscalers and filenames.

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

### ControlNet (`--controls`)

JSON array of control configurations. See `references/controlnet-guide.md` for the complete JSON schema, control modes, preprocessor types, and weight recommendations.

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
| `--decoding-tile-overlap` | int | — | Pixel overlap between decoding tiles. |
| `--decoding-tile-width` | int | — | Width of each decoding tile. |
| `--decoding-tile-height` | int | — | Height of each decoding tile. |

Diffusion tiling uses `--diffusion-tile-width`, `--diffusion-tile-height`, `--diffusion-tile-overlap`.

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
| `"Euler a"` | Default for Flux. Fast, good quality. |
| `"Euler A Substep"` | Substep variant of Euler a. |
| `"Euler A Trailing"` | Trailing schedule variant. |
| `"Euler A AYS"` | AYS (Align Your Steps) schedule. |
| `"DPM++ 2M Karras"` | Default for SD 1.5 and SDXL. Excellent quality/speed. |
| `"DPM++ 2M AYS"` | AYS schedule variant. Flux Klein default. |
| `"DPM++ 2M Trailing"` | Trailing schedule variant. |
| `"DPM++ SDE Karras"` | Stochastic; richer details, slower. |
| `"DPM++ SDE AYS"` | AYS schedule for SDE variant. |
| `"DPM++ SDE Substep"` | Substep variant of SDE. |
| `"DPM++ SDE Trailing"` | Trailing schedule for SDE variant. |
| `"DDIM"` | Classic; good for inpainting. Deterministic. |
| `"DDIM Trailing"` | Trailing schedule variant of DDIM. |
| `"PLMS"` | Pseudo-linear multistep. |
| `"UniPC"` | Unified Predictor-Corrector. |
| `"UniPC Trailing"` | Trailing schedule variant. |
| `"UniPC AYS"` | AYS schedule variant. |
| `"LCM"` | Latent Consistency Model. Very fast (4-8 steps). |
| `"TCD"` | Trajectory Consistency Distillation. |

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

