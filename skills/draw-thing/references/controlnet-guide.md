# Advanced Controls Guide

Guidance for ControlNet, LoRA, inpaint, upscale, and other advanced Draw Things workflows. Load when the user asks for structure control, LoRAs, masking, inpainting, or upscaling.

---

## Current CLI Boundary

The installed `draw-things-cli generate --help` in this environment does not expose direct flags for:

- `--controls`
- `--loras`
- `--mask`
- `--mask-blur`
- `--upscaler`
- `--upscaler-scale`
- `--hires-fix`

Therefore, do not run old direct-flag examples. Use one of these paths instead:

1. Use first-class current flags when enough: `--image`, `--strength`, `--prompt`, `--output`.
2. Import required assets with `draw-things-cli models import`.
3. Use Draw Things app-managed settings or a verified `--config-json` / `--config-file` workflow.
4. Ask for or inspect a known-good Draw Things config export before building advanced JSON.

---

## What Each Advanced Tool Does

| Tool                 | Purpose                                                | Current safe path                                                         |
| -------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------- |
| ControlNet           | Structural control from edges, depth, pose, tile, etc. | Import control model, then use verified config file                       |
| LoRA                 | Style, subject, or concept adapter                     | Import LoRA, then use verified config file or app preset                  |
| Inpaint              | Replace masked region                                  | Prefer app workflow or verified config because direct mask flag is absent |
| Upscale              | Increase resolution/enhance detail                     | Use app workflow or verified config; do not invent upscaler flags         |
| IP/reference adapter | Image reference/style conditioning                     | Use app/config after verifying schema                                     |

---

## Import Protocol

Draw Things optimized assets are preferred. External Hugging Face or CivitAI assets may work, but local file import is usually more reliable than URL import.

```bash
draw-things-cli models import /path/to/control-or-lora.safetensors
```

Before import:

1. Verify license and commercial constraints.
2. Verify base-family compatibility: SD1.5 controls for SD1.5, SDXL controls for SDXL, FLUX controls for FLUX, etc.
3. Prefer current models in `references/model-catalog.md`; legacy controls may force legacy base models.

---

## Config-File Protocol

Use `--config-file` only with a verified schema.

Recommended workflow:

1. Build the desired workflow in Draw Things app or obtain a trusted current config example.
2. Export or save the config JSON.
3. Inspect keys before running; do not guess keys.
4. Run a small smoke test with explicit `--output`.

Template:

```bash
draw-things-cli generate \
  --model <compatible-model-id> \
  --prompt "<prompt>" \
  --image <input-or-control-image> \
  --config-file <verified-config.json> \
  --seed <seed> \
  --output <output.png>
```

If the config contains model-specific values, do not silently swap model families.

---

## Img2img As Safe First Step

Many requested edits do not need ControlNet or LoRA. Start with current img2img when possible:

```bash
draw-things-cli generate \
  --model qwen_image_edit_2511_q8p.ckpt \
  --image ~/Pictures/input.png \
  --prompt "Change the background to a quiet winter street. Preserve the person, pose, and lighting." \
  --strength 0.55 \
  --steps 30 \
  --cfg 4 \
  --seed 1234 \
  --output ~/Pictures/draw-thing/edit-1234.png
```

Escalate to advanced controls only when the user needs strict pose/edge/depth fidelity, specific LoRA identity/style, masked replacement, or high-resolution upscaling.

---

## Control Strength Guidance

When a verified config exposes control weights, use these starting points:

| Control type       | Starting weight | Notes                                         |
| ------------------ | --------------- | --------------------------------------------- |
| Canny/edges        | 0.55-0.75       | Good for architecture, products, silhouettes. |
| Depth              | 0.45-0.65       | Better for scene layout and organic forms.    |
| Pose               | 0.6-0.8         | Strong enough to preserve human skeleton.     |
| Tile/upscale       | 0.35-0.55       | Keep lower to avoid overcooking detail.       |
| IP/style reference | 0.4-0.7         | Raise only if style transfer is too weak.     |

For multiple controls, reduce individual weights so the total influence stays near 0.8-1.0.

---

## LoRA Guidance

When a verified config exposes LoRA weights:

| Use case          | Starting weight    |
| ----------------- | ------------------ |
| Subtle style      | 0.35-0.55          |
| Strong style      | 0.65-0.85          |
| Subject/character | 0.6-0.9            |
| Multiple LoRAs    | Start 0.4-0.6 each |

If a LoRA was trained for SDXL/SD1.5, do not apply it to Qwen/Z/FLUX unless compatibility is verified.

---

## Escalation Checklist

Before running advanced workflows:

1. `draw-things-cli generate --help` confirms no simpler direct flag exists.
2. Required model/control/LoRA exists locally or has an approved import command.
3. Config JSON keys come from a current trusted source.
4. Source images are preserved and output goes to a new path.
5. The command is shown to the user before execution.

If any item fails, explain the blocker and ask for a config export, asset path, or approval to use the Draw Things app workflow.
