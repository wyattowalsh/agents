# Prompt Patterns

Prompt engineering reference for Draw Things CLI. Load when constructing complex prompts, troubleshooting quality issues, or working with a model family for the first time.

---

## Model Family Quick-Reference

| Family | Style | Negative Prompt | CFG Range |
|--------|-------|-----------------|-----------|
| **Flux** (Schnell / Dev / Klein) | Natural language sentences | **Not supported — omit entirely** | 1.0 |
| **SDXL** | Descriptive sentences, S-A-L-S structure | Short, targeted | 5–9 (default 7.0) |
| **SD 1.5** | Comma-separated tags, most important first | Aggressive — essential | 7–12 (default 7.5) |

---

## Flux Prompting

Flux understands natural language. Don't use tag lists or weighting syntax.

### Rules
- **No `--negative-prompt`** — omit the flag entirely; it is unsupported and may error.
- Frame exclusions positively: write *what you want*, not what to avoid.
  - ❌ "no extra fingers" → ✅ "hands with five fingers, correct anatomy"
  - ❌ "no blur" → ✅ "sharp focus, crisp detail"
- Subject first, then context, then technical/aesthetic qualifiers.
- Camera and lens terms work well: focal length, aperture, lighting type.

### Structure
```
[Subject with key traits], [scene/context], [lighting], [camera/lens], [style/mood]
```

### Examples

**Portrait:**
```
Portrait of a woman with auburn hair and freckles, soft studio lighting, 85mm lens,
f/1.8 bokeh, neutral gray backdrop, direct eye contact, photorealistic
```

**Environment:**
```
Vast salt flats at sunrise, mirror reflection of the sky in shallow standing water,
lone figure silhouetted at center, warm orange and pink gradient, aerial perspective
```

**Product:**
```
Minimalist wooden watch on a slate surface, dramatic side lighting, macro lens,
shallow depth of field, matte texture, lifestyle photography
```

**Text in image (Flux excels here):**
```
Vintage poster design reading "OPEN LATE" in bold serif lettering, worn edges,
muted red and cream palette, art deco style
```

### Quality Boosters (Flux)
Flux generally doesn't need quality tokens, but these help for specific looks:
- Photorealism: `photorealistic, hyperrealistic, shot on film`
- Illustration: `digital illustration, concept art, high detail`
- Cinematic: `cinematic still, movie frame, anamorphic lens`

---

## SDXL Prompting

SDXL bridges tags and natural language. Descriptive sentences outperform pure tag lists.

### Rules
- Subject → Action/State → Location → Style/Quality (S-A-L-S)
- Include a short, focused negative prompt — avoid piling in every bad token.
- CFG 7.0 default; raise to 9–10 for more literal adherence, lower to 5–6 for creative variation.
- Prompt weighting `(term:weight)` is supported — use sparingly (max 1.3–1.5 per term).

### Structure
```
[Subject + action], [location/environment], [lighting conditions], [style/quality tags]
```

### Examples

**Landscape:**
```
A medieval castle perched on a rocky coastal cliff, stormy sea below, dramatic
thunderclouds, golden shaft of light breaking through, highly detailed, masterpiece
```

**Portrait:**
```
Close-up portrait of an elderly fisherman with weathered skin, piercing blue eyes,
fishing harbor background, golden hour light, photorealistic, sharp focus
```

**Concept art:**
```
A biomechanical forest where trees have exposed cable roots and glowing sap,
fog settling between trunks, lone explorer in foreground, concept art,
cinematic composition, detailed environment
```

### Quality Boosters (SDXL)
Append to end of positive prompt:
```
highly detailed, masterpiece, best quality, 8k, sharp focus
```

For photorealism:
```
photorealistic, hyperrealistic, RAW photo, DSLR, sharp details, natural lighting
```

### Negative Prompt Template (SDXL)
```
ugly, deformed, low quality, blurry, watermark, signature, extra limbs,
poorly drawn hands, bad anatomy, cropped
```

**Targeted negatives by subject:**

| Subject | Add to negative |
|---------|----------------|
| Portraits | `bad face, asymmetric eyes, unnatural skin` |
| Architecture | `perspective distortion, leaning, fisheye` |
| Hands | `extra fingers, fused fingers, too many hands` |
| Animals | `deformed legs, unnatural proportions` |

---

## SD 1.5 Prompting

SD 1.5 thrives on comma-separated token lists. Tag order matters — earlier = more weight.

### Rules
- Most important terms first (subject, style, quality) — they get the most attention.
- Quality boosters belong at the front of the positive prompt.
- **Negative prompt is essential** — without it, SD 1.5 consistently produces low-quality output.
- CFG 7–9 sweet spot; above 12 causes oversaturation and artifacts.
- Prompt weighting `(term:1.3)` or emphasis `((term))` supported.

