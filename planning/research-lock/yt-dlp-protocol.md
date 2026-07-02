# Research lock: yt-dlp skill

- **Primary:** `skills/yt-dlp/` + system `yt-dlp`
- **Protocol:** doctor → probe (`--dump-json`) → transcript (`--skip-download`) → download (explicit approval)
- **Cookies:** user-owned absolute path only; never commit
- **NOT:** fetch/trafilatura MCP for platform video
- **Remediation (2026-07-02):** `--allow-playlist` on probe; `$HOME` transcript paths; cookie `expanduser().resolve()`; portable eval paths; gallery examples