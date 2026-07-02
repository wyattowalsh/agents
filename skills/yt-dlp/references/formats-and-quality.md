# Formats and Quality

## Reading probe output

`probe_url.py` returns full `info` plus a `summary` with `format_id`, `ext`, and subtitle languages. Use these fields before choosing `-f`.

## Common format selectors

| Goal | Suggested `-f` | Notes |
| --- | --- | --- |
| Best video + audio (default) | `bv*+ba/b` | May require ffmpeg merge |
| Best audio only | `ba/b` | Smaller; good for podcasts |
| Limit resolution | `bv*[height<=1080]+ba/b` | Saves bandwidth |
| Specific format id from probe | `137+140` | Use ids from `formats` list in probe JSON |
| Worst case fallback | `b` | Single best combined format if merge unavailable |

## Subtitle extraction

| Flag | Purpose |
| --- | --- |
| `--skip-download` | No media bytes |
| `--write-subs` | Manual captions |
| `--write-auto-subs` | Auto-generated captions |
| `--sub-langs 'en.*,en'` | Language preference |
| `--convert-subs srt` | Normalize to SRT |

Prefer manual subtitles when probe `subtitles.manual` is non-empty.

## Playlist behavior

- Single video URL: use `--no-playlist` (default in `probe_url.py`).
- Playlist URL: pass `--allow-playlist` to probe; download with `--playlist-items N,M` after user picks entries.

## Output templates

Keep titles filesystem-safe:

```text
-o '%(playlist_index)s-%(title).200B.%(ext)s'
```

Use `--paths home:DIR` to confine writes:

```bash
--paths home:"$HOME/Downloads/yt-dlp/media"
```

## ffmpeg dependency

When `-f` selects separate video and audio streams, yt-dlp invokes ffmpeg to mux. Doctor warns when ffmpeg is missing; downloads may fail or fall back to single-stream formats.