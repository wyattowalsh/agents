# CLI and API Recipes

## Contents

1. Environment Check
2. CLI Flow
3. CLI Command Patterns
4. API Flow
5. Error-Aware API Example
6. Output Layout

## Environment Check

Use this before live command guidance when local evidence matters:

```bash
uv run python skills/docling-graph/scripts/check-env.py --format json
```

With a template:

```bash
uv run python skills/docling-graph/scripts/check-env.py \
  --template templates.BillingDocument \
  --format json
```

## CLI Flow

The normal operator flow is:

1. `docling-graph init` when a reusable config is desired.
2. `docling-graph convert SOURCE --template TEMPLATE ...`.
3. Inspect generated outputs.
4. Adjust template/config and rerun into a new output directory.

For first runs, include `--debug` and an explicit `--output-dir`.

## CLI Command Patterns

Minimal:

```bash
docling-graph convert document.pdf \
  --template "templates.BillingDocument" \
  --output-dir "outputs/document"
```

Text-heavy remote LLM:

```bash
docling-graph convert research.pdf \
  --template "templates.ScholarlyPaper" \
  --backend llm \
  --inference remote \
  --provider mistral \
  --model mistral-large-latest \
  --processing-mode many-to-one \
  --use-chunking \
  --debug \
  --output-dir "outputs/research"
```

Local form/image workflow:

```bash
docling-graph convert form.jpg \
  --template "templates.FormRecord" \
  --backend vlm \
  --inference local \
  --processing-mode one-to-one \
  --output-dir "outputs/form"
```

Cypher export:

```bash
docling-graph convert document.pdf \
  --template "templates.GraphRecord" \
  --export-format cypher \
  --output-dir "outputs/neo4j"
```

## API Flow

Use API mode when the workflow is embedded in an application, job runner, notebook, or service.

Short form:

```python
from docling_graph import run_pipeline

context = run_pipeline({
    "source": "document.pdf",
    "template": "templates.BillingDocument",
    "backend": "llm",
    "inference": "remote",
})

graph = context.knowledge_graph
model = context.pydantic_model
```

Typed config:

```python
from docling_graph import PipelineConfig, run_pipeline

config = PipelineConfig(
    source="document.pdf",
    template="templates.BillingDocument",
    backend="llm",
    inference="remote",
    processing_mode="many-to-one",
    use_chunking=True,
    dump_to_disk=True,
    output_dir="outputs/document",
)

context = run_pipeline(config)
```

## Error-Aware API Example

```python
from docling_graph import PipelineConfig, run_pipeline
from docling_graph.exceptions import (
    ClientError,
    ConfigurationError,
    DoclingGraphError,
    ExtractionError,
)

config = PipelineConfig(
    source="document.pdf",
    template="templates.BillingDocument",
    backend="llm",
    inference="remote",
    dump_to_disk=True,
    output_dir="outputs/document",
)

try:
    context = run_pipeline(config)
except ConfigurationError as exc:
    raise RuntimeError(f"Invalid pipeline config: {exc}") from exc
except ClientError as exc:
    raise RuntimeError("Provider/API failure; check credentials and rate limits") from exc
except ExtractionError as exc:
    raise RuntimeError("Extraction failed; inspect debug traces and partial outputs") from exc
except DoclingGraphError as exc:
    raise RuntimeError(f"Docling Graph failure: {exc}") from exc

graph = context.knowledge_graph
if graph.number_of_nodes() == 0:
    raise RuntimeError("Extraction returned an empty graph")
```

## Output Layout

When file exports are enabled, expect a structure like:

```text
outputs/<run>/
  metadata.json
  docling/
    document.json
    document.md
  docling_graph/
    graph.json
    nodes.csv
    edges.csv
    graph.html
    report.md
```

Always validate the actual output tree because export flags and package versions can change file presence.
