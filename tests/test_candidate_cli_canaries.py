from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_cli_canaries",
        ROOT / "scripts" / "run_candidate_cli_canaries.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_every_binding_references_a_probe() -> None:
    module = _module()
    assert module.PROBE_BINDINGS
    assert set(module.PROBE_BINDINGS.values()) <= set(module.PROBES)


def test_every_runtime_cli_has_a_semantic_probe() -> None:
    module = _module()
    activation = module.activation_module()
    expected = {
        (url, str(seed["kind"]))
        for url, rows in activation.runtime_specs().items()
        for seed in rows
        if seed.get("kind") in {"cli", "library"}
    }
    assert len([item for item in expected if item[1] == "cli"]) == 30
    assert expected == set(module.PROBE_BINDINGS)


def test_sanitized_env_strips_secret_shaped_names(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    monkeypatch.setenv("EXAMPLE_API_KEY", "do-not-copy")
    monkeypatch.setenv("EXAMPLE_TOKEN", "do-not-copy")
    monkeypatch.setenv("SAFE_VALUE", "kept")

    env = module.sanitized_env(home=tmp_path)

    assert "EXAMPLE_API_KEY" not in env
    assert "EXAMPLE_TOKEN" not in env
    assert env["SAFE_VALUE"] == "kept"
    assert env["HOME"] == str(tmp_path)


def test_receipt_writer_is_deterministic(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    output = tmp_path / "receipts.json"
    monkeypatch.setattr(module, "RECEIPTS", output)
    rows = {
        ("b", "install"): {"artifact_id": "b", "phase": "install"},
        ("a", "behavior"): {"artifact_id": "a", "phase": "behavior"},
    }

    module.write_receipts(rows)

    assert [row["artifact_id"] for row in module.read_receipts().values()] == ["a", "b"]


def test_directory_digest_changes_with_package_content(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "package"
    package.mkdir()
    source = package / "index.js"
    source.write_text("one\n", encoding="utf-8")
    before = module.file_digest([package])
    source.write_text("two\n", encoding="utf-8")
    assert module.file_digest([package]) != before

    dependency = package / "node_modules" / "dependency"
    dependency.mkdir(parents=True)
    dependency_file = dependency / "index.js"
    dependency_file.write_text("one\n", encoding="utf-8")
    without_dependency = module.file_digest([package])
    dependency_file.write_text("two\n", encoding="utf-8")
    assert module.file_digest([package]) == without_dependency


def test_installed_version_reads_matching_npm_manifest(tmp_path: Path) -> None:
    module = _module()
    package = tmp_path / "package"
    package.mkdir()
    (package / "package.json").write_text(
        '{"name":"example-tool","version":"2.0.0"}\n',
        encoding="utf-8",
    )
    seed = {"package_manager": "npm", "package_name": "example-tool"}
    assert module.installed_version(seed, [package]) == "2.0.0"


def test_node_promotion_state_must_prove_exact_rollback(tmp_path: Path, monkeypatch) -> None:
    module = _module()
    state = tmp_path / "state.json"
    state.write_text('{"preimage_digest":"before","rollback_digest":"after"}\n')
    monkeypatch.setattr(
        sys,
        "argv",
        ["run_candidate_cli_canaries.py", "--node-promotion-state", str(state)],
    )
    with pytest.raises(ValueError, match="exact rollback"):
        module.main()


def test_fixture_mcp_server_is_valid_python(tmp_path: Path) -> None:
    module = _module()
    server = tmp_path / "server.py"
    module._write_fixture_mcp_server(server)
    compile(server.read_text(encoding="utf-8"), str(server), "exec")
