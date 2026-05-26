# Prompt Patterns

Prompt guidance for the current Draw Things recommended model pack. Load when constructing complex prompts, troubleshooting output quality, or switching model families.

---

## Model Family Quick Reference

| Family          | Prompt style                                                       | CFG starting point   | Negative prompt                                   |
| --------------- | ------------------------------------------------------------------ | -------------------- | ------------------------------------------------- |
| Z Image Turbo   | Short natural-language instructions; clear subject and composition | `0`                  | Usually omit                                      |
| Z Image Base    | Natural-language scene plus style/control details                  | `3-5`                | Short targeted negatives when useful              |
| Qwen Image 2512 | Explicit layout, exact text, typography, realism/detail            | `4`                  | Short targeted negatives                          |
| Qwen Edit 2511  | Imperative edit instruction plus what to preserve                  | `4`                  | Use only for avoid-changing constraints           |
| Qwen Layered    | Describe layer separation and editable elements                    | `4`                  | Minimal                                           |
| FLUX.2 Dev      | Natural language with reference/edit intent                        | `2-4`                | Verify model behavior; do not assume FLUX.1 rules |
| HiDream I1 Full | Rich art direction, medium, composition, lighting                  | `3-5`                | Short targeted negatives                          |
| LTX / Wan media | Temporal action, camera motion, continuity                         | model default or `1` | Avoid still-image tag negatives                   |

---

## Z Image Patterns

Use for fast current drafts and general creative work.

### Fast Draft Structure

```text
[subject], [scene/context], [lighting], [composition], [style]
```

Example:

```text
A compact brass robot reading a field guide in a mossy forest, cinematic side light, shallow depth of field, warm curious mood
```

For Turbo, keep prompts concise and start with `--steps 8 --cfg 0`.

### Base Creative Structure

```text
[subject with traits], [environment], [visual style], [color palette], [camera/framing], [finish]
```

Example:

```text
An arctic research greenhouse at blue hour, translucent geodesic panels glowing from within, teal and amber palette, wide establishing shot, polished sci-fi concept art
```

---

## Qwen Image 2512 Patterns

Use for typography, posters, labels, product layouts, editorial images, and realism.

### Text/Layout Structure

```text
[format] reading "[exact text]", [layout constraints], [subject], [style], [lighting], [quality]
```

Example:

```text
A clean editorial poster reading "LOCAL MODELS 2026" in precise bold sans-serif typography, centered grid layout, silver studio background, polished product lighting, high realism
```

### Realism Structure

```text
[subject], realistic natural detail, [environment], [lens/lighting], [specific constraints]
```

Example:

```text
A chef plating a citrus tart in a quiet restaurant kitchen, realistic skin and fabric detail, stainless steel counters, soft overhead work lights, 50mm documentary photography
```

For text, quote exact words and specify placement. Avoid vague requests like "add some text".

---

## Qwen Edit 2511 Patterns

Use imperative edit prompts and preservation constraints.

### Edit Structure

```text
Change [target] to [new attribute]. Preserve [identity/composition/background]. Keep [important constraints].
```

Examples:

```text
Change the jacket to deep emerald velvet. Preserve the person's face, pose, lighting, and background.
```

```text
Replace the coffee mug with a clear glass teacup. Preserve the table, hands, camera angle, and morning light.
```

Start at `--strength 0.45-0.6`. Raise only if the requested change is not visible.

---

## Qwen Layered Patterns

Use when the output should separate foreground, text, background, or product parts for later edits.

### Layered Structure

```text
Create a layered image with separate [foreground], [text], [background], and [effects] elements. [Style and layout].
```

Example:

```text
Create a layered product poster with separate perfume bottle foreground, headline text reading "NIGHT GARDEN", dark botanical background, and mist effects, luxury editorial layout
```

---

## FLUX.2 Patterns

Use natural language and precise intent. FLUX.2 is current high-end but not the fast default on this rig.

### Structure

```text
[Subject and action] in [scene], [specific visual constraints], [camera/framing], [mood/style]
```

Example:

```text
A ceramic fox curled beside a rainy window in a quiet bookshop, reflections on glass, warm tungsten interior light, 35mm cinematic still, gentle melancholy
```

Do not carry over blanket FLUX.1 rules. Verify negative-prompt behavior on the selected FLUX.2 model before using it.

---

## HiDream I1 Full Patterns

Use for rich art direction, illustration, and high-quality prompt following.

### Structure

```text
[Subject], [medium/style], [composition], [lighting], [palette], [detail level]
```

Example:

```text
A botanist mapping glowing fungi in an underground cathedral, oil-painted fantasy realism, low-angle composition, emerald bioluminescence and candlelight, intricate stone textures
```

If output is slow or memory-heavy, reduce dimensions before switching away from Full.

---

## Media Prompt Patterns

Video/media prompts need time, motion, and camera direction.

### Structure

```text
[Subject] [does what over time], [camera movement], [environment changes], [lighting/mood], [continuity constraints]
```

Examples:

```text
A paper boat drifting across a moonlit pond, slow camera push, ripples spreading outward, silver reflections, calm continuous motion
```

```text
A red tram gliding through a rainy neon street at night, side tracking shot, pedestrians with umbrellas passing in soft blur, reflections shimmering on pavement
```

Avoid still-image-only tags such as "masterpiece, 8k" unless the model benefits from them. Specify motion instead.

---

## Refinement Patterns

Change one variable at a time:

| Problem               | First prompt fix                               | Parameter fix                 |
| --------------------- | ---------------------------------------------- | ----------------------------- |
| Composition wrong     | Put layout constraints earlier                 | Lock seed, adjust prompt only |
| Text misspelled       | Quote exact text and specify font/placement    | Use Qwen 2512, increase steps |
| Edit changes identity | Add preservation sentence                      | Lower `--strength`            |
| Too static video      | Add explicit motion verbs and camera movement  | Increase frames modestly      |
| Too generic           | Add materials, era, palette, lens, environment | Try HiDream or Z Image Base   |

---

## Legacy Prompting Note

SDXL and SD 1.5 tag-heavy patterns are legacy compatibility guidance only. Do not select them for current best-pack work unless the user explicitly needs an old LoRA/checkpoint ecosystem.
