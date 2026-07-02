"""Bundle dispatch contract tests for ``wagents.hooks.bundle`` and CLI."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any, ClassVar, cast

from wagents.hooks.bundle import run_bundle

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_PATH = REPO_ROOT / "hooks" / "wagents-hook.py"
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures" / "hooks"


def _load_hook_module():
    spec = importlib.util.spec_from_file_location("wagents_hook_bundle_tests", HOOK_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


wagents_hook = _load_hook_module()


class CaptureStream:
    def __init__(self) -> None:
        self.value = ""

    def write(self, text: str) -> None:
        self.value += text

    def flush(self) -> None:
        pass


def _run_bundle(monkeypatch, fixture_name: str, policy_ids: list[str], harness: str = "cursor") -> tuple[int, str]:
    payload = json.loads((FIXTURES_DIR / fixture_name).read_text(encoding="utf-8"))
    monkeypatch.setattr(sys, "stdin", type("In", (), {"read": lambda self: json.dumps(payload)})())
    stdout = CaptureStream()
    monkeypatch.setattr(sys, "stdout", stdout)
    monkeypatch.setattr(sys, "stderr", CaptureStream())
    code = wagents_hook.main(
        [
            "--bundle",
            ",".join(policy_ids),
            "--harness",
            harness,
            "--bundle-mode",
            "enforce-chain",
        ]
    )
    return code, stdout.value


def _read_ledger_records(home: Path, harness_home: str) -> list[dict[str, Any]]:
    [ledger] = (home / harness_home / "research" / "hook-ledger").glob("*.jsonl")
    return [json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines()]


def test_bundle_cli_denies_destructive_shell_first_in_chain(monkeypatch):
    code, stdout = _run_bundle(
        monkeypatch,
        "cursor-bash-destructive.json",
        ["cursor-destructive-shell-guard", "cursor-protected-file-guard"],
    )
    payload = json.loads(stdout)
    assert code == 0
    assert payload["permission"] == "deny"


def test_bundle_cli_allows_benign_shell(monkeypatch):
    code, stdout = _run_bundle(
        monkeypatch,
        "cursor-bash-benign.json",
        ["cursor-destructive-shell-guard", "cursor-protected-file-guard"],
    )
    assert code == 0
    if stdout.strip():
        assert json.loads(stdout).get("permission") == "allow"


def test_bundle_cli_records_implicit_allow_decisions(monkeypatch, tmp_path):
    monkeypatch.setattr(wagents_hook.Path, "home", lambda: tmp_path)
    monkeypatch.setenv(wagents_hook.AUDIT_SAMPLE_ENV, "1")

    code, stdout = _run_bundle(
        monkeypatch,
        "cursor-bash-benign.json",
        ["cursor-destructive-shell-guard", "cursor-protected-file-guard"],
    )

    records = _read_ledger_records(tmp_path, ".cursor")
    decisions = {(record["policy"], record["decision"]) for record in records}
    assert code == 0
    if stdout.strip():
        assert json.loads(stdout).get("permission") == "allow"
    assert decisions == {
        ("cursor-destructive-shell-guard", "allow"),
        ("cursor-protected-file-guard", "allow"),
    }


def test_run_bundle_module_short_circuits_on_first_deny():
    emitted: dict[str, object] = {}

    class FakeDispatcher:
        POLICIES: ClassVar[dict[str, Any]] = {
            "deny-policy": lambda payload: FakeDispatcher._deny(payload),
            "allow-policy": lambda payload: 0,
        }
        ENFORCE_POLICY_IDS = frozenset({"deny-policy", "allow-policy"})
        CURSOR_FAIL_CLOSED_ALLOW_POLICIES: frozenset[str] = frozenset()
        _STDOUT_EMITTED = False

        @staticmethod
        def _deny(payload):
            FakeDispatcher._STDOUT_EMITTED = True
            return FakeDispatcher._emit_json({"permission": "deny", "reason": "blocked"})

        @staticmethod
        def _emit_json(data):
            emitted.update(data)
            return 0

        @staticmethod
        def _record_decision(payload, policy_id, decision, reason=""):
            return 0

        @staticmethod
        def _additional_context(payload, message, policy_id="..."):
            return 0

    dispatcher = FakeDispatcher()
    code = run_bundle(
        ["deny-policy", "allow-policy"],
        "cursor",
        {"event": "PreToolUse"},
        dispatcher=cast("Any", dispatcher),
    )
    assert code == 0
    assert emitted == {"permission": "deny", "reason": "blocked"}


def test_run_bundle_module_does_not_record_implicit_allow_for_evidence_ledger():
    decisions: list[tuple[str, str]] = []

    class FakeDispatcher:
        POLICIES: ClassVar[dict[str, Any]] = {"research-evidence-ledger": lambda payload: 0}
        ENFORCE_POLICY_IDS: frozenset[str] = frozenset()
        CURSOR_FAIL_CLOSED_ALLOW_POLICIES: frozenset[str] = frozenset()
        _STDOUT_EMITTED = False

        @staticmethod
        def _emit_json(data):
            return 0

        @staticmethod
        def _record_decision(payload, policy_id, decision, reason=""):
            decisions.append((policy_id, decision))
            return 0

        @staticmethod
        def _deny(payload, reason, policy_id="policy-deny"):
            return 0

        @staticmethod
        def _additional_context(payload, message, policy_id="..."):
            return 0

    code = run_bundle(
        ["research-evidence-ledger"],
        "codex",
        {"event": "AfterTool"},
        dispatcher=cast("Any", FakeDispatcher()),
    )

    assert code == 0
    assert decisions == []


def test_legacy_tier_render_matches_uncollapsed_cursor_pre_tool_use_count():
    from wagents.hooks.render import render_cursor_hooks

    registry = json.loads((REPO_ROOT / "config" / "hook-registry.json").read_text(encoding="utf-8"))
    legacy = render_cursor_hooks(registry, perf_tier="legacy")
    bundle = render_cursor_hooks(registry, perf_tier="bundle")
    assert legacy is not None
    assert bundle is not None
    assert len(legacy["hooks"]["preToolUse"]) > len(bundle["hooks"]["preToolUse"])


def test_bundle_timeout_skip_fail_closed_emits_deny(monkeypatch):
    """T-031b: enforce-tier policies skipped for exhausted bundle budget must deny with exit 0."""
    emitted: dict[str, object] = {}

    class FakeDispatcher:
        POLICIES: ClassVar[dict[str, Any]] = {
            "fast-allow": lambda payload: 0,
            "slow-enforce": lambda payload: 0,
        }
        ENFORCE_POLICY_IDS = frozenset({"slow-enforce"})
        CURSOR_FAIL_CLOSED_ALLOW_POLICIES: frozenset[str] = frozenset()

        @staticmethod
        def _deny(payload, reason, policy_id="policy-deny"):
            emitted.update({"permission": "deny", "reason": reason, "policy_id": policy_id})
            return 0

        @staticmethod
        def _record_decision(payload, policy_id, decision, reason=""):
            return 0

        @staticmethod
        def _emit_json(data):
            emitted.update(data)
            return 0

        @staticmethod
        def _additional_context(payload, message, policy_id="..."):
            return 0

    import wagents.hooks.bundle as bundle_mod

    times = iter([0.0, 0.0, 1000.0])
    monkeypatch.setattr(bundle_mod.time, "monotonic", lambda: next(times))

    code = run_bundle(
        ["fast-allow", "slow-enforce"],
        "cursor",
        {"event": "PreToolUse"},
        timeout_seconds=1.0,
        dispatcher=cast("Any", FakeDispatcher()),
    )
    assert code == 0
    assert emitted.get("permission") == "deny"
    assert "bundle timeout" in str(emitted.get("reason", "")).lower()


def test_research_stop_verifier_runs_in_process_inside_bundle(monkeypatch):
    """T-080d: bundled research-stop-verifier uses in-process POLICIES dispatch (no subprocess)."""
    calls: list[str] = []

    def _spy(payload):
        calls.append("research-stop-verifier")
        return 0

    monkeypatch.setitem(wagents_hook.POLICIES, "research-stop-verifier", _spy)
    code = run_bundle(
        ["research-stop-verifier"],
        "codex",
        {"event": "Stop", "session_id": "bundle-stop"},
        dispatcher=wagents_hook,
    )
    assert code == 0
    assert calls == ["research-stop-verifier"]
