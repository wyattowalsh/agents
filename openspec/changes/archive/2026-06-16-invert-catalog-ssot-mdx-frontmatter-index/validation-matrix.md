# Validation Matrix

| Surface | Command | Expected Result | Notes |
|---------|---------|-----------------|-------|
| Schema files present + load | `python -c 'import json; a=json.load(open("config/schemas/skills-catalog-authoring.schema.json")); i=json.load(open("config/schemas/skills-catalog-index.schema.json")); print(a["title"], i["title"])'` | Titles match; no parse error |  |
| Schema tests (jsonschema or structural) | `uv run pytest tests/test_skills_catalog_schemas.py -q --tb=line` | All pass (4 tests) | Uses jsonschema when available in dev env. |
| OpenSpec artifacts | `uv run wagents openspec validate` | Pass for this change (5 files + no syntax issues) |  |
| Minimal authoring shape | `python -c '
from jsonschema import Draft202012Validator
import json
auth = json.load(open("config/schemas/skills-catalog-authoring.schema.json"))
idx = json.load(open("config/schemas/skills-catalog-index.schema.json"))
Draft202012Validator(auth).validate({"skill_id":"x","source_kind":"external","name":"x","description":"d"})
print("authoring ok")
e = {"skill_id":"x","source_kind":"external","name":"x","description":"d","body_path":"docs/src/authoring/skills/external/x.mdx"}
Draft202012Validator(idx).validate({"version":1,"generated_at":"2026-06-16T00:00:00Z","entries":[e]})
print("index ok")
'` | "authoring ok" + "index ok" on stdout | Demonstrates roundtrip for W0. |
| Pre-generate parity (baseline) | `uv run wagents skills sync --dry-run && uv run wagents validate` | Exit 0; no new drift from this scaffolding |  |
| Docs generate baseline (no-installed, CI mode) | `uv run wagents docs generate --no-installed` | Succeeds (may warn on missing authoring dir until W1) |  |

## W7 Full Validation Commands (from plan)

These represent the final-wave (W7) gates per the SSOT inversion parallel DAG plan (hyperfine tasks, merge gates M1-M5). Run after all prior waves land (schemas, migration, dual-read, generate emission, consumer retarget, policy, tests).

```bash
# Core
uv run wagents validate
uv run wagents eval validate
uv run pytest tests/test_skills_catalog_schemas.py tests/test_external_skills.py tests/test_docs.py tests/test_site_model.py tests/test_validate*.py -q --tb=line

# Generate + index emission (CI parity)
uv run wagents docs generate --no-installed
python -c '
import json, os
idx = "docs/src/generated/generated-registries.json"
assert os.path.exists(idx), "index missing"
data = json.load(open(idx))
assert data["version"] == 1
assert any(e["source_kind"]=="external" for e in data.get("entries",[]))
print("index emitted + versioned")
'

# Sync + drift (dual-read still green)
uv run wagents skills sync --dry-run
uv run python scripts/sync_agent_stack.py --targets repo --check || true

# Parity / catalog
uv run python -m wagents.catalog_rows  # or equivalent parity helper
uv run wagents docs generate --include-installed  # local preview only

# Docs build
cd docs && pnpm install --frozen-lockfile && pnpm build

# OpenSpec + full repo gates
uv run wagents openspec validate
uv run python -m pytest -q --tb=no   # broad slice or full as per plan
git diff --check
```

## Blockers

- None for pure W0 scaffolding (schemas + OpenSpec + test). Later waves surface dual-read and generate emission work.

## Deferred Checks

- Full authoring migration of 100+ external rows (parallel per-skill waves).
- Cutover (remove dual-read fallback) — after W7 sign-off + sufficient bake time.
- Harness-surface / other Bucket A inversion (separate OpenSpec changes).
- Live apply of skills sync during W7 (use --dry-run in gates).
