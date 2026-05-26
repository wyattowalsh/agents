# Draw Things Model Catalog

Rig-aware model guidance for Draw Things CLI. This catalog reflects the approved current pack for Apple M1 Pro, 32 GiB unified memory, arm64, macOS 26.5, on 2026-05-15.

---

## Current Decision Tree

```text
Need fastest current still image?      -> z_image_turbo_1.0_q8p.ckpt
Need text/layout/high realism?         -> qwen_image_2512_q8p.ckpt
Need creative controllable base?       -> z_image_1.0_q8p.ckpt
Need instruction edit of an image?     -> qwen_image_edit_2511_q8p.ckpt
Need high-benchmark art alternative?   -> hidream_i1_full_q5p.ckpt
Need FLUX.2 reference/edit workflows?  -> flux_2_dev_q6p.ckpt
Need short local video/media?          -> ltx_2.3_22b_distilled_q6p.ckpt
Need current Wan video on this rig?    -> wan_v2.2_5b_ti2v_q8p.ckpt
```

Default to these current models. Treat SDXL, SD 1.5, SD 2.x, SVD, FLUX.1, Qwen 1.0, Qwen Edit 2509, Wan 2.1, and old community checkpoints as legacy compatibility only.

Do not confuse generation/media model ids with helper files. Local text encoders, VLMs, chat models, tensor-data sidecars, and incomplete `.part` files may exist in the Models directory as dependencies or interrupted downloads; they are not part of the best current generation pack unless they appear in the recommended tables below.

Qwen Layered is current, but it is not in the guaranteed best effective pack for this Mac after repeated installation failures: `qwen_image_layered_1.0_bf16_q6p.ckpt` failed verification with a checksum mismatch, and `qwen_image_layered_1.0_bf16_q8p.ckpt` repeatedly stalled through the CLI. Treat it as optional until a clean install succeeds.

---

## Recommended Pack

### Image Pack

| Role                             | Model id                        | Download command                                                      | Notes                                     |
| -------------------------------- | ------------------------------- | --------------------------------------------------------------------- | ----------------------------------------- |
| Fast image default               | `z_image_turbo_1.0_q8p.ckpt`    | `draw-things-cli models ensure --model z_image_turbo_1.0_q8p.ckpt`    | Fast distilled Z Image, good first pass.  |
| Best text/layout/realism         | `qwen_image_2512_q8p.ckpt`      | `draw-things-cli models ensure --model qwen_image_2512_q8p.ckpt`      | Use for posters, labels, precise text.    |
| Creative base                    | `z_image_1.0_q8p.ckpt`          | `draw-things-cli models ensure --model z_image_1.0_q8p.ckpt`          | Controllable base for broad creativity.   |
| High-end FLUX/reference/edit     | `flux_2_dev_q6p.ckpt`           | `draw-things-cli models ensure --model flux_2_dev_q6p.ckpt`           | q6p chosen for 32 GiB rig.                |
| Instruction edit                 | `qwen_image_edit_2511_q8p.ckpt` | `draw-things-cli models ensure --model qwen_image_edit_2511_q8p.ckpt` | Current edit model.                       |
| Art/prompt-following alternative | `hidream_i1_full_q5p.ckpt`      | `draw-things-cli models ensure --model hidream_i1_full_q5p.ckpt`      | Full quality variant, q5p for memory fit. |

### Optional Image Targets

| Role                | Model id                               | Status on this rig                                     | Notes                             |
| ------------------- | -------------------------------------- | ------------------------------------------------------ | --------------------------------- |
| Layered editability | `qwen_image_layered_1.0_bf16_q8p.ckpt` | Optional; repeated CLI download stalls                 | Direct official Layered artifact. |
| Layered fallback    | `qwen_image_layered_1.0_bf16_q6p.ckpt` | Optional; verification failed with known-good mismatch | Lower-precision catalog entry.    |

### Media Pack

| Role              | Model id                         | Download command                                                       | Notes                                     |
| ----------------- | -------------------------------- | ---------------------------------------------------------------------- | ----------------------------------------- |
| Fast local media  | `ltx_2.3_22b_distilled_q6p.ckpt` | `draw-things-cli models ensure --model ltx_2.3_22b_distilled_q6p.ckpt` | Use first for text/video and image/video. |
| Rig-fit Wan video | `wan_v2.2_5b_ti2v_q8p.ckpt`      | `draw-things-cli models ensure --model wan_v2.2_5b_ti2v_q8p.ckpt`      | Current 5B Wan path for this rig.         |

---

## Download All Missing Recommended Models

Show commands first, then run only missing ones:

```bash
draw-things-cli models ensure --model hidream_i1_full_q5p.ckpt
draw-things-cli models ensure --model ltx_2.3_22b_distilled_q6p.ckpt
draw-things-cli models ensure --model wan_v2.2_5b_ti2v_q8p.ckpt
```

Use the helper for status:

```bash
uv run python skills/draw-thing/scripts/model_inventory.py --recommended-pack all --format json
```

---

## Quantization Policy For This Rig

