# OSS Dependencies

## Baseline

The baseline package has no runtime dependency beyond Python. This keeps bootstrap, inventory, lint, and plan commands available in constrained local repos.

## Optional Adapter Targets

| Capability | Preferred package | Baseline status |
|------------|-------------------|-----------------|
| Rendered/deep crawl | `crawl4ai>=0.8.6` | Optional extra |
| Large-crawl orchestration | `crawlee>=0.4.0b3` | Optional crawl extra |
| Static extraction | `trafilatura>=2.0.0`, `selectolax>=0.4.7` | Optional extra |
| Broad document parsing | `docling-slim>=2.92.0` | Optional docs extra |
| Granite VLM document path | `docling>=2.92.0` and Docling VLM/DocTags path | Optional `vlm` extra |
| PDF specialist parser | `opendataloader-pdf>=2.4.1` | Optional adapter |
| Fallback conversion | `markitdown>=0.1.5` | Optional adapter |
| Local vector extension | `sqlite-vec>=0.1.9` | Optional semantic extra |

Do not make these imports mandatory in package modules that power baseline commands.
