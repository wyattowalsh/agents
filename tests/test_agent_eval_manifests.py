"""Structural checks for evals/agents/*/evals.json maintainer manifests."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_EVALS_ROOT = ROOT / "evals" / "agents"

REQUIRED_EVAL_FIELDS = {"id", "prompt", "expected_output", "assertions"}


def _load_manifest(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_agent_eval_manifests_exist_for_priority_agents() -> None:
    expected = {
        "triage-lead",
        "permission-policy-auditor",
        "mcp-capability-mapper",
        "bridge-consistency-checker",
        "skill-author",
        "prompt-optimizer",
        "agent-change-recorder",
        "agent-eval-runner",
        "agent-permission-simulator",
        "agent-registry-publisher",
        "agent-transpiler",
        "mcp-template-maintainer",
    }
    present = {path.name for path in AGENT_EVALS_ROOT.iterdir() if path.is_dir()}
    missing = expected - present
    assert not missing, f"missing evals/agents manifests: {sorted(missing)}"


def test_agent_eval_manifest_shape() -> None:
    for agent_dir in sorted(AGENT_EVALS_ROOT.iterdir()):
        if not agent_dir.is_dir():
            continue
        manifest_path = agent_dir / "evals.json"
        assert manifest_path.is_file(), f"missing {manifest_path}"
        manifest = _load_manifest(manifest_path)
        assert manifest.get("agent_name") == agent_dir.name
        evals = manifest.get("evals")
        assert isinstance(evals, list), f"{manifest_path}: evals must be a list"
        assert evals, f"{manifest_path}: evals must be non-empty"
        ids: set[str] = set()
        for case in evals:
            assert isinstance(case, dict)
            missing = REQUIRED_EVAL_FIELDS - case.keys()
            assert not missing, f"{manifest_path} case {case.get('id')}: missing {sorted(missing)}"
            case_id = case["id"]
            assert case_id not in ids, f"duplicate eval id {case_id!r} in {manifest_path}"
            ids.add(case_id)
            assertions = case["assertions"]
            assert isinstance(assertions, list)
            assert assertions


def test_agent_eval_manifests_reference_portable_agent_files() -> None:
    for manifest_path in sorted(AGENT_EVALS_ROOT.glob("*/evals.json")):
        manifest = _load_manifest(manifest_path)
        agent_name = manifest["agent_name"]
        portable = ROOT / "agents" / f"{agent_name}.md"
        assert portable.is_file(), f"{manifest_path}: portable agent missing at {portable}"
        referenced = False
        for case in manifest["evals"]:
            files = case.get("files") or []
            if f"agents/{agent_name}.md" in files:
                referenced = True
                break
        assert referenced, f"{manifest_path}: no case references agents/{agent_name}.md"