# Research lock: ffmpeg skill

- **Primary:** `skills/ffmpeg/` + system `ffmpeg`/`ffprobe`
- **Recipes:** trim, transcode, concat, extract-audio, thumbnail, gif
- **Protocol:** probe → recipe → new output path (no in-place overwrite)
- **Complements:** draw-thing (generative), remotion (programmatic video)
- **MCP:** disabled; do not enable ffmpeg-mcp by default
- **Remediation (2026-07-02):** gallery evals added; probe_media int coercion for stream fields