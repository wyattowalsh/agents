# Workflow Recipes

Multi-step creative workflows for Draw Things CLI. Each recipe is a complete pipeline with numbered steps and real CLI commands. Load when the user has a complex creative goal that goes beyond a single generation.

---

## Recipe Index

1. [Quick Prototype → Best Seed Selection](#1-quick-prototype--best-seed-selection)
2. [Character Design Pipeline](#2-character-design-pipeline)
3. [Photo Restoration](#3-photo-restoration)
4. [Style Transfer](#4-style-transfer)
5. [Concept Art Iteration](#5-concept-art-iteration)
6. [Pose-Guided Character Generation](#6-pose-guided-character-generation)
7. [Edge-Guided Redesign (Canny)](#7-edge-guided-redesign-canny)
8. [Hi-Res from Scratch](#8-hi-res-from-scratch)
9. [Inpainting Workflow](#9-inpainting-workflow)

---

## 1. Quick Prototype → Best Seed Selection

**Goal:** Fast exploration to find a composition worth developing.  
**Model:** Flux Schnell or Klein (4 steps, ~1-2s per image)  
**Time:** < 60 seconds for 8 variations

### Steps

**Step 1: Generate 4–8 fast variations**
```bash
draw-things-cli generate \
  --model flux_1_schnell_q5p.ckpt \
  --prompt "A lone lighthouse on a rocky coast, stormy sky, crashing waves, cinematic" \
  --width 1024 --height 1024 \
  --steps 4 --guidance-scale 1.0 \
  --sampler "Euler a" \
  --batch-count 4 \
  --seed -1
```

**Step 2: Note the seed of the best result** (reported in CLI output)

**Step 3: Lock seed, refine the prompt**
```bash
draw-things-cli generate \
  --model flux_1_schnell_q5p.ckpt \
  --prompt "A lone lighthouse on a rocky coast, stormy Atlantic sky, waves crashing on boulders, lighthouse beam cutting through rain, cinematic, wide angle" \
  --width 1024 --height 1024 \
  --steps 4 --guidance-scale 1.0 \
  --sampler "Euler a" \
  --seed 12345
```

**Step 4: Switch to Flux Dev for final quality**
```bash
draw-things-cli generate \
  --model flux_1_dev_q6p.ckpt \
  --prompt "<same refined prompt>" \
  --width 1024 --height 1024 \
  --steps 30 --guidance-scale 1.0 \
  --sampler "Euler a" \
  --seed 12345
```

> Schnell and Dev share the same latent space, so the same seed often produces similar compositions across them — useful for fast → quality transitions.

---

## 2. Character Design Pipeline

**Goal:** Consistent, detailed character at multiple angles and expressions.  
**Model:** SDXL (Juggernaut XL recommended) or Flux Dev

### Steps

**Step 1: Establish the base character (front view)**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --prompt "character design, young female knight, silver armor with blue trim, short brown hair, green eyes, neutral expression, white background, highly detailed, masterpiece, character sheet" \
  --negative-prompt "ugly, deformed, bad anatomy, blurry, watermark" \
  --width 1024 --height 1024 \
  --steps 25 --guidance-scale 7.5 \
  --seed -1
```

**Step 2: Note the seed. Lock it for all subsequent variations.**

**Step 3: Generate 3/4 view (prompt-only variation)**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --prompt "character design, young female knight, silver armor with blue trim, short brown hair, green eyes, 3/4 view, white background, highly detailed, masterpiece" \
  --negative-prompt "ugly, deformed, bad anatomy, blurry, watermark" \
  --width 1024 --height 1024 \
  --steps 25 --guidance-scale 7.5 \
  --seed 12345
```

**Step 4: Generate action pose (use img2img from step 1 at low strength OR ControlNet pose)**
```bash
# img2img approach: preserves character traits, changes pose loosely
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/character-base.png \
  --prompt "female knight, dynamic battle pose, sword raised, silver armor, dramatic lighting" \
  --negative-prompt "ugly, deformed, bad anatomy, blurry" \
  --strength 0.65 \
  --steps 25 --guidance-scale 7.5 \
  --seed 12345
```

**Step 5: Upscale the hero shot**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/character-final.png \
  --upscaler realesrgan_x4plus_f16.ckpt \
  --upscaler-scale 4 \
  --strength 0.25 \
  --steps 30
```

---

## 3. Photo Restoration

**Goal:** Improve a degraded, damaged, or low-quality photo.  
**Model:** SDXL or SD 1.5 (Realistic Vision recommended for SD 1.5)

### Steps

**Step 1: Light img2img pass to restore overall quality**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/old-photo.png \
  --prompt "high quality photo, sharp details, natural lighting, photorealistic" \
  --negative-prompt "damaged, scratched, low quality, blurry, faded, sepia, noise" \
  --strength 0.35 \
  --steps 30 --guidance-scale 7.0
```
> Keep `--strength` low (0.2–0.4) to preserve original composition while improving quality.

**Step 2: Inpaint specific damaged areas**

Create a mask (white = repaint, black = preserve) in any image editor, then:
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/restored-pass1.png \
  --mask ~/Pictures/damage-mask.png \
  --prompt "intact photo surface, no scratches, sharp detail" \
  --negative-prompt "damaged, scratched, noise" \
  --strength 0.75 \
  --mask-blur 4 \
  --steps 30 --guidance-scale 7.0
```

**Step 3: Upscale the restored result**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/restored-inpainted.png \
  --upscaler realesrgan_x4plus_f16.ckpt \
  --upscaler-scale 4 \
  --strength 0.2 \
  --steps 30
```

---

## 4. Style Transfer

**Goal:** Apply the visual style of a reference artwork or description to an existing image.  
**Model:** SDXL or SD 1.5

### Approach A: Prompt-driven (no reference image needed)

```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/source-photo.png \
  --prompt "oil painting, impressionist style, thick brushstrokes, vibrant colors, painted texture" \
  --negative-prompt "photograph, photorealistic, digital art" \
  --strength 0.75 \
  --steps 25 --guidance-scale 7.0
```

**Adjust `--strength` by target:**
- 0.4–0.5: Light stylization, preserve most content
- 0.65–0.75: Clear style shift, content still recognizable
- 0.85+: Heavy transformation, loose content preservation

### Approach B: Style + LoRA

```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/source-photo.png \
  --prompt "studio ghibli style, anime, painterly, detailed landscape" \
  --negative-prompt "photorealistic, photograph" \
  --loras '[{"file": "ghibli_style_xl.safetensors", "weight": 0.7}]' \
  --strength 0.7 \
  --steps 25 --guidance-scale 7.0
```

> LoRA weight 0.7 is a good starting point. Raise to 0.9 for stronger style influence, lower to 0.5 if the LoRA overwhelms the content.

### Approach C: IP-Adapter (style from reference image)

```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/source-photo.png \
  --prompt "high quality, detailed" \
  --controls '[{"file": "ip_adapter_xl.safetensors", "weight": 0.6, "guidanceStart": 0.0, "guidanceEnd": 1.0, "controlMode": "Balanced"}]' \
  --strength 0.6 \
  --steps 25 --guidance-scale 6.0
```

> Verify IP-Adapter flag syntax with `draw-things-cli generate --help` — it may require different parameters than standard ControlNet.

---

## 5. Concept Art Iteration

**Goal:** Explore multiple design directions, then converge on the best one.  
**Model:** SDXL or Flux Dev

### Steps

**Step 1: Generate batch of divergent variations (unlock seed)**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --prompt "futuristic vehicle concept, sleek aerodynamic design, carbon fiber panels, LED accents, side view, white background, concept art, product design" \
  --negative-prompt "ugly, deformed, low quality" \
  --width 1216 --height 832 \
  --steps 25 --guidance-scale 7.0 \
  --batch-count 6 \
  --seed -1
```

**Step 2: Identify the 1–2 best candidates. Note their seeds.**

**Step 3: Refine each candidate independently (locked seed, prompt adjustments)**
```bash
# Refining candidate A
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --prompt "futuristic vehicle concept, sleek aerodynamic design, matte black carbon fiber, electric blue LED accents, racing stance, side view, studio lighting, product visualization" \
  --negative-prompt "ugly, deformed, low quality, background elements" \
  --width 1216 --height 832 \
  --steps 25 --guidance-scale 7.5 \
  --seed 11111
```

**Step 4: Run img2img on the best result to push further**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/vehicle-candidate-A.png \
  --prompt "photorealistic 3D render, studio lighting, highly detailed surface, perfect reflections" \
  --negative-prompt "concept art, sketch, painterly" \
  --strength 0.45 \
  --steps 30 --guidance-scale 7.0
```

**Step 5: Upscale the selected final**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/vehicle-final.png \
  --upscaler 4x_ultrasharp_f16.ckpt \
  --upscaler-scale 4 \
  --strength 0.3 \
  --steps 30
```

---

## 6. Pose-Guided Character Generation

**Goal:** Generate a character in a specific body position from a pose reference.  
**Model:** SDXL (requires SDXL OpenPose ControlNet)

### Steps

**Step 1: Source or create a pose image**
- Use a photo, 3D mannequin render, or pose extracted from another image
- The pose image should be the same dimensions as your target output

**Step 2: Generate with Pose ControlNet**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/pose-reference.png \
  --prompt "powerful male wizard, flowing dark robes, casting a spell, dramatic purple energy, stone castle background, dramatic lighting, highly detailed" \
  --negative-prompt "ugly, deformed, bad anatomy, extra limbs" \
  --controls '[{"file": "control_openpose_xl.safetensors", "weight": 0.75, "guidanceStart": 0.0, "guidanceEnd": 0.6, "controlMode": "Balanced"}]' \
  --width 1024 --height 1536 \
  --steps 25 --guidance-scale 7.0 \
  --seed -1
```

**Step 3: Iterate with locked seed if pose is good**
- If pose is correct but details are off: lock seed, adjust prompt
- If pose is wrong: try a different pose image or raise ControlNet weight to 0.85

**Step 4: Upscale**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/wizard-final.png \
  --upscaler realesrgan_x4plus_f16.ckpt \
  --upscaler-scale 4 \
  --strength 0.25 \
  --steps 30
```

---

## 7. Edge-Guided Redesign (Canny)

**Goal:** Keep the exact composition and silhouette of a source image but apply a completely different style or content.  
**Model:** SDXL

### Steps

**Step 1: Use your source image as the Canny control input**
Draw Things will extract the edge map automatically if you provide the raw image. If you need to pre-extract, use an external tool (ImageMagick, Photoshop, etc.).

**Step 2: Generate with Canny ControlNet**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/source-building.png \
  --prompt "fantasy castle, magical glowing windows, ivy-covered stone walls, misty forest background, dramatic lighting, highly detailed" \
  --negative-prompt "modern, ugly, low quality" \
  --controls '[{"file": "control_canny_xl.safetensors", "weight": 0.7, "guidanceStart": 0.0, "guidanceEnd": 1.0, "controlMode": "Balanced"}]' \
  --width 1024 --height 1024 \
  --steps 25 --guidance-scale 7.0
```

**Step 3: Tune the Canny weight**
- Output too rigid / looks like a traced image: lower weight to 0.5
- Composition drifting from original: raise weight to 0.8–0.9
- Try `controlMode: "Prompt"` for more creative freedom while maintaining rough structure

**Step 4: Inpaint any areas that need attention**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/redesign-v1.png \
  --mask ~/Pictures/sky-mask.png \
  --prompt "dramatic sunset sky, orange and purple clouds, epic atmosphere" \
  --strength 0.75 \
  --mask-blur 6 \
  --steps 25
```

---

## 8. Hi-Res from Scratch

**Goal:** Generate a high-resolution image in a single pipeline using hi-res fix, then push further with an upscaler.  
**Model:** SDXL or SD 1.5

### Steps

**Step 1: Generate at model-native resolution with hi-res fix**

> **Verify hi-res fix flags** with `draw-things-cli generate --help` — exact flag names (`--hires-fix`, `--hires-fix-width`, `--hires-fix-strength`) should be confirmed before use.

```bash
# SDXL: native 1024×1024, hi-res fix to 2048×2048
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --prompt "ancient library with towering bookshelves, dramatic shafts of light, floating magical books, detailed architecture, masterpiece" \
  --negative-prompt "ugly, blurry, low quality" \
  --width 1024 --height 1024 \
  --steps 25 --guidance-scale 7.0 \
  --hires-fix \
  --hires-fix-width 2048 --hires-fix-height 2048 \
  --hires-fix-strength 0.7 \
  --seed -1
```

**Step 2: Upscale further with Real-ESRGAN for pixel-level sharpness**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/library-hires.png \
  --upscaler 4x_ultrasharp_f16.ckpt \
  --upscaler-scale 4 \
  --strength 0.2 \
  --steps 30
```

**Alternative for SD 1.5 (512 → 1024 hi-res fix):**
```bash
draw-things-cli generate \
  --model v1-5-pruned-emaonly.ckpt \
  --prompt "masterpiece, best quality, ancient library, magical, detailed" \
  --negative-prompt "(worst quality:2), (low quality:2), blurry" \
  --width 512 --height 512 \
  --steps 25 --guidance-scale 7.5 \
  --hires-fix \
  --hires-fix-width 1024 --hires-fix-height 1024 \
  --hires-fix-strength 0.7
```

---

## 9. Inpainting Workflow

**Goal:** Replace a specific region of an image while blending naturally with surroundings.  
**Model:** SDXL or SD 1.5

### Steps

**Step 1: Generate or select a base image**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --prompt "portrait of a woman, outdoor park setting, sunny day" \
  --width 1024 --height 1024 \
  --steps 25 --guidance-scale 7.0 \
  --seed 99999
```

**Step 2: Create a mask**
- White pixels = area to repaint
- Black pixels = area to preserve
- Use any image editor: Preview, Photoshop, GIMP, Pixelmator
- Save as PNG, same dimensions as the source image

**Step 3: Inpaint the masked region**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/portrait-base.png \
  --mask ~/Pictures/background-mask.png \
  --prompt "busy city street background, tall buildings, afternoon light, bokeh" \
  --negative-prompt "ugly, low quality, blurry" \
  --strength 0.75 \
  --mask-blur 4 \
  --steps 30 --guidance-scale 7.0
```

> **Prompt tip:** Describe only what goes in the masked area — not the full image. The model knows the surrounding context.

**Step 4: Tune if seams are visible**
- Visible hard edge: increase `--mask-blur` to 8–12
- New content looks disconnected: lower `--strength` to 0.6 and increase steps
- New content too similar to original: raise `--strength` to 0.85

**Step 5: Upscale if needed**
```bash
draw-things-cli generate \
  --model sd_xl_base_1.0.safetensors \
  --image ~/Pictures/draw-thing/portrait-inpainted.png \
  --upscaler realesrgan_x4plus_f16.ckpt \
  --upscaler-scale 2 \
  --strength 0.2 \
  --steps 30
```
