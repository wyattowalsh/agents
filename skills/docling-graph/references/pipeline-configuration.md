# Pipeline Configuration

## Contents

1. Decision Matrix
2. Backend Selection
3. Inference Mode
4. Processing Mode
5. Chunking
6. Provider and Model
7. Docling Pipeline
8. Batch Defaults

## Decision Matrix

Use this reference in **Plan**, **Convert**, and **Batch** modes.

| Input condition | Recommended starting point |
|---|---|
| Text-heavy PDF, article, contract, markdown | LLM backend |
| Image, form, scanned page, layout-heavy source | VLM backend if local runtime supports it |
| Multi-page document with cross-page facts | `many-to-one` |
| Independent forms/pages | `one-to-one` |
| Large document or context pressure | enable chunking |
| First run or failure-prone domain | enable debug traces |
| Sensitive data | prefer local inference; call out remote exposure |

## Backend Selection

**LLM** is the default for text-heavy extraction:

- contracts
- research papers
- financial filings
- policies
- markdown or HTML
- documents where semantic relationships matter more than visual layout

**VLM** is strongest when layout and image content are primary:

- ID cards
- invoices as images
- forms
- scans
- table-heavy layouts where OCR/vision quality dominates

If the user lacks GPU/local VLM capacity, offer LLM as fallback after Docling conversion and explain the trade-off.

## Inference Mode

| Mode | Use when | Risks |
|---|---|---|
| `local` | sensitive data, no API budget, local models available | hardware setup, speed, memory |
| `remote` | quality/provider access matters, data can leave machine | API keys, cost, rate limits, privacy |

Never silently choose remote inference for regulated or confidential documents.

## Processing Mode

| Mode | Use when | Trade-off |
|---|---|---|
| `many-to-one` | facts span pages or one graph should represent the full document | higher context and merge complexity |
| `one-to-one` | pages are independent or each page is a separate form | faster and simpler, weaker cross-page linking |

Default to `many-to-one` for contracts, papers, filings, and reports. Default to `one-to-one` for batches of independent forms.

## Chunking

Enable chunking when:

- document has more than a few pages
- source has long sections or many tables
- provider context limits are likely
- extraction fails with context or memory pressure

Disable chunking when:

- source is small
- full context is essential for one global decision
- the first-pass goal is a fast smoke test

If disabling chunking, add a validation note: verify no facts were missed because context was truncated.

## Provider and Model

Docling Graph routes LLM extraction through provider/model settings. Choose provider only after these are known:

1. data sensitivity
2. available API keys or local runtimes
3. expected context length
4. structured-output reliability
5. cost and latency tolerance

For remote providers, check that required env vars are present without printing values. Use:

```bash
uv run python skills/docling-graph/scripts/check-env.py --provider-env OPENAI_API_KEY --format json
```

## Docling Pipeline

Use OCR pipeline for standard PDFs and faster runs. Use vision pipeline for complex layouts, tables, forms, and scanned sources.

If the user reports poor table or layout extraction, revisit the Docling pipeline before changing the Pydantic template.

## Batch Defaults

For batches:

1. Use one output directory per input.
2. Save command/config per document.
3. Retry failed documents only.
4. Preserve partial outputs.
5. Start with a small sample before the full corpus.
6. Record provider, model, template version, and command flags for reproducibility.
