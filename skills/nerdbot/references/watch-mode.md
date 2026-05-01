# Watch Mode

## Purpose

Watch mode observes local KB changes and queues safe follow-up work. It must not directly rewrite canonical material or risky wiki surfaces.

The package exposes `nerdbot.watch.classify_watch_event()`, `classify_watch_events()`, review-item conversion, and checkpoint rendering as non-mutating policy helpers. The CLI exposes `nerdbot watch-classify <path>` for one event. Decisions return `wait`, `ignore`, `queue-review`, `quarantine`, or `classify` and keep canonical surfaces review-first.

## Requirements

- Debounce file events and wait for path stability before reading files.
- Ignore volatile editor state unless explicitly configured.
- Record checkpoints so interrupted watches can replay.
- Quarantine unreadable, conflicting, or risky events.
- Emit review items for save-back rather than mutating query/audit paths.

Volatile `.obsidian` workspace state and rebuildable `indexes/generated/` artifacts are ignored by default. Unsafe paths are quarantined. Shared templates, snippets, raw sources, wiki pages, indexes, schema, config, and activity changes create review-visible events before any follow-up work runs.
