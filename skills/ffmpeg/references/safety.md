# Safety and mutation policy

Read-only inspection is always allowed. Any file write follows these rules.

## Probe before mutate

1. Run doctor when tooling is uncertain:
   ```bash
   uv run python scripts/doctor.py --format json
   ```
2. Probe the source file before trim, transcode, concat, extract-audio, thumbnail, or gif:
   ```bash
   uv run python scripts/probe_media.py /absolute/path/to/input.mp4
   ```
3. Use probe output to choose codecs, stream maps, duration bounds, and whether re-encode is required.
4. Never guess duration, rotation, or audio presence when probe can answer.

## Never overwrite in-place (default)

- **Default:** write to a new path (`input.trimmed.mp4`, `input.h264.mp4`, `frames/thumb.jpg`).
- **Forbidden by default:** `-i input.mp4 -c copy output.mp4` when `output.mp4` is the same path as `input.mp4`.
- If the user explicitly requests in-place replacement, require:
  1. Confirmed backup or version control snapshot
  2. Explicit approval in the prompt
  3. Atomic replace via temp file + `mv` (never direct overwrite of the only copy)

## Recipe-only mutations

- Build ffmpeg commands only from approved recipes in:
  - `references/recipes-trim-transcode.md`
  - `references/recipes-thumbnail-gif.md`
- Do not invent exotic filter graphs, hardware flags, or undocumented switches without user approval.
- Prefer stream copy (`-c copy`) when probe shows compatible codecs and the recipe allows it.
- Prefer re-encode only when container/codec change, frame-accurate trim, scaling, or GIF palette steps require it.

## Stream and path hygiene

- Quote paths with spaces; prefer absolute paths in examples.
- Map streams explicitly when multiple video/audio tracks exist (`-map 0:v:0`, `-map 0:a:0`).
- For concat, use the concat demuxer recipe with a verified file list; never concatenate unrelated codecs without re-encode guidance.
- Report the final output path, byte size change, and whether streams were copied or re-encoded.

## When to stop and ask

- Missing ffmpeg/ffprobe on PATH
- Probe shows zero video streams for thumbnail/gif modes
- User asks to strip DRM, bypass copyright protection, or process files they do not own
- Destructive batch over many files without explicit approval
- Request is generative AI imagery → redirect to `draw-thing`
- Request is UI/layout design → redirect to `design`