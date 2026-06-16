# Coordinator Contract

Machine-readable wave manifests and filesystem artifact handoffs for discover-skills.

## W0 Deterministic Scans

Run from repository root before spawning scouts:

```bash
python skills/discover-skills/scripts/inventory_scan.py --repo-root . -o artifacts/<sid>/wave0/inventory.json
python skills/discover-skills/scripts/mcp_scan.py --repo-root . -o artifacts/<sid>/wave0/mcp.json
python skills/discover-skills/scripts/plugin_scan.py --repo-root . -o artifacts/<sid>/wave0/plugins.json
python skills/discover-skills/scripts/invoke_surfaces.py --repo-root . -o artifacts/<sid>/wave0/surfaces.json
python skills/discover-skills/scripts/gap_engine.py \
  --taxonomy skills/discover-skills/data/discovery-taxonomy.json \
  --inventory artifacts/<sid>/wave0/inventory.json \
  --mcp artifacts/<sid>/wave0/mcp.json \
  --plugins artifacts/<sid>/wave0/plugins.json \
  --harness artifacts/<sid>/wave0/surfaces.json \
  -o artifacts/<sid>/wave0/gap-report.json
python skills/discover-skills/scripts/validate_session.py artifacts/<sid>/wave0/gap-report.json
python skills/discover-skills/scripts/parity_check.py
```

Journal init (v2) should record the artifact root:

```bash
python skills/discover-skills/scripts/journal-store.py init \
  --focus "full scan" \
  --artifact-root artifacts/<sid>
```

## Manifest Planning

```bash
python skills/discover-skills/scripts/coordinator.py plan \
  --gap artifacts/<sid>/wave0/gap-report.json \
  --session-id <sid> \
  --wave 2 \
  --artifacts-root artifacts/<sid> \
  -o artifacts/<sid>/wave2/manifest.json
```

## Accounting Verify

```bash
python skills/discover-skills/scripts/coordinator.py verify \
  --manifest artifacts/<sid>/wave2/manifest.json \
  --artifacts artifacts/<sid>/wave2
```

Do not advance to ideation until `ok: true`.

## Scout Artifact Shape

Each scout writes JSON to its `outputs.artifact` path:

```json
{
  "task_id": "W2-RS-00",
  "role": "registry-scout",
  "status": "success",
  "candidates": [],
  "errors": [],
  "provenance": {"tool": "npx_skills.find"}
}
```

Registry scouts should call:

```bash
python skills/discover-skills/scripts/npx_skills.py find "<query>" --timeout-sec 45 -o <artifact-path>
```

## Merge

```bash
python skills/discover-skills/scripts/merge_artifacts.py \
  --artifacts artifacts/<sid>/wave2 \
  --gap-report artifacts/<sid>/wave0/gap-report.json \
  -o artifacts/<sid>/merged/candidates.json
```

## Recovery

Follow orchestrator Recovery Ladder: resume → re-spawn with manifest slice → re-assign → escalate. Wave 2 does not allow `verify --partial-ok`.