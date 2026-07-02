# Thumbnail and GIF recipes

Requires a video stream in probe output. Always write new files under a dedicated output directory.

## Thumbnail (single frame at timestamp)

```bash
ffmpeg -y -ss 00:00:03.000 -i "INPUT.mp4" \
  -frames:v 1 -q:v 2 \
  "OUTPUT/thumb.jpg"
```

- Default seek: 10% of `duration_seconds`, clamped between `00:00:01` and `00:00:10`
- For black-frame risk at start, prefer 10% seek or user-provided timestamp

## Thumbnail (scale to max width)

```bash
ffmpeg -y -ss TIMESTAMP -i "INPUT.mp4" \
  -vf "scale='min(1280,iw)':-2" \
  -frames:v 1 -q:v 2 \
  "OUTPUT/thumb.jpg"
```

## Thumbnail strip (filmstrip)

```bash
ffmpeg -y -i "INPUT.mp4" \
  -vf "fps=1/10,scale=320:-1,tile=4x4" \
  -frames:v 1 \
  "OUTPUT/filmstrip.jpg"
```

Adjust `fps=1/10` for one frame every 10 seconds and `tile=4x4` for grid size.

## GIF (palette, standard quality)

Two-pass palette method for better color:

```bash
ffmpeg -y -ss START -t DURATION -i "INPUT.mp4" \
  -vf "fps=12,scale=480:-1:flags=lanczos,palettegen" \
  "OUTPUT/palette.png"

ffmpeg -y -ss START -t DURATION -i "INPUT.mp4" \
  -i "OUTPUT/palette.png" \
  -lavfi "fps=12,scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse" \
  "OUTPUT/clip.gif"
```

Defaults when user omits values:

- `DURATION`: min(5s, 20% of probe duration, remaining after `START`)
- `fps`: 12
- `scale`: 480 px width

## GIF (short preview, single pass)

Lower quality, faster:

```bash
ffmpeg -y -ss START -t DURATION -i "INPUT.mp4" \
  -vf "fps=10,scale=320:-1:flags=lanczos" \
  "OUTPUT/clip.gif"
```

## Safety notes

- GIF generation re-encodes; never target the source path
- Long clips produce huge GIFs — cap duration unless user expands limit
- For high-quality looping assets, suggest MP4/WebM instead of GIF when appropriate