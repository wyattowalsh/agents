from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import ModuleType

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "skills" / "new-project" / "scripts"


def load_script(name: str) -> ModuleType:
    path = SCRIPT_DIR / name
    spec = importlib.util.spec_from_file_location(path.stem.replace("-", "_"), path)
    assert spec is not None
    assert spec.loader is not None

    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(SCRIPT_DIR))
    return module


def test_validate_catalog_accepts_current_catalog() -> None:
    validate_catalog = load_script("validate_catalog.py")

    result = validate_catalog.validate_catalog()

    assert result["ok"] is True
    assert result["errors"] == []
    assert result["capability_count"] > 0
    assert result["preset_count"] > 0


def test_resolve_capabilities_closes_implied_graph_and_honors_without() -> None:
    catalog_utils = load_script("catalog_utils.py")

    result = catalog_utils.resolve_capabilities(["repo.pre-commit"])

    assert result["ok"] is True
    assert "github.actions-ci" in result["capabilities"]
    assert "github.actions-ci" in result["auto_added_capabilities"]

    blocked = catalog_utils.resolve_capabilities(["repo.pre-commit"], ["github.actions-ci"])
    assert blocked["ok"] is False
    assert any("excluded capability: github.actions-ci" in error for error in blocked["errors"])


def test_command_classification_blocks_secret_reads_and_destructive_commands() -> None:
    catalog_utils = load_script("catalog_utils.py")

    assert catalog_utils.classify_command("docker compose --env-file .env.example config") == ["read_only"]
    assert "secret_read" in catalog_utils.classify_command("cat .env.local")
    assert "secret_read" in catalog_utils.classify_command("gh auth token")
    assert "blocked_destructive" in catalog_utils.classify_command("docker compose down -v")
    assert set(catalog_utils.classify_command("npx create-next-app@latest demo")) >= {
        "file_mutation",
        "package_install",
    }


def test_blueprint_and_plan_validation_include_command_safety(tmp_path: Path) -> None:
    blueprint = load_script("blueprint.py")
    validate_plan = load_script("validate_plan.py")

    plan = blueprint.build_blueprint(tmp_path, "minimal", ["repo.pre-commit"], [])

    assert plan["ok"] is True
    assert "github.actions-ci" in plan["auto_added_capabilities"]
    assert "command_categories" in plan
    assert "package-install" in plan["approval_required"]
    assert validate_plan.validate(plan)["ok"] is True

    unsafe_plan = {
        "mode": "plan",
        "preflight": {},
        "commands_to_run": ["cat .env.local"],
        "approval_required": [],
        "files_to_create": [],
        "external_side_effects": [],
    }
    unsafe_result = validate_plan.validate(unsafe_plan)
    assert unsafe_result["ok"] is False
    assert any("secret-like file" in error for error in unsafe_result["errors"])


def test_version_check_resolves_aliases_and_rejects_invalid_packages() -> None:
    version_check = load_script("version_check.py")

    check, warning = version_check.build_check("vercel-ai-sdk", "npm")
    assert warning is None
    assert check is not None
    assert check["package"] == "ai"
    assert check["argv"] == ["npm", "view", "ai", "version"]
    assert check["display"] == "npm view ai version"

    unresolved, unresolved_warning = version_check.build_check("guardrails-ai", "pypi")
    assert unresolved is None
    assert "Verify current package name" in unresolved_warning

    invalid, invalid_warning = version_check.build_check("bad/package", "pypi")
    assert invalid is None
    assert invalid_warning == "bad/package: invalid pypi package name"
