"""Minimal schema validation tests for skills catalog authoring + index (W0 SSOT inversion)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = ROOT / "config" / "schemas"

AUTHORING_SCHEMA = SCHEMAS_DIR / "skills-catalog-authoring.schema.json"
INDEX_SCHEMA = SCHEMAS_DIR / "skills-catalog-index.schema.json"


def _load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def _try_jsonschema():
    try:
        from jsonschema import Draft202012Validator

        return Draft202012Validator
    except Exception:
        return None


def test_authoring_schema_file_exists_and_loads() -> None:
    assert AUTHORING_SCHEMA.exists()
    schema = _load_json(AUTHORING_SCHEMA)
    assert schema["title"] == "SkillsCatalogAuthoring"
    assert "skill_id" in schema["properties"]
    assert "source_kind" in schema["properties"]
    assert "skill_id" not in schema["required"]


def test_index_schema_file_exists_and_loads() -> None:
    assert INDEX_SCHEMA.exists()
    schema = _load_json(INDEX_SCHEMA)
    assert schema["title"] == "SkillsCatalogIndex"
    assert "allSkillIndex" in schema["properties"]
    assert "customSkillIndex" in schema["properties"]
    assert "externalSkillIndex" in schema["properties"]


def test_authoring_minimal_valid_structural() -> None:
    # Structural assert fallback (jsonschema used if available in full run)
    data = {
        "skill_id": "plannotator-review",
        "source_kind": "curated-external",
        "name": "plannotator-review",
        "description": "Review plans with structured critique.",
        "audit_date": "2026-06-23",
        "audited_head": "abc123",
        "pin_policy": "pin where practical",
        "source_list_evidence": "npx skills add owner/repo --list",
        "executable_surface": "No hooks.",
        "allowed_tools": "Read",
        "hook_surface": "none",
        "script_surface": "none",
        "credential_behavior": "No credentials.",
        "network_access": "No network access.",
        "file_access": "Reads requested files.",
        "live_action_risk": "No live actions.",
        "risk_category": "low",
        "dedupe_notes": "No overlap.",
        "unsupported_target_agents": ["grok"],
    }
    schema = _load_json(AUTHORING_SCHEMA)
    # basic required + enum checks manually for structural path
    assert data["source_kind"] in ["custom", "curated-external", "external"]
    for k in schema.get("required", []):
        assert k in data
    # if jsonschema present, also run it
    Validator = _try_jsonschema()
    if Validator:
        v = Validator(schema)
        v.validate(data)  # raises on invalid


def test_index_minimal_valid_structural() -> None:
    row = {
        "name": "example-skill",
        "description": "Example.",
        "sourceKind": "curated-external",
        "sourcePath": "docs/src/authoring/skills/example-skill.mdx",
        "installCommand": "npx skills add owner/repo --skill example-skill",
        "auditDate": "2026-06-23",
        "auditedHead": "abc123",
        "pinPolicy": "pin where practical",
        "sourceListEvidence": "npx skills add owner/repo --list",
        "executableSurface": "No hooks.",
        "allowedTools": "Read",
        "hookSurface": "none",
        "scriptSurface": "none",
        "credentialBehavior": "No credentials.",
        "networkAccess": "No network access.",
        "fileAccess": "Reads requested files.",
        "liveActionRisk": "No live actions.",
        "riskCategory": "low",
        "dedupeNotes": "No overlap.",
        "unsupportedTargetAgents": ["grok"],
    }
    data = {
        "customSkillIndex": [],
        "externalSkillIndex": [row],
        "allSkillIndex": [row],
    }
    schema = _load_json(INDEX_SCHEMA)
    assert isinstance(data["allSkillIndex"], list)
    assert len(data["allSkillIndex"]) > 0
    entry0 = data["allSkillIndex"][0]
    for k in ["name", "description", "sourcePath", "sourceKind"]:
        assert k in entry0
    Validator = _try_jsonschema()
    if Validator:
        v = Validator(schema)
        v.validate(data)


def test_committed_catalog_index_matches_schema() -> None:
    index_path = ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
    if not index_path.exists():
        return
    data = _load_json(index_path)
    schema = _load_json(INDEX_SCHEMA)
    Validator = _try_jsonschema()
    if Validator:
        Validator(schema).validate(data)
