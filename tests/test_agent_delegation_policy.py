"""OpenCode task delegation parity vs config/agent-delegation-policy.json."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "config" / "agent-delegation-policy.json"
POLICY_SCHEMA_PATH = ROOT / "config" / "schemas" / "agent-delegation-policy.schema.json"
OPENCODE_AGENTS_PATH = ROOT / "config" / "opencode-agents.json"
AGENTS_DIR = ROOT / "agents"

CANONICAL_AGENT_NAMES = sorted(
    path.stem for path in AGENTS_DIR.glob("*.md") if path.name != "README.md"
)

TRIAGE_ROUTING_TARGETS = {
    "security-auditor",
    "docs-writer",
    "mcp-template-maintainer",
    "skill-author",
    "bridge-consistency-checker",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _task_allowlist(permission: dict) -> set[str]:
    task = permission.get("task")
    if not isinstance(task, dict):
        return set()
    return {key for key, value in task.items() if key != "*" and value == "allow"}


def _overlay_by_name() -> dict[str, dict]:
    data = _load_json(OPENCODE_AGENTS_PATH)
    return {entry["name"]: entry for entry in data["agents"]}


def test_delegation_policy_schema_valid() -> None:
    policy = _load_json(POLICY_PATH)
    schema = _load_json(POLICY_SCHEMA_PATH)
    jsonschema.validate(policy, schema)


def test_delegation_policy_agents_exist_in_portable_corpus() -> None:
    policy = _load_json(POLICY_PATH)
    portable = set(CANONICAL_AGENT_NAMES)
    for delegator, spec in policy["delegators"].items():
        assert delegator in portable, f"delegator {delegator!r} missing from agents/"
        for target in spec["allow"]:
            if target in {"general", "explore"}:
                continue
            assert target in portable, f"{delegator} allow target {target!r} missing from agents/"


def test_delegation_policy_denies_self_delegation() -> None:
    policy = _load_json(POLICY_PATH)
    overlays = _overlay_by_name()
    for delegator, spec in policy["delegators"].items():
        if spec.get("deny_self"):
            assert delegator not in spec["allow"]
            allowed = _task_allowlist(overlays[delegator]["permission"])
            assert delegator not in allowed


def test_opencode_task_permissions_match_delegation_policy() -> None:
    policy = _load_json(POLICY_PATH)
    overlays = _overlay_by_name()
    for delegator, spec in policy["delegators"].items():
        entry = overlays[delegator]
        task = entry["permission"]["task"]
        assert isinstance(task, dict)
        assert task.get("*") == spec["task_default"]
        expected = set(spec["allow"])
        actual = _task_allowlist(entry["permission"])
        assert actual == expected, (
            f"{delegator}: task allow mismatch\n"
            f"  missing: {sorted(expected - actual)}\n"
            f"  extra: {sorted(actual - expected)}"
        )


def test_triage_lead_routing_targets_subset_of_task_allowlist() -> None:
    policy = _load_json(POLICY_PATH)
    triage_allow = set(policy["delegators"]["triage-lead"]["allow"])
    missing = TRIAGE_ROUTING_TARGETS - triage_allow
    assert not missing, f"triage-lead routing targets not delegatable: {sorted(missing)}"


def test_triage_lead_body_routes_to_delegatable_agents() -> None:
    text = (AGENTS_DIR / "triage-lead.md").read_text(encoding="utf-8")
    for target in TRIAGE_ROUTING_TARGETS:
        assert target in text, f"triage-lead.md should mention routing target {target!r}"


def test_portable_read_only_agents_use_plan_mode() -> None:
    for name in ("code-reviewer", "security-auditor", "planner", "researcher"):
        block = (AGENTS_DIR / f"{name}.md").read_text(encoding="utf-8").split("---", 2)[1]
        frontmatter = yaml.safe_load(block)
        assert isinstance(frontmatter, dict)
        assert frontmatter.get("permissionMode") == "plan", f"{name} must use permissionMode: plan"