### Structure
```
[quality tokens], [subject], [style], [lighting], [composition], [medium/artist]
```

### Examples

**Portrait:**
```
masterpiece, best quality, 1girl, beautiful face, detailed eyes, studio lighting,
professional photography, sharp focus, 8k, detailed skin, realistic
```

**Landscape:**
```
masterpiece, best quality, mountain valley, autumn forest, river reflections,
golden hour, dramatic lighting, detailed foliage, cinematic, wide angle
```

**Anime:**
```
masterpiece, best quality, anime style, 1girl, school uniform, cherry blossoms,
detailed background, bright colors, sharp lines, studio lighting
```

### Quality Boosters (SD 1.5)
Place at the beginning of your positive prompt:
```
masterpiece, best quality, highres, 8k, sharp focus, highly detailed
```

For photorealism:
```
(RAW photo:1.2), (photorealistic:1.4), DSLR, 8k UHD, sharp
```

For illustration:
```
masterpiece, best quality, digital art, concept art, detailed illustration
```

### Negative Prompt Template (SD 1.5) — Universal Base
```
(worst quality:2), (low quality:2), (normal quality:2), lowres, bad anatomy,
bad hands, ((missing fingers)), extra digit, fewer digits, blurry, text,
watermark, signature, jpeg artifacts, ugly, duplicate, morbid, mutilated,
out of frame, extra limbs, disfigured, gross proportions, malformed limbs
```

**Category-specific additions:**

| Category | Append to negative |
|----------|--------------------|
| Portraits | `bad face, crossed eyes, uneven eyes, asymmetric face` |
| Landscapes | `overexposed, flat, lack of depth` |
| Anime | `realistic, 3d render, photographic` |
| Product photo | `shadow artifacts, chromatic aberration, fisheye` |

### Textual Inversion Embeddings (SD 1.5)
Place embedding tokens in the negative prompt to activate them (must be downloaded to models dir):

| Embedding | Effect | Usage |
|-----------|--------|-------|
| `EasyNegative` | General quality | Add to negative |
| `BadDream` | Reduce anatomical errors | Add to negative |
| `ng_deepnegative_v1_75t` | Reduce deep negatives | Add to negative |

Example negative with embeddings:
```
EasyNegative, BadDream, (worst quality:2), (low quality:2), bad anatomy, bad hands
```

> **Note:** Verify embedding filenames match your downloaded files. Names may vary.

---

## Prompt Weighting Syntax

Supported in **SD 1.5** and **SDXL**. Not applicable to Flux.

| Syntax | Effect | Example |
|--------|--------|---------|
| `(term:1.3)` | Increase weight to 1.3× | `(masterpiece:1.4)` |
| `(term:0.8)` | Decrease weight to 0.8× | `(blurry:0.1)` |
| `((term))` | Roughly 1.21× (square of 1.1) | `((detailed eyes))` |
| `[term]` | Roughly 0.91× | `[background]` |

**Guidelines:**
- Stay in the 0.5–1.5 range; extremes cause artifacts.
- Don't over-weight everything — relative balance matters more than absolute values.
- Verify current weighting syntax support with `draw-things-cli generate --help` if behavior seems off.

---

## Wildcard Syntax

SD 1.5 and SDXL support wildcard expansion (verify if this is enabled in your Draw Things build):
```
a {red|blue|golden} dragon flying over {mountains|ocean|forest}
```

> If wildcards don't expand, Draw Things may not have this feature enabled. Check `draw-things-cli generate --help`.

---

## Negative Prompt: Model Compatibility

| Feature | Flux | SDXL | SD 1.5 |
|---------|------|------|--------|
| Negative prompt | ❌ No | ✅ Yes (short) | ✅ Essential |
| Weighting `(term:n)` | ❌ No | ✅ Yes | ✅ Yes |
| Textual inversions | ❌ No | ⚠️ Limited | ✅ Yes |
| BREAK keyword | ❌ No | ⚠️ Verify | ✅ Yes |

---

## Common Issues & Fixes

| Problem | Likely Cause | Fix |
|---------|-------------|-----|
| Distorted hands/fingers | Insufficient negative | Add `bad hands, extra fingers` to negative |
| Over-saturated colors | CFG too high | Lower `--guidance-scale` (try 6.5–7.5 for SD 1.5) |
| Flat, low-quality output (SD 1.5) | Missing quality tokens | Add `masterpiece, best quality` to front of prompt |
| Prompt not followed | CFG too low | Raise `--guidance-scale` by 1–2 |
| Too many steps wasted | Steps too high | 20–30 is sufficient for most samplers |
| Flux output ignoring words | Natural language order off | Put subject first, qualifiers last |

