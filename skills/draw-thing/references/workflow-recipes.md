# Workflow Recipes

Current Draw Things CLI recipes using exposed flags only. Load when the user asks for a multi-step workflow beyond a single generation.

---

## Recipe Index

1. [Setup The Current Recommended Pack](#1-setup-the-current-recommended-pack)
2. [Fast Draft To Quality Final](#2-fast-draft-to-quality-final)
3. [Typography Poster With Qwen 2512](#3-typography-poster-with-qwen-2512)
4. [Instruction Image Edit](#4-instruction-image-edit)
5. [Layered Editable Artwork](#5-layered-editable-artwork)
6. [HiDream Art Alternative](#6-hidream-art-alternative)
7. [Short Media Smoke Test](#7-short-media-smoke-test)
8. [Seed Variation Loop](#8-seed-variation-loop)
9. [Advanced Control Escalation](#9-advanced-control-escalation)

---

## 1. Setup The Current Recommended Pack

**Goal:** Ensure only the approved current pack is missing/downloaded, without deleting legacy models.

```bash
uv run python skills/draw-thing/scripts/model_inventory.py --recommended-pack all --format json
```

Run only missing `ensure_command` values from the JSON. Approved pack commands:

```bash
draw-things-cli models ensure --model hidream_i1_full_q5p.ckpt
draw-things-cli models ensure --model ltx_2.3_22b_distilled_q6p.ckpt
draw-things-cli models ensure --model wan_v2.2_5b_ti2v_q8p.ckpt
```

Qwen Layered is optional on this rig until a clean install succeeds. Do not retry its q6p or q8p artifacts automatically; both have failed or stalled through the CLI.

Do not prune legacy models without separate approval.

---

## 2. Fast Draft To Quality Final

**Goal:** Explore quickly with Z Image Turbo, then rebuild the selected idea with Qwen 2512.

**Step 1: Fast draft**

```bash
draw-things-cli generate \
  --model z_image_turbo_1.0_q8p.ckpt \
  --prompt "a lighthouse library built into black sea cliffs, storm clouds, warm windows, cinematic" \
  --steps 8 \
  --cfg 0 \
  --width 1024 \
  --height 1024 \
  --seed 4101 \
  --output "$HOME/Pictures/draw-thing/lighthouse-draft-4101.png"
```

**Step 2: Quality final with same seed**

```bash
draw-things-cli generate \
  --model qwen_image_2512_q8p.ckpt \
  --prompt "a lighthouse library built into black sea cliffs, storm clouds, warm glowing windows, cinematic editorial illustration, detailed stone texture, dramatic coastal atmosphere" \
  --steps 40 \
  --cfg 4 \
  --width 1328 \
  --height 1328 \
  --seed 4101 \
  --output "$HOME/Pictures/draw-thing/lighthouse-final-4101.png"
```

---

## 3. Typography Poster With Qwen 2512

**Goal:** Generate legible text and clean layout.

```bash
draw-things-cli generate \
  --model qwen_image_2512_q8p.ckpt \
  --prompt "a clean editorial poster reading 'LOCAL MODELS 2026' in precise bold sans-serif typography, centered grid layout, silver studio background, polished product lighting, high realism" \
  --steps 40 \
  --cfg 4 \
  --width 1328 \
  --height 1328 \
  --seed 1234 \
  --output "$HOME/Pictures/draw-thing/local-models-2026-1234.png"
```

If text is wrong, keep the seed and rewrite only the text/layout portion of the prompt.

---

## 4. Instruction Image Edit

**Goal:** Modify an existing image while preserving identity/composition.

```bash
draw-things-cli generate \
  --model qwen_image_edit_2511_q8p.ckpt \
  --image "$HOME/Pictures/source-portrait.png" \
  --prompt "Change the jacket to deep emerald velvet. Preserve the person's face, pose, lighting, and background." \
  --strength 0.55 \
  --steps 30 \
  --cfg 4 \
  --seed 2401 \
  --output "$HOME/Pictures/draw-thing/portrait-emerald-2401.png"
```

Use lower strength for identity preservation. Increase in 0.1 increments only when the edit is too weak.

---

## 5. Layered Editable Artwork

**Goal:** Create artwork intended for later layer manipulation.

```bash
draw-things-cli generate \
  --model qwen_image_layered_1.0_bf16_q8p.ckpt \
  --prompt "Create a layered product poster with separate perfume bottle foreground, headline text reading 'NIGHT GARDEN', dark botanical background, and mist effects, luxury editorial layout" \
  --steps 35 \
  --cfg 4 \
  --width 1328 \
  --height 1328 \
  --seed 3301 \
  --output "$HOME/Pictures/draw-thing/night-garden-layered-3301.png"
```

If Qwen Layered is missing, do not auto-download it. Explain the prior install failures and ask before retrying either optional artifact:

```bash
draw-things-cli models ensure --model qwen_image_layered_1.0_bf16_q6p.ckpt
draw-things-cli models ensure --model qwen_image_layered_1.0_bf16_q8p.ckpt
```

---

## 6. HiDream Art Alternative

**Goal:** Try a high-quality art/prompt-following alternative.

```bash
draw-things-cli generate \
  --model hidream_i1_full_q5p.ckpt \
  --prompt "a botanist mapping glowing fungi in an underground cathedral, oil-painted fantasy realism, low-angle composition, emerald bioluminescence and candlelight, intricate stone textures" \
  --steps 35 \
  --cfg 4 \
  --width 1024 \
  --height 1280 \
  --seed 5101 \
  --output "$HOME/Pictures/draw-thing/fungi-cathedral-5101.png"
```

If memory pressure appears, reduce dimensions before switching to HiDream Dev/Fast.

---

## 7. Short Media Smoke Test

**Goal:** Verify local media generation with LTX 2.3 distilled.

```bash
draw-things-cli generate \
  --model ltx_2.3_22b_distilled_q6p.ckpt \
  --prompt "a paper boat drifting across a moonlit pond, slow camera push, ripples spreading outward, silver reflections, calm continuous motion" \
  --frames 49 \
  --width 768 \
  --height 512 \
  --seed 1234 \
  --output "$HOME/Pictures/draw-thing/paper-boat-1234.mov"
```

Keep width and height divisible by 32. Keep frames divisible by 8 plus 1.

---

## 8. Seed Variation Loop

**Goal:** Replace old `--batch-count` with explicit shell loops.

```bash
mkdir -p "$HOME/Pictures/draw-thing"
for seed in 7001 7002 7003 7004; do
  draw-things-cli generate \
    --model z_image_turbo_1.0_q8p.ckpt \
    --prompt "four ceramic birds on a blue kitchen table, morning light, soft shadows" \
    --steps 8 \
    --cfg 0 \
    --width 1024 \
    --height 1024 \
    --seed "$seed" \
    --output "$HOME/Pictures/draw-thing/ceramic-birds-$seed.png"
done
```

Pick the strongest seed, then rerun with Qwen 2512 or Z Image Base for final quality.

---

## 9. Advanced Control Escalation

**Goal:** Handle a user request for ControlNet, LoRA, inpaint, or upscale without using stale direct flags.

1. Try current img2img first if the request is an edit:
   ```bash
   draw-things-cli generate \
     --model qwen_image_edit_2511_q8p.ckpt \
     --image "$HOME/Pictures/input.png" \
     --prompt "<edit instruction>. Preserve <important details>." \
     --strength 0.55 \
     --steps 30 \
     --cfg 4 \
     --seed 1234 \
     --output "$HOME/Pictures/draw-thing/edit-1234.png"
   ```
2. If strict controls are needed, import required assets:
   ```bash
   draw-things-cli models import /path/to/control-or-lora.safetensors
   ```
3. Ask for or create a verified Draw Things config file.
4. Run with `--config-file`; do not invent `--controls`, `--loras`, `--mask`, or `--upscaler` flags.

Template:

```bash
draw-things-cli generate \
  --model <compatible-model-id> \
  --prompt "<prompt>" \
  --image <input.png> \
  --config-file <verified-config.json> \
  --seed 1234 \
  --output <output.png>
```
