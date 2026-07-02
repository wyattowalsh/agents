# ffprobe fields

Use `probe_media.py` for a normalized summary plus raw ffprobe JSON.

```bash
uv run python scripts/probe_media.py /absolute/path/to/file.mp4
uv run python scripts/probe_media.py /absolute/path/to/file.mp4 --raw
```

## Summary wrapper (`ok`, `file`, `summary`, `ffprobe`)

| Field | Use |
| --- | --- |
| `summary.duration_seconds` | Trim end times, clip length checks |
| `summary.format_name` | Container hint (`mov,mp4,m4a,...`, `matroska`, `webm`) |
| `summary.size_bytes` / `bit_rate` | Output size expectations |
| `summary.stream_counts` | Detect missing audio/video/subtitles |
| `summary.video.codec` | Whether copy or transcode is viable |
| `summary.video.width` / `height` | Thumbnail scale, aspect ratio |
| `summary.video.avg_frame_rate` | GIF timing and `-r` defaults |
| `summary.audio.codec` | Extract-audio and transcode mapping |

## Raw `format` object

| Field | Meaning |
| --- | --- |
| `format.filename` | Resolved input path |
| `format.duration` | Duration in seconds (string) |
| `format.bit_rate` | Overall bitrate |
| `format.tags` | Title, rotation metadata, creation time |

## Raw `streams[]` entries

Filter by `codec_type`:

| `codec_type` | Key fields |
| --- | --- |
| `video` | `codec_name`, `width`, `height`, `pix_fmt`, `avg_frame_rate`, `r_frame_rate`, `bit_rate`, `disposition.default` |
| `audio` | `codec_name`, `sample_rate`, `channels`, `channel_layout`, `bit_rate` |
| `subtitle` | `codec_name` (often `mov_text`, `subrip`, `ass`) |

## Dispatch hints from probe

| Observation | Route |
| --- | --- |
| Single H.264/AAC in MP4 | Copy-friendly trim/transcode |
| HEVC, VP9, ProRes, or PCM | Plan re-encode or explicit copy risk |
| Multiple audio streams | Ask which track or use `-map 0:a:N` |
| No audio stream | Skip extract-audio; warn on `-c copy` expectations |
| Very short duration (<1s) | Caution on GIF/thumbnail seek |
| Rotation tag present | May need transpose filter before thumbnail |

## Probe-before-mutate checklist

1. Confirm `duration_seconds` and stream counts.
2. Record primary video/audio codecs.
3. Choose recipe (copy vs re-encode).
4. Pick a **new** output path.
5. Run ffmpeg with quoted absolute paths.