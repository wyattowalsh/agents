"""Contract tests for .pre-commit-config.yaml hook inventory."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"

REQUIRED_HOOK_IDS = (
    "ruff",
    "ruff-format",
    "ty",
    "wagents-validate",
    "apm-materialize-check",
    "apm-doctor",
    "openspec-validate",
    "catalog-index-check",
    "readme-check",
    "docs-generate-check",
    "docs-compose-check",
    "sync-stack-check",
    "actionlint",
)


def _load_hooks() -> list[dict]:
    data = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
    hooks: list[dict] = []
    for repo in data.get("repos", []):
        hooks.extend(repo.get("hooks", []))
    return hooks


def test_precommit_config_exists() -> None:
    assert PRE_COMMIT_CONFIG.is_file()


def test_required_hooks_present() -> None:
    hooks = _load_hooks()
    hook_ids = {hook["id"] for hook in hooks}
    missing = [hook_id for hook_id in REQUIRED_HOOK_IDS if hook_id not in hook_ids]
    assert not missing, f"missing pre-commit hooks: {missing}"


def test_local_hooks_use_uv_or_system_language() -> None:
    hooks = _load_hooks()
    for hook in hooks:
        assert hook.get("language") in {"system", "python", "node"}, hook["id"]
        entry = hook.get("entry", "")
        if hook["id"] in {"ruff", "ruff-format", "ty", "wagents-validate"}:
            assert entry.startswith("uv run"), f"{hook['id']} should run via uv"


def test_wagents_validate_scoped_to_skills_and_agents() -> None:
    hooks = {hook["id"]: hook for hook in _load_hooks()}
    validate_hook = hooks["wagents-validate"]
    assert validate_hook.get("pass_filenames") is False
    assert "skills/" in validate_hook.get("files", "")
