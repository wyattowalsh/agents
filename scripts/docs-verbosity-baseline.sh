#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MANIFEST="$ROOT/planning/manifests/docs-verbosity-baseline.json"
CONTENT="$ROOT/docs/src/content/docs"
python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path

root = Path("$ROOT")
content = root / "docs/src/content/docs"
pages = {}
for path in sorted(content.rglob("*.mdx")):
    rel = str(path.relative_to(content))
    pages[rel] = len(path.read_text(encoding="utf-8").splitlines())

manifest = {
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "pages": pages,
}
out = root / "planning/manifests/docs-verbosity-baseline.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {out} ({len(pages)} pages)")
PY
