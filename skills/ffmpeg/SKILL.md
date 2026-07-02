---
name: ffmpeg
description: >-
  Probe, trim, transcode, concat, and extract local A/V with ffmpeg/ffprobe.
  Use when converting or inspecting media files. NOT for AI image generation
  (draw-thing) or UI design (design).
argument-hint: "<doctor|probe|trim|transcode|concat|extract-audio|thumbnail|gif> [paths]"
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
user-invocable: true
allowed-tools: Bash Read Glob
---

# FFmpeg

CLI skill for **local** audio/video inspection and transformation via `ffmpeg` and `ffprobe`. Invoke as `/ffmpeg`.

**Scope:** Probe metadata, trim clips, transcode containers/codecs, concatenate segments, extract audio, capture thumbnails, and build GIF previews from files on disk. NOT for AI image or video generation (`draw-thing`), UI or layout design (`design`), networked downloads (`yt-dlp`), or broadcast/streaming pipelines.

---

## Canonical Vocabulary

| Term | Meaning | NOT |
| --- | --- | --- |
| **probe** | Read-only ffprobe inspection | transcode |
| **trim** | Shorten by time range | crop UI mockup |
| **transcode** | Re-mux or re-encode to new container/codec | generate new imagery |
| **concat** | Join multiple inputs sequentially | merge git branches |
| **extract-audio** | Strip video, keep audio track | speech-to-text |
| **thumbnail** | Single still frame from video | design a poster layout |
| **gif** | Animated GIF preview from video clip | CSS animation |
| **stream copy** | `-c copy` without re-encode | always safe for all trims |
| **recipe** | Approved command template from `references/` | ad-hoc filter graph |

---

## Dispatch

| `$ARGUMENTS` | Mode | Action |
| --- | --- | --- |
| `doctor` / `check` / `preflight` | **Doctor** | Run PATH doctor; stop if ffmpeg/ffprobe missing |
| `probe <path>` / `info <path>` / `metadata <path>` | **Probe** | Run probe helper; summarize streams and duration |
| `trim <path> <start> <end>` / `clip <path> ...` | **Trim** | Probe, pick copy vs re-encode recipe, new output path |
| `transcode <path>` / `convert <path> to mp4` | **Transcode** | Probe codecs; apply H.264/AAC or copy recipe |
| `concat <file1> <file2> [...]` / `join ...` | **Concat** | Verify probes; concat demuxer recipe + new output |
| `extract-audio <path>` / `audio <path>` | **Extract audio** | Probe audio stream; MP3/M4A/copy recipe |
| `thumbnail <path>` / `thumb <path> [timestamp]` | **Thumbnail** | Seek frame; write JPG/PNG to new path |
| `gif <path>` / `animate <path> [start] [duration]` | **GIF** | Palette GIF recipe with duration cap |
| Path to media + natural language edit intent | **Auto** | Classify trim/transcode/thumbnail/gif from intent |
| _(empty)_ | **Help** | Show modes, critical rules, script commands, references |

### Auto-Detection Heuristic

1. Install/tooling doubt → **Doctor**.
2. "metadata", "codec", "duration", "how long", "what format" → **Probe**.
3. "cut", "clip", "from ... to ...", time range → **Trim**.
4. "mp4", "webm", "h264", "aac", "smaller", "compress" → **Transcode**.
5. "join", "merge clips", "append videos" → **Concat**.
6. "mp3", "wav", "m4a", "strip video", "audio only" → **Extract audio**.
7. "poster frame", "screenshot", "still", "thumbnail" → **Thumbnail**.
8. "gif", "animated preview" → **GIF**.
9. Generative image/video language → refuse; redirect to `draw-thing`.
10. UI/page/layout design → refuse; redirect to `design`.
11. Ambiguous → ask which mode and state copy vs re-encode tradeoff.

---

## Critical Rules

1. **Probe before mutate** — run `probe_media.py` on every source file before trim, transcode, concat, extract-audio, thumbnail, or gif. Use probe fields to choose maps, codecs, and duration bounds. See `references/probe-fields.md`.
2. **Never overwrite in-place (default)** — always write to a new output path. In-place replace requires explicit user approval plus backup/temp-file replace. See `references/safety.md`.
3. **Recipe-only mutations** — build ffmpeg commands only from `references/recipes-trim-transcode.md` and `references/recipes-thumbnail-gif.md`. No improvised filter chains or destructive batch jobs without approval.

---

## Prerequisite Protocol

Run before any mutation:

```bash
uv run python scripts/doctor.py --format json
```

Stop when JSON `ok` is false. Install guidance:

```bash
brew install ffmpeg
```

For each input file:

```bash
uv run python scripts/probe_media.py /absolute/path/to/input.mp4
```

Parse `summary.duration_seconds`, `summary.stream_counts`, and codec fields before selecting a recipe.

