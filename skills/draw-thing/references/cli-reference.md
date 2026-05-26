# Draw Things CLI Reference

Current reference for `draw-things-cli` as used by this skill. Load when building non-trivial commands or checking whether a flag is supported.

> Trust the installed CLI first. If this file and `draw-things-cli generate --help` disagree, use the installed help and update the skill later.

---

## Commands

| Command                                         | Purpose                                        | Typical use                |
| ----------------------------------------------- | ---------------------------------------------- | -------------------------- |
| `draw-things-cli generate`                      | Run local inference and save an image or video | Generation, img2img, media |
| `draw-things-cli models list`                   | List official and community catalog entries    | Model discovery            |
| `draw-things-cli models list --downloaded-only` | List local downloads                           | Inventory                  |
| `draw-things-cli models ensure --model <id>`    | Download/resolve a model and dependencies      | Setup                      |
| `draw-things-cli models import <path-or-url>`   | Import external model/LoRA/control assets      | Imports                    |
| `draw-things-cli train lora`                    | LoRA training entrypoint                       | Training workflows         |
| `draw-things-cli completion`                    | Shell completion                               | User setup                 |

---

## Generate Flags Exposed By Current Help

| Flag                                           | Type   | Notes                                                                              |
| ---------------------------------------------- | ------ | ---------------------------------------------------------------------------------- |
| `--models-dir`                                 | path   | Override Draw Things models directory.                                             |
| `-m`, `--model`                                | string | Model file id, display name, `hf://owner/repo`, `owner/repo`, or Hugging Face URL. |
| `-p`, `--prompt`                               | string | Inline prompt.                                                                     |
| `--prompt-file`                                | path   | Read prompt from a file.                                                           |
| `--negative-prompt`                            | string | Inline negative prompt when model supports it.                                     |
| `--negative-prompt-file`                       | path   | Read negative prompt from a file.                                                  |
| `--steps`                                      | int    | Inference steps. Use recommended defaults per model.                               |
| `--cfg`                                        | float  | Guidance. Replaces old `--guidance-scale` examples.                                |
| `--width`                                      | int    | Output width. Use model-appropriate dimensions.                                    |
| `--height`                                     | int    | Output height. Use model-appropriate dimensions.                                   |
| `--frames`                                     | int    | Media/video frame count. For LTX, use divisible by 8 plus 1.                       |
| `--strength`                                   | float  | Img2img change amount.                                                             |
| `-s`, `--seed`                                 | int    | Reproducibility seed.                                                              |
| `--config-json`                                | JSON   | Override settings with JSON. Verify schema before use.                             |
| `--config-file`                                | path   | Override settings from JSON file. Best path for advanced app settings.             |
| `--image`                                      | path   | Input image for img2img/image-conditioned workflows.                               |
| `-o`, `--output`                               | path   | Output image/video file. Always set this explicitly.                               |
| `--video-format`                               | string | Video format when output path does not imply it.                                   |
| `--terminal-image`                             | bool   | Preview image in terminal where supported. Not a file output substitute.           |
| `--terminal-image-protocol`                    | string | Terminal image protocol.                                                           |
| `--download-missing` / `--no-download-missing` | bool   | Whether missing model assets may be downloaded.                                    |
| `--offline`                                    | bool   | Disable network access.                                                            |

---

## Removed Or Unexposed Old Flags

These flags appeared in older examples but are not exposed by current `generate --help` in this environment:

| Old flag                         | Current action                                                 |
| -------------------------------- | -------------------------------------------------------------- |
| `--guidance-scale`               | Use `--cfg`.                                                   |
| `--sampler`                      | Do not pass directly unless help later exposes it.             |
| `--batch-count`, `--batch-size`  | Use a shell loop with explicit seeds/output names.             |
| `--upscaler`, `--upscaler-scale` | Use app/config-file workflow only after schema verification.   |
| `--mask`, `--mask-blur`          | Use app/config-file workflow only after schema verification.   |
| `--controls`                     | Use app/config-file workflow only after schema verification.   |
| `--loras`                        | Use app/import/config workflow only after schema verification. |
| `--hires-fix` and related flags  | Use app/config-file workflow only after schema verification.   |

