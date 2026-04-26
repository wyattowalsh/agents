# CLI and API Recipes

Use these patterns as starting points. Confirm exact flags and field names against the installed `docling-graph --help` and package docs when precision matters.

## CLI Convert

```bash
docling-graph convert docs/filing.pdf \
  --template templates.sec:FilingGraph \
  --output out/filing \
  --provider openai \
  --model gpt-4.1-mini \
  --extraction-contract staged \
  --schema-enforced-llm \
  --structured-sparse-check \
  --llm-streaming \
  --show-llm-config
```

After conversion:

```bash
docling-graph inspect out/filing
```

Review graph counts, missing required fields, structured-output fallback, sparse-check findings, and provider/model config.

## Direct Contract Smoke Run

```bash
docling-graph convert samples/simple.pdf \
  --template templates.invoice:InvoiceGraph \
  --output out/simple \
  --extraction-contract direct \
  --provider openai \
  --model gpt-4.1-mini \
  --schema-enforced-llm \
  --structured-sparse-check
```

Use this for simple templates and small samples. If required relationships are consistently missing, switch to staged or delta rather than adding vague fields.

## Staged Contract Run

```bash
docling-graph convert samples/report.pdf \
  --template templates.report:ReportGraph \
  --output out/report \
  --extraction-contract staged \
  --provider mistral \
  --model mistral-large-latest \
  --schema-enforced-llm \
  --llm-streaming
```

Inspect stage outputs and merge behavior before exporting.

## Delta Contract Run

```bash
docling-graph convert samples/contracts.pdf \
  --template templates.contracts:ContractGraph \
  --output out/contracts \
  --extraction-contract delta \
  --provider openai \
  --model gpt-4.1 \
  --schema-enforced-llm \
  --structured-sparse-check
```

Use delta for complex graphs with repeated observations, high-cardinality entities, or relationship resolution across sections. Verify stable IDs and duplicate-resolution behavior.

## API Equivalent

```python
from pathlib import Path

from docling_graph import run_pipeline
from docling_graph.pipeline import PipelineConfig

from templates.contracts import ContractGraph

config = PipelineConfig(
    input_path=Path("samples/contracts.pdf"),
    output_dir=Path("out/contracts"),
    template=ContractGraph,
    provider_override="openai",
    model_override="gpt-4.1",
    extraction_contract="delta",
    structured_output=True,
    structured_sparse_check=True,
    llm_streaming=True,
    gleaning_enabled=True,
    gleaning_max_passes=2,
    dump_to_disk=True,
    debug=True,
)

context = run_pipeline(config)
```

Keep secrets in environment variables. Do not serialize provider keys into config snapshots or traces.

## Batch Manifest Pattern

Use a manifest that is explicit enough to resume safely:

```json
[
  {
    "source": "docs/a.pdf",
    "template": "templates.sec:FilingGraph",
    "output": "out/a",
    "provider": "openai",
    "model": "gpt-4.1-mini",
    "extraction_contract": "staged",
    "status": "pending"
  }
]
```

Batch validation should aggregate:

- Success/failure count by document class.
- Required-field coverage.
- Relationship density.
- Duplicate IDs and orphan relationship count.
- Structured-output fallback rate.
- Provider cost and latency.

## Debug Handoff

Include:

- Exact CLI command or redacted `PipelineConfig`.
- Template module and root model.
- Source sample or reproducible excerpt.
- Output directory tree.
- `debug/trace_data.json`.
- Inspect report.
- Expected graph invariant that failed.
