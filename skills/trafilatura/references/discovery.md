# Discovery Modes

Link discovery uses `--list` to enumerate URLs without downloading content.

## Modes

| Mode | CLI | Purpose |
| --- | --- | --- |
| feed | `--feed URL --list` | Atom/RSS feed URLs |
| sitemap | `--sitemap URL --list` | Sitemap URLs |
| crawl | `--crawl URL --list` | Follow internal links (experimental) |
| probe | `--probe URL --list` | Probe for extractable content |

Use `list_urls.py` in this skill:

```bash
uv run python scripts/list_urls.py --mode sitemap --url 'https://example.org' --format json
```

## Filters

- `--url-filter PATTERN` — space-separated substring filters
- `--target-language ISO639-1` — requires `trafilatura[all]` / py3langid

## Conservative policy

1. Always present `url_count` and `sample_urls` to the user.
2. Do not auto-run batch `-i` after discovery without explicit approval.
3. For large sitemaps, suggest filtering before batch processing.

## Courlan (URL hygiene)

For cleaning URL lists before batch runs, see [trafilatura url-management docs](https://trafilatura.readthedocs.io/en/latest/url-management.html). Optional `courlan` CLI for normalize/sample operations.