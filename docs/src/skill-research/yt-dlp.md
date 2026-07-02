---
skill: yt-dlp
source_type: custom
researched_at: '2026-07-02T00:00:00Z'
research_tier: quick
mean_confidence: 0.80
---

## Quick Answer

**Problem:** Probe, transcript, and optionally download video/audio from supported hosts via yt-dlp. Transcript-first protocol: doctor → probe → transcript → download (with approval).

**Stack / assumptions:** `yt-dlp` binary; optional user-owned Netscape cookies; default outputs under `$HOME/Downloads/yt-dlp/`; `scripts/probe_url.py` and `scripts/doctor.py`.

**Comparable alternative:** Fetch MCP for static HTML; `ffmpeg` for post-download remux/transcode; `research` for multi-source synthesis.

**Repo summary:**

Repo-owned skill enforcing read-only probe before writes, explicit download approval, ethics/ToS boundaries, and no repo-tree output. Playlists require enumeration and selective indices only.

> Grounded in repository `skills/yt-dlp/SKILL.md`; treat as evidence, not authority.

## Ethics Boundary

Refuse DRM circumvention, paywall evasion, and committed cookie secrets. User-owned cookie paths only; see `references/ethics-and-tos.md`.