---
name: trafilatura
description: >-
  Extract clean article text and metadata from URLs or HTML with trafilatura
  CLI. Use for single-page extraction, piped/local HTML, bounded discovery.
  NOT for research synthesis (research), PDFs (docling), raw fetch (fetch), video (yt-dlp).
argument-hint: "<extract|pipe|discover|batch|local|metadata|archived|doctor|help> [target]"
user-invocable: true
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
allowed-tools: Bash Read Glob Write
---

# Trafilatura

CLI skill for [trafilatura](https://github.com/adbar/trafilatura): extract main article text and metadata from URLs, piped HTML, or local files. Follow the **stdout-first protocol** before any batch writes.

**Scope:** Single-page extraction, metadata JSON, piped/local HTML, bounded URL discovery (`--list`), and user-approved batch processing. **NOT for:** multi-source research (`research`), PDF/tables (`docling`), raw page fetch (`fetch`/`fetcher`), video hosts (`yt-dlp`), or paywall bypass.

---

## Canonical Vocabulary

| Term | Meaning | NOT |
| --- | --- | --- |
| **extract** | Single URL → clean text via CLI | full crawl harvest |
| **metadata** | JSON output with `with_metadata` | bare URL probe only |
| **pipe** | Stdin or local `.html` file as input | download from URL |
| **discover** | `--feed` / `--sitemap` / `--crawl` / `--probe` with `--list` | bulk download |
| **batch** | `-i` link list → output directory | silent mass scrape |
| **local** | `--input-dir` reprocess saved HTML | live fetch |
| **archived** | `--archived` Internet Archive fallback | paywall bypass |
| **precision** | `--precision` — less noise | default when content missing |
| **recall** | `--recall` — more text | default when noise high |
| **doctor** | Preflight JSON for binary and version | live URL smoke |

---

## Dispatch

| `$ARGUMENTS` | Mode | Action |
| --- | --- | --- |
| `doctor` / `preflight` | **Doctor** | Run `scripts/doctor.py --format json` |
| `extract <url>` / bare `https://…` | **Extract** | Stdout-first via `extract_url.py` |
| `metadata <url>` | **Metadata** | `extract_url.py` with `--with-metadata --format json` |
| `pipe <file>` / stdin HTML | **Pipe** | `trafilatura` on file or stdin |
| `discover feed <url>` | **Discover** | `list_urls.py --mode feed` (`--list` only) |
| `discover sitemap <url>` | **Discover** | `list_urls.py --mode sitemap` |
| `discover crawl <url>` | **Discover** | `list_urls.py --mode crawl` |
| `discover probe <url>` | **Discover** | `list_urls.py --mode probe` |
| `batch <listfile>` | **Batch** | Approval gate → `-i` + `-o` under user dir |
| `local <input-dir>` | **Local** | Approval gate → `--input-dir` + `-o` |
| `archived <url>` | **Archived** | `extract_url.py --archived` after normal fetch fails |
| Natural language: "main text", "clean article", "extract from URL" | **Auto** | Map to extract (stdout-first) |
| _(empty)_ | **Help** | Gallery + protocol + references |

### Auto-Detection Heuristic

1. URL + "sitemap", "feed", "crawl", "list URLs" → **Discover** (`--list` only).
2. URL + "metadata", "title", "author", "date" → **Metadata**.
3. Path to `.html` or "pipe", "stdin", "local file" → **Pipe**.
4. Path to URL list file or "batch" → **Batch** (approval gate).
5. Directory of saved HTML → **Local** (approval gate).
6. "Archive", "wayback", "link rot" after failed fetch → **Archived**.
7. Bare URL or "extract", "clean", "article text" → **Extract**.
8. Ambiguous → ask: extract, metadata, discover list, or batch?

---

## Stdout-First Protocol

Run stages in order. **Do not skip doctor** after CLI errors. **Do not batch-write** until single-URL needs are met or the user explicitly approves bulk scope.

### Stage 1 — Doctor (once per session or after errors)

```bash
uv run python scripts/doctor.py --format json
```

Stop on `ok: false` or any check with `status: fail` (missing `trafilatura` binary).

### Stage 2 — Extract (preferred for single URLs)

```bash
uv run python scripts/extract_url.py --url 'https://…' --format json
```

Markdown (default readable):

```bash
uv run python scripts/extract_url.py --url 'https://…' --output-format markdown
```

From probe JSON, report: `url`, `title`, `date` (if metadata), `text_length`, and format. Load [references/output-formats.md](references/output-formats.md) when choosing formats.

### Stage 3 — Discover (list only by default)

```bash
uv run python scripts/list_urls.py --mode sitemap --url 'https://…' --format json
```

Present `url_count` and a sample of URLs. **Do not** chain into batch download without explicit user approval.

### Stage 4 — Batch / local (explicit approval required)

Before running:

1. Confirm URL count or directory scope.
2. Confirm output directory (default: `$HOME/Downloads/trafilatura/output/`).
3. Confirm politeness acknowledgment — see [references/politeness-and-ethics.md](references/politeness-and-ethics.md).

```bash
mkdir -p "$HOME/Downloads/trafilatura/output"
trafilatura -i list.txt -o "$HOME/Downloads/trafilatura/output/" --markdown --backup-dir "$HOME/Downloads/trafilatura/html-backup/"
```

### Stage 5 — Escalation (missing or blocked content)

1. Retry with `--recall` (CLI) or `--recall` flag on `extract_url.py`.
2. If download blocked: `wget -qO- 'URL' | trafilatura` or `curl -sL 'URL' | trafilatura`.
3. If unavailable: `extract_url.py --archived` or `trafilatura --archived -u 'URL'`.
4. If still empty: note JS-rendered page limitation — no in-tool browser automation. See [references/troubleshooting.md](references/troubleshooting.md).

### MCP fallback (no Bash)

When doctor fails because the harness has no shell, use MCPHub `trafilatura` → `fetch_and_extract`. Document degraded path. See [references/mcp-fallback.md](references/mcp-fallback.md).

---

## Mode Details

### Extract

- Use bundled `extract_url.py` (wraps `trafilatura -u`).
- Read-only regarding repo tree; stdout or JSON envelope only.
- Default output: markdown for human summary; json when structured metadata is needed.

### Metadata

```bash
uv run python scripts/extract_url.py --url 'https://…' --output-format json --with-metadata
```

### Pipe

```bash
trafilatura --markdown < page.html
cat page.html | trafilatura --json --no-tables
```

### Discover

Modes: `feed`, `sitemap`, `crawl`, `probe`. Always `--list` via `list_urls.py` unless user explicitly requests harvest.

Optional filters: `--url-filter`, `--target-language` (requires `trafilatura[all]`). See [references/discovery.md](references/discovery.md).

### Batch

- Parse list file (one URL per line).
- Require approval before `-i` runs.
- Recommend `--backup-dir` for HTML archival.
- Never write into the agents repo.

### Local

- `--input-dir` for previously downloaded HTML.
- Mirror structure with `--keep-dirs` when needed.
- Approval gate same as batch.

### Archived

- Use when `fetch_url` equivalent returns nothing.
- Slow; best for small URL sets.

### Doctor

```bash
uv run python scripts/doctor.py --format json
```

### Help

Show dispatch table, stdout-first protocol, default paths, and reference index.

### Gallery (Empty Arguments)

| # | Task | Example |
| --- | --- | --- |
| 1 | Preflight | `/trafilatura doctor` |
| 2 | Extract article | `/trafilatura extract https://example.org/article` |
| 3 | Metadata JSON | `/trafilatura metadata https://example.org/article` |
| 4 | Discover sitemap | `/trafilatura discover sitemap https://example.org` |
| 5 | Pipe local HTML | `/trafilatura pipe saved-page.html` |
| 6 | Archived fallback | `/trafilatura archived https://example.org/missing` |

> Pick a number, a mode from the dispatch table, or paste a URL and say whether you need extract, metadata, or URL discovery.

---

## Critical Rules

1. **Doctor before first extract** in a session (or after CLI errors).
2. **Stdout-first for single URLs** — use `extract_url.py` before filesystem batch writes.
3. **Discover list-only by default** — present URL count; no auto bulk download.
4. **Explicit approval for batch/local** — confirm scope, output dir, politeness.
5. **No paywall bypass coaching** — see [references/politeness-and-ethics.md](references/politeness-and-ethics.md).
6. **Not Fetch MCP primary** — article main-text extraction belongs here when trafilatura is appropriate.
7. **Not research** — multi-source synthesis uses `/research`.
8. **Not docling** — PDFs and table-heavy documents use docling MCP.
9. **Not yt-dlp** — video/audio hosts use `/yt-dlp`.
10. **Report provenance** — URL, format, title/date if present, text length in summary.

---

## Troubleshooting

See [references/troubleshooting.md](references/troubleshooting.md) for precision/recall, archived fallback, wget/curl pipe, and JS-rendered pages.

---

## References

| File | Use when |
| --- | --- |
| [output-formats.md](references/output-formats.md) | Choosing txt/json/markdown/xml formats |
| [discovery.md](references/discovery.md) | Feed, sitemap, crawl, url-filter |
| [troubleshooting.md](references/troubleshooting.md) | Missing content, blocked downloads |
| [politeness-and-ethics.md](references/politeness-and-ethics.md) | Robots, rate limits, refusals |
| [mcp-fallback.md](references/mcp-fallback.md) | Shell-less harness / MCPHub path |

---

## Scripts

| Script | Purpose |
| --- | --- |
| `scripts/doctor.py` | JSON preflight: trafilatura binary and version |
| `scripts/extract_url.py` | Single-URL CLI wrapper with JSON envelope |
| `scripts/list_urls.py` | Discovery `--list` wrapper |
| `scripts/check.py` | Validate skill manifest and evals |

---

## Examples

```bash
# Preflight
uv run python scripts/doctor.py --format json

# Extract (stdout-first)
uv run python scripts/extract_url.py --url 'https://github.blog/2019-03-29-leader-spotlight-erin-spiceland/' --output-format markdown

# Metadata JSON
uv run python scripts/extract_url.py --url 'https://example.org' --output-format json --with-metadata

# Discover sitemap URLs (list only)
uv run python scripts/list_urls.py --mode sitemap --url 'https://www.sitemaps.org/' --format json

# Pipe local HTML
trafilatura --markdown < saved.html

# Batch (after user approval)
trafilatura -i urls.txt -o "$HOME/Downloads/trafilatura/output/" --markdown --backup-dir "$HOME/Downloads/trafilatura/html-backup/"
```