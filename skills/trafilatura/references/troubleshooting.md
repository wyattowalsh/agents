# Troubleshooting

## Missing or partial content

1. Retry with `--recall` on `extract_url.py` or CLI.
2. Remove `--fast` if used.
3. Try `--no-comments` / `--no-tables` toggles if structure is odd.
4. Use `html2txt`-style fallback via piping raw HTML if extraction is too strict.

## Blocked downloads

- Sites may block default user-agent or IP.
- Install `trafilatura[all]` for pycurl support.
- Pipe external download:

```bash
wget -qO- 'URL' | trafilatura --markdown
curl -sL 'URL' | trafilatura --json
```

## Link rot / unavailable pages

```bash
uv run python scripts/extract_url.py --url 'URL' --archived
```

Internet Archive fallback is slow; use for small URL sets.

## JavaScript-rendered pages

Trafilatura parses raw HTML. Content injected only by JavaScript may be absent. Use browser automation separately, then **pipe** saved HTML through trafilatura.

## Paywalls and cookies

- Do not bypass paywalls or DRM.
- Cookies belong in user-owned `settings.cfg` — never commit secrets.
- Separate download infrastructure from extraction when sites require login.