Never copy old direct-flag examples into live commands without rechecking help.

---

## Output Semantics

Always pass `--output <file>`.

If `--output` is omitted, current CLI behavior may be terminal preview only. Agent workflows need a durable path for follow-up edits, comparison, and user reporting.

Recommended output directory:

```bash
mkdir -p "$HOME/Pictures/draw-thing"
```

Use descriptive names with model role and seed, for example:

```text
$HOME/Pictures/draw-thing/qwen2512-poster-seed-1234.png
$HOME/Pictures/draw-thing/ltx-boat-seed-1234.mov
```

---

## Model Setup Commands

List all catalog entries:

```bash
draw-things-cli models list
```

List local downloads only:

```bash
draw-things-cli models list --downloaded-only
```

Ensure a model and dependencies:

```bash
draw-things-cli models ensure --model qwen_image_layered_1.0_bf16_q8p.ckpt
```

Use `--offline` to verify local availability without downloading:

```bash
draw-things-cli models ensure --model qwen_image_2512_q8p.ckpt --offline
```

---

## Import Workflow

Use Draw Things optimized assets when available. For external models, LoRAs, and controls, prefer local files over URL imports when possible:

```bash
draw-things-cli models import /path/to/model-or-lora.safetensors
```

For a URL or Hugging Face model reference, verify licensing and compatibility first:

```bash
draw-things-cli models import hf://owner/repo
```

---

## Command Templates

### Fast Image

```bash
draw-things-cli generate \
  --model z_image_turbo_1.0_q8p.ckpt \
  --prompt "a small brass robot reading a field guide, cinematic light" \
  --steps 8 \
  --cfg 0 \
  --width 1024 \
  --height 1024 \
  --seed 1234 \
  --output /tmp/draw-thing-smoke.png
```

### Text/Layout Quality

```bash
draw-things-cli generate \
  --model qwen_image_2512_q8p.ckpt \
  --prompt "a clean editorial poster reading 'LOCAL MODELS 2026', precise typography, polished studio lighting" \
  --steps 40 \
  --cfg 4 \
  --width 1328 \
  --height 1328 \
  --seed 1234 \
  --output /tmp/draw-thing-qwen-smoke.png
```

### Img2img Edit

```bash
draw-things-cli generate \
  --model qwen_image_edit_2511_q8p.ckpt \
  --image /path/to/input.png \
  --prompt "change the jacket to deep emerald velvet while preserving face identity and background" \
  --strength 0.55 \
  --steps 30 \
  --cfg 4 \
  --seed 1234 \
  --output /tmp/draw-thing-edit.png
```

### Short Media

```bash
draw-things-cli generate \
  --model ltx_2.3_22b_distilled_q6p.ckpt \
  --prompt "a paper boat drifting across a moonlit pond, slow camera push, rippling reflections" \
  --frames 49 \
  --width 768 \
  --height 512 \
  --seed 1234 \
  --output /tmp/draw-thing-smoke.mov
```

### Variations With Shell Loop

```bash
for seed in 2201 2202 2203 2204; do
  draw-things-cli generate \
    --model z_image_turbo_1.0_q8p.ckpt \
    --prompt "four ceramic birds on a blue kitchen table, morning light" \
    --steps 8 \
    --cfg 0 \
    --width 1024 \
    --height 1024 \
    --seed "$seed" \
    --output "$HOME/Pictures/draw-thing/birds-$seed.png"
done
```

---

## Advanced Config Caveat

`--config-json` and `--config-file` apply Draw Things configuration overrides after model recommendations and before explicit flags. Use them for advanced settings only when you have verified the schema from a known-good Draw Things export or current docs.

Do not invent JSON keys for ControlNet, LoRA, inpaint, upscale, tiling, samplers, or refiner settings.
