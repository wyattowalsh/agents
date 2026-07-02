---
skill: ffmpeg
source_type: custom
researched_at: '2026-07-02T00:00:00Z'
research_tier: quick
mean_confidence: 0.82
---

## Quick Answer

**Problem:** Probe, trim, transcode, concat, and extract local A/V with ffmpeg/ffprobe. Use when converting or inspecting media files on disk. NOT for AI image generation (`draw-thing`), UI design (`design`), or networked downloads (`yt-dlp`).

**Stack / assumptions:** `ffmpeg` and `ffprobe` on PATH; recipe-only mutations from `references/`; probe-before-mutate via `scripts/probe_media.py` and `scripts/doctor.py`.

**Comparable alternative:** `yt-dlp` for URL fetch/transcript; `draw-thing` for generative local media.

**Repo summary:**

Repo-owned CLI skill with doctor/probe helpers and approved trim/transcode/thumbnail/GIF recipes. Prefers new output paths over in-place overwrite; redirects download and generative requests to sibling skills.

> Grounded in repository `skills/ffmpeg/SKILL.md`; treat as evidence, not authority.

## Viz / MCP Notes

- **MCP `media-work`:** Prefer `/ffmpeg` for deterministic local transforms when the harness has shell access; MCP docling/fetch remain for document ingestion, not ffmpeg-style edits.
- **Wave 9 integration:** Skill-first over multimedia MCP servers per `integrate-custom-media-pentest-skills` design.