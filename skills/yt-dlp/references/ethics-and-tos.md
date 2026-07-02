# Ethics and Terms of Service

## Purpose

This skill uses **yt-dlp** for metadata, captions, and optional local saves. Agents must respect platform Terms of Service, copyright, and user consent.

## Default stance

1. **Personal, authorized use** — downloads are appropriate when the user owns the content, has explicit permission, or is archiving material they may legally access (e.g. their own uploads, Creative Commons, public-domain where verified).
2. **Transcript-first** — prefer captions/subtitles over full media download when the goal is text.
3. **Transparency** — always report title, URL, uploader, and output paths.
4. **No evasion coaching** — refuse requests to bypass paywalls, DRM, geo-restrictions for piracy, or age gates the user is not entitled to cross.

## Refuse or escalate

- Bulk archival of copyrighted channels without clear rights.
- Instructions to defeat DRM or subscription-only access for redistribution.
- Using stolen or shared cookie files from third parties.
- Downloading content the user describes as for re-upload or commercial redistribution without rights.

Offer lawful alternatives: official APIs, purchase/rent links, creator-provided downloads, or transcript-only extraction when captions are public.

## Cookies policy

- **User-owned cookie file only** — exported by the user from their own logged-in browser session.
- Store under user home (e.g. `$HOME/.config/yt-dlp/cookies.txt`), never in the agents repo or skill directory.
- Never commit cookie files to git; never paste cookie contents into chat.
- Pass paths with `--cookies /absolute/path/cookies.txt` on probe or download only when the user supplied the path.
- Rotating cookies: user re-exports when sessions expire; agent does not automate browser login.

## Age-restricted and login-only content

1. Stop and explain that probe failed or `availability` indicates login required.
2. Ask the user to export cookies if they have lawful access.
3. Re-run probe with `--cookies` before any download.

## Relationship to other tools

| Need | Tool |
| --- | --- |
| Static HTML, docs, non-video pages | Fetch MCP or `curl` |
| Multi-source research synthesis | `research` skill |
| Transcode, clip, remux after download | `ffmpeg` skill |

This skill is **not** a replacement for Fetch MCP on arbitrary URLs.

## Agent checklist before download

1. Did probe succeed without login errors?
2. Does the user have lawful access to the content?
3. Is transcript-only sufficient for the stated goal?
4. Is the output directory explicit and outside the repo?
5. Are cookies user-owned and passed by path only (never pasted)?

If any answer is unclear, ask before running `yt-dlp` with media writes.

## Redistribution and attribution

When the user plans to quote or cite transcript text, prefer excerpt + link to the source URL. Do not imply official endorsement. For Creative Commons or licensed material, surface license fields from probe metadata when present (`license`, `creator`, `tags`) and remind the user to comply with attribution requirements.

## Platform-specific reminders

- **YouTube:** Terms restrict downloading except where YouTube provides a download button or separate licensed product. This skill is for user-directed CLI workflows the user accepts responsibility for.
- **Live streams:** Do not assume replay availability; probe `live_status` before promising output.
- **Private/unlisted:** Access does not imply download rights; confirm with the user.

## Cookie export (user action)

Typical flow the user performs (agent documents, does not automate login):

1. Sign in with their account in a supported browser.
2. Export Netscape-format `cookies.txt` via a trusted extension or tool they choose.
3. Save to `~/.config/yt-dlp/cookies.txt` (or another home-directory path).
4. Tell the agent the absolute path for `--cookies` on probe/download.

Never ask the user to paste cookie contents into chat.