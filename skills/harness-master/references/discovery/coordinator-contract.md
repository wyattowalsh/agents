# Coordinator Contract

Machine-readable wave manifests and filesystem artifact handoffs for harness-master discovery.

## W0 Deterministic Scans

Run from repository root before spawning scouts:

```bash
python skills/harness-master/scripts/discovery/inventory_scan.py --repo-root . -o artifacts/<sid>/wave0/inventory.json
python skills/harness-master/scripts/discovery/mcp_scan.py --repo-root . -o artifacts/<sid>/wave0/mcp.json
python skills/harness-master/scripts/discovery/plugin_scan.py --repo-root . -o artifacts/<sid>/wave0/plugins.json
python skills/harness-master/scripts/discovery/hook_scan.py --repo-root . -o artifacts/<sid>/wave0/hooks.json
python skills/harness-master/scripts/discovery/invoke_surfaces.py --repo-root . -o artifacts/<sid>/wave0/surfaces.json
python skills/harness-master/scripts/discovery/gap_engine.py \
  --taxonomy skills/harness-master/data/discovery/discovery-taxonomy.json \
  --inventory artifacts/<sid>/wave0/inventory.json \
  --mcp artifacts/<sid>/wave0/mcp.json \
  --plugins artifacts/<sid>/wave0/plugins.json \
  --harness artifacts/<sid>/wave0/surfaces.json \
  --hooks artifacts/<sid>/wave0/hooks.json \
  -o artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/validate_session.py artifacts/<sid>/wave0/gap-report.json
python skills/harness-master/scripts/discovery/parity_check.py
```

Journal init (v2) should record the artifact root:

```bash
python skills/harness-master/scripts/discovery/journal-store.py init \
  --focus "full scan" \
  --artifact-root artifacts/<sid>
```

## Manifest Planning

```bash
python skills/harness-master/scripts/discovery/coordinator.py plan \
  --gap artifacts/<sid>/wave0/gap-report.json \
  --session-id <sid> \
  --wave 2 \
  --artifacts-root artifacts/<sid> \
  -o artifacts/<sid>/wave2/manifest.json
```

## Accounting Verify

```bash
python skills/harness-master/scripts/discovery/coordinator.py verify \
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
python skills/harness-master/scripts/discovery/npx_skills.py find "<query>" --timeout-sec 45 -o <artifact-path>
```

## Merge

```bash
python skills/harness-master/scripts/discovery/merge_artifacts.py \
  --artifacts artifacts/<sid>/wave2 \
  --gap-report artifacts/<sid>/wave0/gap-report.json \
  -o artifacts/<sid>/merged/candidates.json
```

## Recovery

Follow orchestrator Recovery Ladder: resume → re-spawn with manifest slice → re-assign → escalate. Wave 2 does not allow `verify --partial-ok`.