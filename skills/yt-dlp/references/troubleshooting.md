# Troubleshooting

## Preflight

Always run doctor first:

```bash
uv run python scripts/doctor.py --format json
```

| Check | `fail` meaning | Fix |
| --- | --- | --- |
| `yt-dlp-binary` | Not on PATH | `pipx install yt-dlp` or `brew install yt-dlp` |
| `yt-dlp-version` | Binary broken | Reinstall / upgrade yt-dlp |
| `ffmpeg-binary` | Missing | `brew install ffmpeg` (warn only) |

## Probe failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `Video unavailable` | Removed, private, or geo-blocked | Confirm URL; check rights; try user cookies if login-required |
| `Sign in to confirm your age` | Age gate | User-owned cookies; do not bypass illegally |
| `Unsupported URL` | Host not supported by yt-dlp | Use Fetch MCP or direct site tools |
| `HTTP Error 403` | Blocked or expired cookies | Re-export cookies |
| Timeout | Slow network or live stream | Increase `--timeout` on probe; retry |

## Download failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ffmpeg not found` | Merge required | Install ffmpeg; or use `-f b` combined format |
| `Requested format not available` | Stale format id | Re-probe; use `bv*+ba/b` |
| Partial file `.part` | Interrupted download | Re-run yt-dlp; it resumes by default |
| Disk full | Output dir | Choose another `--paths home:` directory |

## Subtitle issues

| Symptom | Action |
| --- | --- |
| No manual subs, auto only | Use `--write-auto-subs`; note lower accuracy |
| Wrong language | Adjust `--sub-langs` from probe language list |
| Empty subtitle file | Probe again; video may have no captions |

## Update yt-dlp

Extractor breakages are common. Upgrade before blaming the URL:

```bash
yt-dlp -U
# or
pipx upgrade yt-dlp
```

## When to leave this skill

- Plain web page text → **Fetch MCP**
- Research report across sources → **research**
- Audio normalization, clipping, codec change → **ffmpeg** after download