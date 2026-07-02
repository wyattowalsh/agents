"""Gate tests for eval-ci-flagship-skills manifest."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from wagents.parsing import parse_frontmatter

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "planning" / "manifests" / "eval-ci-flagship-skills.json"


@pytest.fixture(scope="module")
def manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_manifest_has_expected_shape(manifest: dict) -> None:
    assert manifest["version"] == 1
    assert isinstance(manifest["skills"], list)
    assert len(manifest["skills"]) >= 8
    names = [entry["name"] for entry in manifest["skills"]]
    assert len(names) == len(set(names)), "duplicate flagship skill names"


@pytest.mark.parametrize(
    "entry",
    json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["skills"],
    ids=lambda e: e["name"],
)
def test_flagship_skill_meets_gate(entry: dict) -> None:
    name = entry["name"]
    skill_dir = REPO_ROOT / "skills" / name
    assert skill_dir.is_dir(), f"missing skill directory: skills/{name}"

    skill_md = skill_dir / "SKILL.md"
    assert skill_md.is_file(), f"missing SKILL.md for {name}"
    fm, body = parse_frontmatter(skill_md.read_text(encoding="utf-8"))
    assert fm.get("name") == name
    assert fm.get("description")
    assert body.strip()

    evals_manifest = skill_dir / "evals" / "evals.json"
    assert evals_manifest.is_file(), f"missing evals/evals.json for flagship skill {name}"
    payload = json.loads(evals_manifest.read_text(encoding="utf-8"))
    eval_items = payload.get("evals") or payload.get("cases") or []
    assert len(eval_items) >= 1, f"{name} must have at least one eval case"


def test_flagship_manifest_matches_catalog_index(manifest: dict) -> None:
    index_path = REPO_ROOT / "docs" / "public" / "generated-registries" / "skills-catalog-index.json"
    if not index_path.is_file():
        pytest.skip("skills-catalog-index.json not generated in this checkout")

    index = json.loads(index_path.read_text(encoding="utf-8"))
    custom_names = {row["name"] for row in index.get("customSkillIndex", [])}
    for entry in manifest["skills"]:
        assert entry["name"] in custom_names, f"{entry['name']} missing from customSkillIndex"


def test_sarif_schema_validates_success_log() -> None:
    """Cross-check SARIF emitter against repo schema (W11 gate V-100 helper)."""
    import importlib.util

    schema = json.loads(
        (REPO_ROOT / "config" / "schemas" / "wagents-validate.sarif.schema.json").read_text(encoding="utf-8")
    )
    sarif_path = REPO_ROOT / "scripts" / "validate" / "sarif.py"
    spec = importlib.util.spec_from_file_location("validate_sarif", sarif_path)
    assert spec is not None
    assert spec.loader is not None
    sarif_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(sarif_module)

    payload = sarif_module.build_sarif_log([])
    jsonschema.Draft202012Validator(schema).validate(payload)

    payload_with_errors = sarif_module.build_sarif_log(
        [{"source": "skills/x/SKILL.md", "message": "missing name"}]
    )
    jsonschema.Draft202012Validator(schema).validate(payload_with_errors)
