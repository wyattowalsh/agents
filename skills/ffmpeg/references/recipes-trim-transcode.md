# Trim, transcode, concat, extract-audio recipes

All recipes assume probe ran first and output paths are **new files**.

## Trim (stream copy, keyframe-aligned)

Fast cut when codecs match container and keyframe alignment is acceptable:

```bash
ffmpeg -y -ss START -to END -i "INPUT.mp4" -c copy "OUTPUT.trim.mp4"
```

- `START` / `END`: `HH:MM:SS.mmm` or seconds
- Expect cuts on nearest keyframe when using `-c copy`
- Probe `duration_seconds` before choosing `END`

## Trim (re-encode, frame-accurate)

When the user needs sample-accurate boundaries:

```bash
ffmpeg -y -ss START -to END -i "INPUT.mp4" \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 192k \
  "OUTPUT.trim.mp4"
```

## Transcode (H.264 + AAC MP4)

General web-friendly output:

```bash
ffmpeg -y -i "INPUT" \
  -map 0:v:0 -map 0:a:0? \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 192k \
  -movflags +faststart \
  "OUTPUT.mp4"
```

Adjust `-crf` (lower = higher quality, larger file). Omit audio map if probe shows no audio.

## Transcode (copy when compatible)

When probe shows source is already target-friendly:

```bash
ffmpeg -y -i "INPUT.mp4" -map 0 -c copy "OUTPUT.copy.mp4"
```

Only when container and codecs already match the delivery target.

## Scale + transcode (max width)

```bash
ffmpeg -y -i "INPUT" \
  -vf "scale='min(1280,iw)':-2" \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 192k \
  "OUTPUT.1280w.mp4"
```

## Extract audio (MP3)

```bash
ffmpeg -y -i "INPUT" -vn -map 0:a:0 \
  -c:a libmp3lame -q:a 2 \
  "OUTPUT.mp3"
```

## Extract audio (AAC m4a)

```bash
ffmpeg -y -i "INPUT" -vn -map 0:a:0 \
  -c:a aac -b:a 192k \
  "OUTPUT.m4a"
```

## Extract audio (copy)

When audio codec is already AAC inside MP4/M4A:

```bash
ffmpeg -y -i "INPUT" -vn -map 0:a:0 -c:a copy "OUTPUT.m4a"
```

## Concat (concat demuxer, same codecs)

1. Create `list.txt` (each line: `file '/absolute/path/to/part.mp4'`).
2. Run:

```bash
ffmpeg -y -f concat -safe 0 -i "list.txt" -c copy "OUTPUT.concat.mp4"
```

All segments should share codec, resolution, and timebase. If not, transcode segments first or use the re-encode concat recipe.

## Concat (re-encode fallback)

```bash
ffmpeg -y -f concat -safe 0 -i "list.txt" \
  -c:v libx264 -preset medium -crf 23 \
  -c:a aac -b:a 192k \
  "OUTPUT.concat.mp4"
```

## Post-run report

Always state:

- Input probe summary (duration, codecs)
- Recipe used (copy vs re-encode)
- Output path and whether `-y` overwrote a **new** destination only