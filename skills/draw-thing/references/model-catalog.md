# Draw Things — Model Catalog

Reference for model families, checkpoint recommendations, SDXL resolutions, and quantization. Load when the user asks about models or when choosing between model variants.

---

## Model Selection Decision Tree

```
Need text in images?  ──yes──►  Flux Dev or Flux Schnell
        │no
        ▼
Huge LoRA library needed?  ──yes──►  SD 1.5 (most mature ecosystem)
        │no
        ▼
Fast prototype (≤4 steps)?  ──yes──►  Flux Schnell or Flux Klein
        │no
        ▼
Best quality, no rush?  ──yes──►  Flux Dev or SDXL (Juggernaut XL)
        │no
        ▼
Low VRAM / oldest hardware?  ──yes──►  SD 1.5 (4–6 GB)
        │no
        ▼
Default recommendation:  SDXL (Juggernaut XL) or Flux Dev
```

---

## Flux Variants

| Variant | `--model` filename | Steps | CFG | Sampler | Speed | License |
|---------|--------------------|-------|-----|---------|-------|---------|
| **Flux Schnell** | `flux_1_schnell_q5p.ckpt` | 4 | 1.0 | `"Euler a"` | Very fast (~1–2s) | Apache 2.0 |
| **Flux Dev** | `flux_1_dev_q6p.ckpt` | 30 | 1.0 | `"Euler a"` | Moderate | Non-commercial |
| **Flux Klein 4B** | `flux_2_klein_4b_q6p.ckpt` | 4 | 1.0 | `"DPM++ 2M AYS"` | Very fast | Verify license |
| **Flux Klein 9B** | `flux_2_klein_9b_q6p.ckpt` | 8 | 1.0 | `"DPM++ 2M AYS"` | Fast | Verify license |

**Flux critical notes:**
- **No negative prompt support.** Omit `--negative-prompt` entirely.
- Native resolution: 1024×1024.
- Prompt style: natural language sentences, subject-first.
- Dramatically better text rendering than SD 1.5 or SDXL.
- Quantized filenames above are common community conventions — verify actual filenames in your models directory with `ls *.ckpt *.safetensors`.

---

## SDXL Checkpoints

Native resolution: **1024×1024** (see resolution table below).

| Checkpoint | Filename | Strength | Best for |
|------------|----------|----------|----------|
| **Juggernaut XL** | `juggernautXL_*.safetensors` | Photorealism | Portraits, photorealistic scenes |
| **RealVisXL** | `RealVisXL_*.safetensors` | Photorealism | Real-world photography style |
| **DreamShaper XL** | `dreamshaperXL_*.safetensors` | Balanced | Artistic, versatile |
| **Pony V6** | `ponyDiffusionV6XL_*.safetensors` | Stylized | Anime, cartoon, stylized art |
| **SDXL Base** | `sd_xl_base_1.0.safetensors` | General | Baseline, default fallback |

**SDXL settings:**
- Steps: 25 | CFG: 7.0 | Sampler: `"DPM++ 2M Karras"`
- Prompt style: descriptive sentences, Subject-Action-Location-Style structure
- Negative prompt: short and targeted (5–10 words)

Verify exact filenames in your models directory — community checkpoints use varied naming conventions.

---

## SD 1.5 Checkpoints

Native resolution: **512×512**.

| Checkpoint | Filename | Strength | Best for |
|------------|----------|----------|----------|
| **Realistic Vision** | `realisticVision_*.safetensors` | Photorealism | Portraits, people |
| **DreamShaper 8** | `dreamshaper_8.safetensors` | Balanced | General purpose, versatile |
| **Anything V5** | `anything-v5-*.ckpt` | Anime/illustration | Anime, 2D art |
| **epiCRealism** | `epicrealism_*.safetensors` | Photorealism | Natural scenes, landscapes |
| **Deliberate** | `deliberate_*.safetensors` | Semi-realistic | Concept art, characters |
| **SD 1.5 Base** | `v1-5-pruned-emaonly.ckpt` | General | Baseline, broad compatibility |

**SD 1.5 settings:**
- Steps: 25 | CFG: 7.5 | Sampler: `"DPM++ 2M Karras"`
- Prompt style: comma-separated tags, most important first
- Negative prompt: aggressive (20–40 words); see `references/prompt-patterns.md`
- Best LoRA and embedding ecosystem (CivitAI, Hugging Face)

---

## SDXL Recommended Resolutions

SDXL was trained on a specific set of aspect ratios. Use these to avoid conditioning artifacts.

| Aspect Ratio | Width × Height | Use for |
|-------------|----------------|---------|
| 1:1 (square) | 1024 × 1024 | Default, portraits |
| 4:3 | 1152 × 896 | Landscape standard |
| 3:2 | 1216 × 832 | Photography standard |
| 16:9 | 1344 × 768 | Widescreen |
| 21:9 | 1536 × 640 | Cinematic ultra-wide |
| 3:4 (portrait) | 896 × 1152 | Portrait photos |
| 2:3 (portrait) | 832 × 1216 | Tall portrait |
| 9:16 (portrait) | 768 × 1344 | Mobile / story format |

> Using non-listed resolutions is possible but may produce lower quality or compositional artifacts. Stick to these for best SDXL results.

---

## SD 1.5 Recommended Resolutions

SD 1.5 native: **512×512**. Higher resolutions work but risk duplication artifacts; use hi-res fix instead.

| Size | Notes |
|------|-------|
| 512 × 512 | Native — best quality baseline |
| 512 × 768 | Portrait (common, well-supported) |
| 768 × 512 | Landscape (common, well-supported) |
| 768 × 768 | Larger square — use hi-res fix for quality |

For anything above 768px, use hi-res fix (`--hires-fix`) or generate at 512px and upscale separately.

---

## Quantization Guide

Draw Things uses GGUF-style quantization suffixes. Higher quality = more VRAM.

| Suffix | Bits per weight | VRAM (SDXL) | Quality | Use when |
|--------|----------------|-------------|---------|----------|
| `_f16` | 16-bit float | ~12 GB | Best | Plenty of VRAM, max quality |
| `_q8_0` | 8-bit | ~8 GB | Excellent | Good balance, minimal quality loss |
| `_q6p` / `_q6_k` | 6-bit | ~7 GB | Very good | Recommended default for Flux |
| `_q5p` / `_q5_k_m` | 5-bit | ~6 GB | Good | Flux Schnell fast inference |
| `_q4_k_m` | 4-bit | ~5 GB | Acceptable | Low VRAM, still usable |

**Rule of thumb:** Use `q6p` or `q6_k` for Flux models. Use `f16` or `q8_0` for SDXL when VRAM allows. Avoid `q4` for anything requiring fine detail.

> Quantization naming varies between models and community releases. Check the actual filename in your models directory.

---

## Model File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| **Checkpoint** | `.ckpt` | Original PyTorch format. Auto-detected by Draw Things. |
| **SafeTensors** | `.safetensors` | Preferred for safety and speed. Auto-detected. |

Draw Things auto-detects the format from the file extension. Either works with `--model`.

---

## Model Directory

Default path:
```
~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models
```

Override with environment variable:
```bash
export DRAWTHINGS_MODELS_DIR="/path/to/your/models"
```

List available models:
```bash
ls "${DRAWTHINGS_MODELS_DIR:-$HOME/Library/Containers/com.liuliu.draw-things/Data/Documents/Models}"/*.{ckpt,safetensors} 2>/dev/null
```

---

For model-family defaults (steps, CFG, sampler, dimensions), see the Model Quick-Reference table in SKILL.md.
