# Grok headless JSON output

Fixture captured from `grok --no-auto-update -p "..." --output-format json --max-turns 3`.

## Single-turn shape

```json
{
  "text": "assistant response text",
  "stopReason": "EndTurn",
  "sessionId": "019ef3d7-75a0-7743-8172-afb2f9433c7a",
  "requestId": "20e07897-55a5-48f9-a157-a31bdbb18ea6",
  "thought": "optional reasoning summary"
}
```

## Fields for parent orchestration

| Field | Use |
| --- | --- |
| `text` | Primary deliverable; parse for success markers |
| `stopReason` | `EndTurn` = normal stop; tune if incomplete scope |
| `sessionId` | Ledger key; pass to `-r` for tune waves |
| `requestId` | Correlation / debug only |
| `thought` | Optional; do not treat as user-facing output |

## Tune/resume

`-r <sessionId> -p "Tune: ..."` returns the same top-level shape; `sessionId` stays stable across tunes in fixtures.

## Streaming

`--output-format streaming-json` emits newline-delimited events. Prefer `json` for parent bash dispatch unless streaming consumer exists.

## Parser helper

`skills/grok-delegate/scripts/parse_grok_json.py` reads stdin JSON and prints `sessionId`, `stopReason`, and `text` on separate lines for shell pipelines.

## Distinct surface: bundled doctor JSON

Preflight uses a different JSON shape (`ok`, `summary`, `checks[]`). Do not confuse with headless `-p` output. See [doctor-output.md](doctor-output.md).