| Model scale         | Preferred suffix | Rationale                                                         |
| ------------------- | ---------------- | ----------------------------------------------------------------- |
| 6B models           | `q8p`            | Fits 32 GiB well and preserves quality.                           |
| Qwen layered BF16   | optional         | Current but excluded from guaranteed pack until install succeeds. |
| FLUX.2 dev 32B      | `q6p`            | Avoid q8/full on this rig unless explicitly testing.              |
| HiDream I1 Full 17B | `q5p`            | Best quality role while limiting memory pressure.                 |
| LTX 2.3 22B         | `q6p`            | Distilled q6p is safer than dev/full q8.                          |
| Wan 2.2 5B          | `q8p`            | 5B model is rig-fit; q8p is acceptable.                           |
| Wan 2.2 A14B        | excluded         | Model-card guidance indicates much larger GPU memory needs.       |

Prefer official Draw Things optimized ids from `models list`. Do not select exact f16 variants unless the user explicitly accepts memory and runtime risk.

---

## Legacy And Redundant Downloads

These may exist locally but are not current best-pack defaults:

| Model id                   | Status                         | Replacement                                                                 |
| -------------------------- | ------------------------------ | --------------------------------------------------------------------------- |
| `flux_1_schnell_q8p.ckpt`  | Legacy/redundant               | `z_image_turbo_1.0_q8p.ckpt`                                                |
| `flux_1_fill_dev_q8p.ckpt` | Legacy workflow                | `qwen_image_edit_2511_q8p.ckpt`; Qwen Layered optional if installed cleanly |
| `flux_2_klein_4b_q6p.ckpt` | Current but redundant fallback | `flux_2_dev_q6p.ckpt` on 32 GiB rig                                         |
| SDXL / SD 1.5 / SD 2.x     | Legacy compatibility           | Qwen/Z/HiDream current pack                                                 |
| Qwen Image 1.0 / Edit 2509 | Superseded                     | Qwen 2512 / Edit 2511                                                       |
| Wan 2.1 / SVD              | Legacy video                   | LTX 2.3 / Wan 2.2 5B                                                        |

Never delete these automatically. If the user asks to reclaim disk space, present a prune plan and wait for explicit approval.

---

## Auxiliary And Partial Files

The Draw Things model directory can contain dependency files that are not direct generation choices. Examples include text encoders, VLM helpers, tensor-data sidecars, upscalers, and incomplete `*.part` files.

Current policy:

| Local file pattern                          | Interpretation                                                | Action                                                              |
| ------------------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------- |
| `llama_3.1_8b_instruct_q8p.ckpt.part`       | Incomplete stale auxiliary artifact, not a current best model | Do not resume or recommend; prune only after explicit user approval |
| `qwen_3_*`, `qwen_2.5_vl_*`, `mistral_*`    | Helper/dependency or manually imported text/VLM files         | Leave alone; do not select as default `generate --model` targets    |
| `*-tensordata`                              | Sidecar data for optimized Draw Things checkpoints            | Leave with its owning model/helper file                             |
| `qwen_image_layered_1.0_bf16_q6p.ckpt.part` | Interrupted optional Qwen Layered download                    | Retry only if the user accepts prior checksum failure risk          |
| `qwen_image_layered_1.0_bf16_q8p.ckpt.part` | Interrupted optional Qwen Layered download                    | Retry only if the user accepts prior repeated stall risk            |

The inventory helper reports these separately as `incomplete_downloads` and `auxiliary_or_dependency_files` so they cannot be mistaken for current recommended models.

---

## Family Notes

### Z Image

Use `z_image_turbo_1.0_q8p.ckpt` for fast drafts and `z_image_1.0_q8p.ckpt` for a more controllable creative base. Turbo expects low steps and `--cfg 0`.

### Qwen Image

Use `qwen_image_2512_q8p.ckpt` for text, layout, human realism, and polished editorial work. Use explicit quoted text in the prompt.

Use `qwen_image_edit_2511_q8p.ckpt` for img2img instruction edits and identity-preserving changes.

Use Qwen Layered only when editability and layer decomposition matter enough to justify retrying a currently unreliable install path.

### FLUX.2

Use `flux_2_dev_q6p.ckpt` for high-end FLUX.2 workflows on this rig. Treat `flux_2_klein_*` as fallback, not the default, because the rig already supports the dev q6p path.

Check license constraints before commercial use.

### HiDream

Use `hidream_i1_full_q5p.ckpt` for high-quality art and prompt-following alternatives. If smoke tests are too slow or memory-heavy, try `hidream_i1_dev_q5p.ckpt` or `hidream_i1_fast_q5p.ckpt` only after reporting the tradeoff.

### LTX And Wan

Use `ltx_2.3_22b_distilled_q6p.ckpt` for first media attempts. Keep frames divisible by 8 plus 1 and dimensions divisible by 32.

Use `wan_v2.2_5b_ti2v_q8p.ckpt` for current Wan workflows that fit this rig. Exclude A14B models by default.

---

## Model Directory

Default Draw Things model directory:

```text
~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models
```

Override:

```bash
export DRAWTHINGS_MODELS_DIR="/path/to/your/models"
```

Preferred inventory commands:

```bash
draw-things-cli models list --downloaded-only
uv run python skills/draw-thing/scripts/model_inventory.py --format json
```
