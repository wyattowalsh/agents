from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _module():
    spec = importlib.util.spec_from_file_location(
        "_candidate_docs_assurance",
        ROOT / "scripts" / "run_candidate_docs_assurance.py",
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _configure_commands(module) -> None:
    module.PASS_ONE = (("generate-one",),)
    module.PASS_TWO = (("generate-two",),)
    module.VALIDATIONS = (("validate",),)
    module.EXPECTED_COMMANDS = ("generate-one", "generate-two", "validate")


def _passed(command: str) -> list[dict[str, object]]:
    return [
        {
            "command": command,
            "exit_code": 0,
            "status": "passed",
            "stdout_sha256": "a" * 64,
            "stderr_sha256": "b" * 64,
        }
    ]


def test_snapshot_is_stable_and_detects_generated_changes(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    generated = tmp_path / "docs" / "src" / "generated-site-data.mjs"
    generated.parent.mkdir(parents=True)
    readme = tmp_path / "README.md"
    readme.write_text("one\n", encoding="utf-8")
    generated.write_text("page\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)

    before = module.snapshot()
    assert module.snapshot_digest(before) == module.snapshot_digest(module.snapshot())

    generated.write_text("changed\n", encoding="utf-8")
    assert module.snapshot() != before


def test_run_sequence_stops_after_failure(monkeypatch) -> None:
    module = _module()
    calls: list[tuple[str, ...]] = []

    def fake_run(argv: tuple[str, ...]):
        calls.append(argv)
        return {"status": "failed" if len(calls) == 2 else "passed"}

    monkeypatch.setattr(module, "run_command", fake_run)
    results = module.run_sequence((("one",), ("two",), ("three",)))

    assert len(results) == 2
    assert calls == [("one",), ("two",)]


def test_allowed_write_policy_is_explicit_for_custom_authoring(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    skill = tmp_path / "skills" / "owned" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("skill\n", encoding="utf-8")
    external = tmp_path / "docs" / "src" / "authoring" / "skills" / "external-source.mdx"
    external.parent.mkdir(parents=True)
    external.write_text(
        "---\nsource_kind: curated-external\n---\n{/* GENERATED-AUTHORING: source=skills/fake/SKILL.md */}\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "ROOT", tmp_path)

    custom_paths = module.custom_authoring_paths()
    assert module.is_allowed_generator_write(
        "docs/src/authoring/skills/owned.mdx",
        custom_paths=custom_paths,
    )
    assert not module.is_allowed_generator_write(
        "docs/src/authoring/skills/external-source.mdx",
        custom_paths=custom_paths,
    )
    assert not module.is_allowed_generator_write("docs/src/content/docs/contributing.mdx")


def test_build_evidence_records_allowed_first_pass_and_stable_final_state(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    readme = tmp_path / "README.md"
    readme.write_text("before\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    _configure_commands(module)

    def fake_sequence(commands: tuple[tuple[str, ...], ...]):
        if commands == module.PASS_ONE:
            readme.write_text("generated\n", encoding="utf-8")
            return _passed("generate-one")
        if commands == module.PASS_TWO:
            return _passed("generate-two")
        return _passed("validate")

    monkeypatch.setattr(module, "run_sequence", fake_sequence)
    payload = module.build_evidence()

    assert payload["complete"] is True
    assert payload["first_pass_changed_paths"] == ["README.md"]
    assert payload["changed_between_passes"] == []
    assert payload["validation_writes"] == []
    assert payload["unexpected_writes"] == []
    assert payload["second_pass_digests"] == payload["final_digests"]


def test_build_evidence_rejects_out_of_scope_first_pass_write(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    readme = tmp_path / "README.md"
    config = tmp_path / "config" / "policy.json"
    config.parent.mkdir(parents=True)
    readme.write_text("before\n", encoding="utf-8")
    config.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    _configure_commands(module)

    def fake_sequence(commands: tuple[tuple[str, ...], ...]):
        assert commands == module.PASS_ONE
        config.write_text('{"changed": true}\n', encoding="utf-8")
        return _passed("generate-one")

    monkeypatch.setattr(module, "run_sequence", fake_sequence)
    payload = module.build_evidence()

    assert payload["complete"] is False
    assert payload["generation_status"] == "failed"
    assert payload["unexpected_writes"] == ["config/policy.json"]
    assert len(payload["commands"]) == 1


def test_build_evidence_rejects_protected_hand_maintained_write(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    page = tmp_path / "docs" / "src" / "content" / "docs" / "mcp" / "index.mdx"
    page.parent.mkdir(parents=True)
    page.write_text("{/* HAND-MAINTAINED */}\noriginal\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("readme\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    _configure_commands(module)

    def fake_sequence(commands: tuple[tuple[str, ...], ...]):
        assert commands == module.PASS_ONE
        page.write_text("replaced\n", encoding="utf-8")
        return _passed("generate-one")

    monkeypatch.setattr(module, "run_sequence", fake_sequence)
    payload = module.build_evidence()

    assert payload["complete"] is False
    assert payload["unexpected_writes"] == ["docs/src/content/docs/mcp/index.mdx"]


def test_build_evidence_rejects_validation_write(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    readme = tmp_path / "README.md"
    config = tmp_path / "config.json"
    readme.write_text("before\n", encoding="utf-8")
    config.write_text("before\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    _configure_commands(module)

    def fake_sequence(commands: tuple[tuple[str, ...], ...]):
        if commands == module.PASS_ONE:
            readme.write_text("generated\n", encoding="utf-8")
            return _passed("generate-one")
        if commands == module.PASS_TWO:
            return _passed("generate-two")
        config.write_text("validation mutated input\n", encoding="utf-8")
        return _passed("validate")

    monkeypatch.setattr(module, "run_sequence", fake_sequence)
    payload = module.build_evidence()

    assert payload["complete"] is False
    assert payload["check_status"] == "failed"
    assert payload["validation_writes"] == ["config.json"]


def test_build_evidence_rejects_non_idempotent_second_pass(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    readme = tmp_path / "README.md"
    readme.write_text("before\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    _configure_commands(module)

    def fake_sequence(commands: tuple[tuple[str, ...], ...]):
        if commands == module.PASS_ONE:
            readme.write_text("first\n", encoding="utf-8")
            return _passed("generate-one")
        if commands == module.PASS_TWO:
            readme.write_text("second\n", encoding="utf-8")
            return _passed("generate-two")
        raise AssertionError("validations must not run after a non-idempotent pass")

    monkeypatch.setattr(module, "run_sequence", fake_sequence)
    payload = module.build_evidence()

    assert payload["complete"] is False
    assert payload["idempotence_status"] == "failed"
    assert payload["changed_between_passes"] == ["README.md"]


def test_check_stored_evidence_rejects_malformed_success_claim(monkeypatch, tmp_path: Path) -> None:
    module = _module()
    readme = tmp_path / "README.md"
    readme.write_text("before\n", encoding="utf-8")
    monkeypatch.setattr(module, "ROOT", tmp_path)
    _configure_commands(module)

    def fake_sequence(commands: tuple[tuple[str, ...], ...]):
        if commands == module.PASS_ONE:
            readme.write_text("generated\n", encoding="utf-8")
            return _passed("generate-one")
        if commands == module.PASS_TWO:
            return _passed("generate-two")
        return _passed("validate")

    monkeypatch.setattr(module, "run_sequence", fake_sequence)
    valid = module.build_evidence()
    assert module.check_stored_evidence(valid) == []

    malformed = dict(valid)
    malformed.pop("version")
    malformed.pop("assurance_kind")
    malformed["generation_status"] = "failed"
    malformed["commands"] = []

    errors = module.check_stored_evidence(malformed)

    assert any("wrong version" in error for error in errors)
    assert any("wrong assurance kind" in error for error in errors)
    assert any("generation_status" in error for error in errors)
    assert any("command sequence" in error for error in errors)
