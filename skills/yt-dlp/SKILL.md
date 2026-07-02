---
name: yt-dlp
description: >-
  Probe, transcript, and download video/audio with yt-dlp CLI on supported
  hosts. Use when you need metadata, captions, or local media. Transcript-first
  (probe, transcript, download). NOT for static HTML (Fetch MCP), research, or
  ffmpeg transforms.
argument-hint: "<probe|transcript|download|playlist|cookies|doctor|help> [url or path]"
user-invocable: true
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
allowed-tools: Bash Read Glob Write
---

# yt-dlp

CLI skill for [yt-dlp](https://github.com/yt-dlp/yt-dlp): read-only URL probes, caption/transcript extraction, and optional media download. Follow the **transcript-first protocol** before any download.

**Scope:** Supported video/audio hosts via `yt-dlp`, user-owned cookie files, playlist metadata, and local output under an explicit directory. **NOT for:** static page fetch (use Fetch MCP or `curl`), broad multi-source research (`research`), ffmpeg transform recipes (`ffmpeg`), or bypassing platform Terms of Service.

---

## Canonical Vocabulary

| Term | Meaning | NOT |
| --- | --- | --- |
| **probe** | Read-only metadata via `--dump-json`; no media write | download |
| **transcript** | Captions/subtitles to text files; prefer over full download | audio rip by default |
| **download** | Persist media bytes after probe + user approval | silent bulk grab |
| **playlist** | Multi-entry URL; enumerate before selective download | blind full-playlist download |
| **cookies** | User-owned Netscape cookie file passed with `--cookies` | committed or skill-bundled secrets |
| **doctor** | Preflight JSON report for binary, version, ffmpeg | live URL smoke |
| **format id** | yt-dlp `format_id` from probe (e.g. `251`, `137+140`) | guessed extension |
| **manual sub** | Creator-uploaded captions | auto-generated only |
| **auto sub** | Platform-generated captions | guaranteed accuracy |

---

## Dispatch

| `$ARGUMENTS` | Mode | Action |
| --- | --- | --- |
| `probe <url>` / `metadata <url>` / `info <url>` | **Probe** | Run bundled `probe_url.py`; summarize title, id, duration, subs |
| `transcript <url>` / `subs <url>` / `captions <url>` | **Transcript** | Probe first; extract best available subtitles without video download |
| `download <url>` / `fetch <url>` / `save <url>` | **Download** | Probe first; confirm rights + format; download to explicit output dir |
| `playlist <url>` | **Playlist** | Probe with playlist allowed; list entries; selective download only with approval |
| `cookies <path>` / `cookies check <path>` | **Cookies** | Validate user-owned cookie file path; never copy into repo |
| `doctor` / `preflight` | **Doctor** | Run `scripts/doctor.py --format json` |
| Natural language: "what is this video", "get subtitles", "download this" | Auto | Map to probe → transcript → download per protocol below |
| _(empty)_ | **Help** | Show modes, protocol, ethics pointer, and examples |

### Auto-Detection Heuristic

1. URL + words like subtitle, caption, transcript, CC → **Transcript** (still probe first).
2. URL + download, save, mp4, audio, rip → **Download** (still probe + approval first).
3. URL + playlist, channel list, all videos → **Playlist**.
4. Bare URL or "what is this link" → **Probe**.
5. Path ending in `cookies.txt` or mention of login/auth → **Cookies** guidance, then re-probe with `--cookies`.
6. Ambiguous → ask: metadata only, transcript, or download?

---

## Transcript-First Protocol

Run these stages in order. **Do not skip probe.** **Do not download** until transcript needs are ruled out or the user explicitly wants media files.

### Stage 1 — Doctor (once per session or after errors)

```bash
uv run python scripts/doctor.py --format json
```

Stop on `ok: false` or any check with `status: fail` (missing `yt-dlp` binary).

### Stage 2 — Probe (mandatory before transcript or download)

```bash
uv run python scripts/probe_url.py --url 'https://…' --format json
```

With user-owned cookies:

```bash
uv run python scripts/probe_url.py --url 'https://…' --cookies "$HOME/.config/yt-dlp/cookies.txt" --format json
```

Playlist URL (enumerate entries; pass `--allow-playlist` on probe):

```bash
uv run python scripts/probe_url.py --url 'https://www.youtube.com/playlist?list=PL…' --allow-playlist --format json
```

From probe JSON, report: `id`, `title`, `duration`, `uploader`, `availability`, `subtitles` / `automatic_captions` languages, and recommended `format_id` candidates. Load [references/formats-and-quality.md](references/formats-and-quality.md) when choosing formats.

### Stage 3 — Transcript (preferred over download)

When subtitles exist, extract text without downloading video:

```bash
yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs 'en.*,en' \
  --convert-subs srt --sub-format srt \
  -o '%(title).200B.%(ext)s' \
  --paths home:"$HOME/Downloads/yt-dlp/transcripts" \
  'URL'
```

Prefer **manual** subs over **auto** when both exist. Summarize path to `.srt` / `.vtt` and offer to strip timing lines for plain text. If no subs: say so and ask before download-for-transcription (higher cost, rights-sensitive).

### Stage 4 — Download (explicit approval required)

Before running:

1. Confirm the user has rights to save the content (personal/archive/fair-use context per [references/ethics-and-tos.md](references/ethics-and-tos.md)).
2. Confirm output directory (default: `$HOME/Downloads/yt-dlp/media/`).
3. Confirm format from probe (`-f FORMAT` or sensible default: `bv*+ba/b`).

```bash
mkdir -p "$HOME/Downloads/yt-dlp/media"
yt-dlp -f 'bv*+ba/b' \
  --paths home:"$HOME/Downloads/yt-dlp/media" \
  -o '%(playlist_index)s-%(title).200B.%(ext)s' \
  'URL'
```

Report output path, format id, file size, and whether ffmpeg merge ran.

---

## Mode Details

### Probe mode

- Use bundled `probe_url.py` (wraps `yt-dlp --dump-json --no-download`).
- Read-only: no writes under cwd or repo.
- For age-gated or login-only content, stop and route to **Cookies** — do not guess credentials.

### Transcript

- Never default to downloading video/audio for text needs.
- Use `--skip-download` always.
- If multiple languages, pick user-requested lang or `en` with fallback list from probe.

### Download

- Single URL default: `--no-playlist` unless user asked for playlist.
- No bulk channel/archival without explicit scope confirmation.
- Do not embed cookies in commands in chat logs; reference `$COOKIES` env or user path only.

### Playlist

1. Probe with playlist enabled:

```bash
uv run python scripts/probe_url.py --url 'PLAYLIST_URL' --allow-playlist --format json
```

2. Present numbered entries (index, title, duration).
3. Download **selected indices only** (`--playlist-items 1,3,5`) after approval — never blind full playlist.

### Cookies

- **User-owned cookie file only** — path under user home or explicit user-provided path.
- Never commit cookie files, never store in repo, never bundle in skill package.
- Export guidance (browser extension → Netscape `cookies.txt`) lives in [references/ethics-and-tos.md](references/ethics-and-tos.md).
- Validate readability:

```bash
test -r "$HOME/.config/yt-dlp/cookies.txt" && echo readable
```

Pass `--cookies PATH` only on probe/download when user supplied the path.

### Doctor

```bash
uv run python scripts/doctor.py --format json
```

Parses JSON `ok`, `summary`, and per-check `status`. Stop workflow on `fail`. Treat `warn` (e.g. missing ffmpeg) as advisory.

### Help

Show dispatch table, transcript-first protocol, default paths, and ethics reference link.

### Gallery (Empty Arguments)

Present common invocations when `$ARGUMENTS` is empty:

| # | Task | Example |
| --- | --- | --- |
| 1 | Preflight | `/yt-dlp doctor` |
| 2 | Probe metadata | `/yt-dlp probe https://www.youtube.com/watch?v=…` |
| 3 | Get subtitles | `/yt-dlp transcript https://www.youtube.com/watch?v=…` |
| 4 | Download (after approval) | `/yt-dlp download https://www.youtube.com/watch?v=…` |
| 5 | Playlist enumerate | `/yt-dlp playlist https://www.youtube.com/playlist?list=…` |
| 6 | User-owned cookies | `/yt-dlp cookies ~/.config/yt-dlp/cookies.txt` |

> Pick a number, a mode from the dispatch table, or paste a URL and say whether you need metadata, subtitles, or a download.

---

## Critical Rules

1. **Probe before transcript or download** — always use `probe_url.py` or equivalent `--dump-json --no-download`.
2. **Transcript before download** — prefer `--skip-download` subtitle extraction when captions exist.
3. **Explicit approval for downloads** — confirm rights, scope, output dir, and format.
4. **User-owned cookies only** — never commit, copy into repo, or invent cookie paths.
5. **No ToS bypass coaching** — see [references/ethics-and-tos.md](references/ethics-and-tos.md); refuse DRM circumvention or paywall evasion requests.
6. **Not Fetch MCP** — static HTML, docs pages, and non-yt-dlp hosts → Fetch MCP or `curl`, not this skill.
7. **Not ffmpeg skill** — remux, transcode, clip, waveform → `/ffmpeg` after download if needed.
8. **Least privilege output** — write only under user-approved directories, never into the agents repo tree.
9. **Report provenance** — title, URL, extractor, format id, and output paths in the final summary.

---

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for extractor errors, geo blocks, signature failures, and ffmpeg merge issues.

---

## References

| File | Use when |
| --- | --- |
| [ethics-and-tos.md](references/ethics-and-tos.md) | Rights, cookies, refusal boundaries |
| [formats-and-quality.md](references/formats-and-quality.md) | Choosing `-f` format strings |
| [troubleshooting.md](references/troubleshooting.md) | Errors after doctor passes |

---

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/doctor.py` | JSON preflight: yt-dlp, version, ffmpeg |
| `scripts/probe_url.py` | Read-only `--dump-json` wrapper |
| `scripts/check.py` | Validate skill manifest and evals |

---

## Examples

```bash
# Preflight
uv run python scripts/doctor.py --format json

# Probe
uv run python scripts/probe_url.py --url 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' --format json

# Transcript (after probe shows subs)
yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs en -o '%(id)s' \
  --paths home:"$HOME/Downloads/yt-dlp/transcripts" 'URL'

# Download (after user approval)
yt-dlp -f 'bv*+ba/b' --paths home:"$HOME/Downloads/yt-dlp/media" -o '%(title).200B.%(ext)s' 'URL'
```