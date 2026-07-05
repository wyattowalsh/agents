# Output Formats

Trafilatura supports multiple output formats via CLI flags or `--output-format`.

## Formats

| Format | CLI flag | Use when |
| --- | --- | --- |
| txt | default | Plain main text |
| markdown | `--markdown` | Readable article with light formatting |
| json | `--json` | Structured extraction + optional metadata |
| xml | `--xml` | Basic XML structure |
| xmltei | `--xmltei` | TEI corpus workflows |
| html | `--html` | HTML output (v1.11+) |
| csv | `--csv` | Tabular export |

## Metadata

- `--with-metadata` — include title, author, date, url in output
- `--only-with-metadata` — skip documents missing essential metadata

## Precision and recall

- `--precision` — less noise, possibly less text
- `--recall` — more text, possibly more noise
- `--fast` — skip fallback detection (faster, may miss content)

## Element controls

- `--no-comments` / `--no-tables` — exclude those sections
- `--formatting` — keep bold/italic (markdown/xml)
- `--links` / `--images` — experimental; best with xml/json

## Skill default

Single URL reads: **markdown** for summaries, **json** when metadata fields are required.