---

## Mode Protocols

### Doctor

1. Run `uv run python scripts/doctor.py --format json`.
2. Report `checks` statuses and remediation for any `fail`.
3. Do not run ffmpeg mutations when `ffmpeg-binary` or `ffprobe-binary` fails.

### Probe

1. Require a readable local file path.
2. Run `uv run python scripts/probe_media.py <path>`.
3. Summarize: container, duration, video/audio codecs, resolution, stream counts.
4. Load `references/probe-fields.md` when interpreting rotation, multi-track audio, or subtitle streams.

### Trim

1. Probe source; validate `start`/`end` against `duration_seconds`.
2. Prefer stream copy when keyframe alignment is acceptable; otherwise use re-encode trim recipe.
3. Output to `basename.trim.ext` or user-provided **new** path.
4. Load `references/recipes-trim-transcode.md`.

### Transcode

1. Probe source; decide copy vs H.264/AAC re-encode.
2. Map explicit streams when multiple tracks exist.
3. Include `-movflags +faststart` for MP4 web delivery unless user forbids.
4. Load `references/recipes-trim-transcode.md`.

### Concat

1. Probe every segment; confirm compatible codecs/resolution for copy concat.
2. Build concat list file with absolute paths; never concat unrelated codecs with copy without warning.
3. Output to a new `*.concat.mp4` path.
4. Load `references/recipes-trim-transcode.md`.

### Extract audio

1. Probe source; fail gracefully when `stream_counts.audio` is zero.
2. Choose MP3, M4A, or copy recipe based on target format.
3. Write `basename.audio.ext` as a new file.
4. Load `references/recipes-trim-transcode.md`.

### Thumbnail

1. Probe source; require at least one video stream.
2. Pick timestamp (user value, or 10% duration clamped 1–10s).
3. Write JPG/PNG under `OUTPUT/` or sibling path — never overwrite source.
4. Load `references/recipes-thumbnail-gif.md`.

### GIF

1. Probe source; cap duration (default max 5s unless user expands).
2. Use two-pass palette recipe for quality; single-pass only for quick previews.
3. Write `clip.gif` and optional `palette.png` as new files.
4. Load `references/recipes-thumbnail-gif.md`.

### Help _(empty)_

Show dispatch table, critical rules, doctor/probe commands, reference index, and the gallery below.

### Gallery (Empty Arguments)

Present common local media tasks when `$ARGUMENTS` is empty:

| # | Task | Example |
| --- | --- | --- |
| 1 | Preflight tooling | `/ffmpeg doctor` |
| 2 | Inspect metadata | `/ffmpeg probe ~/Movies/clip.mp4` |
| 3 | Trim a clip | `/ffmpeg trim ~/Movies/clip.mp4 00:00:05 00:00:15` |
| 4 | Transcode container | `/ffmpeg transcode ~/Movies/clip.mov` |
| 5 | Join segments | `/ffmpeg concat part1.mp4 part2.mp4` |
| 6 | Extract audio | `/ffmpeg extract-audio ~/Movies/clip.mp4` |
| 7 | Poster frame | `/ffmpeg thumbnail ~/Movies/clip.mp4 00:00:03` |
| 8 | GIF preview | `/ffmpeg gif ~/Movies/clip.mp4 00:00:02 4` |

> Pick a number, a mode from the dispatch table, or paste a file path and describe the edit.

---

## Skill Awareness

| Signal | Redirect |
| --- | --- |
| "generate an image", "txt2img", "AI video", local Draw Things | `draw-thing` |
| "design a landing page", "Figma", "React layout" | `design` |
| "download from YouTube/URL" | `yt-dlp` |
| Live streaming, RTMP, OBS wiring | out of scope — suggest streaming docs |

---

## Reference Files

| File | Load when |
| --- | --- |
| `references/safety.md` | Any mutation; in-place overwrite questions |
| `references/probe-fields.md` | Interpreting probe JSON |
| `references/recipes-trim-transcode.md` | trim, transcode, concat, extract-audio |
| `references/recipes-thumbnail-gif.md` | thumbnail, gif |

---

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/doctor.py` | Verify ffmpeg/ffprobe on PATH (`--format json`) |
| `scripts/probe_media.py` | ffprobe wrapper with summary (`--raw` for full payload) |
| `scripts/check.py` | Validate SKILL.md, evals, package dry-run, audit |

Validation:

```bash
uv run python scripts/check.py
```

---

## Reporting Template

After any mutation, report:

1. Doctor status (if run this session)
2. Probe summary (duration, codecs, streams)
3. Recipe name (copy vs re-encode)
4. Exact ffmpeg command(s) executed
5. Output path(s) and size change
6. Caveats (keyframe trim, missing audio, GIF duration cap)