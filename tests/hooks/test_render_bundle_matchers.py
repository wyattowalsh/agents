"""RV-002: bundle-collapsed hook entries must union every member's matcher.

``_synthetic_bundle_hook`` used to take only the first bundle-group member's
matcher, which silently narrowed the collapsed entry whenever a later member
covered additional tool names (for example a shell-only guard bundled with a
guard that also covers file-write tools). ``union_bundle_matchers()`` fixes
this by splitting each member's ``|``-delimited matcher, deduping tokens
case-sensitively in first-seen order, and rejoining them.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from wagents.hooks.render import (
    dedupe_logical_policy_across_events,
    render_codex_hooks,
    render_copilot_hooks,
    render_cursor_hooks,
    union_bundle_matchers,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HOOK_REGISTRY_PATH = REPO_ROOT / "config" / "hook-registry.json"


def _registry() -> dict:
    return json.loads(HOOK_REGISTRY_PATH.read_text(encoding="utf-8"))


def _cursor_bundle_entry(hooks: list[dict], first_policy_id: str) -> dict:
    """Cursor's flat render shape drops ``bundle_group``, so match on the rendered command."""
    for hook in hooks:
        if first_policy_id in str(hook.get("command", "")):
            return hook
    raise AssertionError(f"no collapsed bundle entry found containing {first_policy_id!r} in {hooks!r}")


def test_union_bundle_matchers_dedupes_first_seen_order():
    members = [
        {"matcher": "Bash|bash|run_shell_command|shell|terminal"},
        {"matcher": "Write|Edit|MultiEdit|apply_patch|edit|create|replace|write_file|Bash|bash|run_shell_command"},
    ]
    assert union_bundle_matchers(members) == (
        "Bash|bash|run_shell_command|shell|terminal|Write|Edit|MultiEdit|apply_patch|edit|create|replace|write_file"
    )


def test_union_bundle_matchers_handles_missing_and_empty_matchers():
    assert union_bundle_matchers([{}, {"matcher": ""}]) is None
    assert union_bundle_matchers([{}, {"matcher": "Bash"}]) == "Bash"


def test_union_bundle_matchers_case_sensitive_no_collapse():
    members = [{"matcher": "bash"}, {"matcher": "Bash"}]
    assert union_bundle_matchers(members) == "bash|Bash"


def test_cursor_shell_file_guards_bundle_matcher_covers_shell_and_write_tokens():
    registry = _registry()
    rendered = render_cursor_hooks(registry, perf_tier="bundle")
    assert rendered is not None
    entry = _cursor_bundle_entry(rendered["hooks"]["preToolUse"], "cursor-destructive-shell-guard")
    matcher = entry["matcher"]
    for token in ("Bash", "bash", "run_shell_command", "shell", "terminal"):
        assert token in matcher.split("|"), f"missing shell token {token!r} in {matcher!r}"
    for token in ("Write", "Edit", "MultiEdit", "apply_patch", "create", "replace", "write_file"):
        assert token in matcher.split("|"), f"missing write token {token!r} in {matcher!r}"


def test_codex_shell_file_guards_bundle_matcher_covers_shell_and_write_tokens():
    registry = _registry()
    rendered = render_codex_hooks(registry, repo_root="/repo", perf_tier="bundle")
    groups = rendered["hooks"].get("PreToolUse", [])
    # Codex's nested-group shape stores matcher on the group; find the collapsed bundle group
    # by looking for the union of both shell and write tokens on a single group's matcher.
    covers_both = [
        group
        for group in groups
        if "Bash" in str(group.get("matcher", "")).split("|") and "Write" in str(group.get("matcher", "")).split("|")
    ]
    assert covers_both, f"expected one collapsed PreToolUse group covering both Bash and Write, got {groups!r}"


def test_codex_rendered_matchers_avoid_unsupported_lookaround():
    registry = _registry()
    rendered = render_codex_hooks(registry, repo_root="/repo", perf_tier="legacy")
    matchers = [
        str(group["matcher"])
        for groups in rendered["hooks"].values()
        for group in groups
        if group.get("matcher")
    ]
    unsupported_tokens = ("(?=", "(?!", "(?<=", "(?<!")
    assert matchers
    assert not [
        matcher
        for matcher in matchers
        if any(token in matcher for token in unsupported_tokens)
    ]


def test_codex_renderer_rejects_unsupported_lookaround_matchers():
    registry = {
        "hooks": [
            {
                "id": "bad-codex-matcher",
                "logical_event": "PreToolUse",
                "matcher": "^(?!Bash$).*$",
                "command": "echo bad",
                "harnesses": ["codex"],
            }
        ]
    }
    with pytest.raises(ValueError, match="unsupported look-around"):
        render_codex_hooks(registry, repo_root="/repo")


def test_research_shell_guards_bundle_matcher_covers_shell_and_write_tokens():
    registry = _registry()
    rendered = render_cursor_hooks(registry, perf_tier="bundle")
    assert rendered is not None
    entry = _cursor_bundle_entry(rendered["hooks"]["preToolUse"], "research-readonly-write-guard")
    matcher = entry["matcher"]
    tokens = matcher.split("|")
    for token in ("Write", "Edit", "MultiEdit", "apply_patch", "create", "replace", "write_file", "run_shell_command"):
        assert token in tokens, f"missing write/shell token {token!r} in {matcher!r}"
    for token in ("Bash", "bash"):
        assert token in tokens, f"missing shell token {token!r} in {matcher!r}"


def test_legacy_tier_matcher_stays_per_row_not_unioned():
    """Byte-stability invariant: legacy tier never collapses, so each row keeps its own matcher."""
    registry = _registry()
    rendered = render_cursor_hooks(registry, perf_tier="legacy")
    assert rendered is not None
    matchers = {entry["matcher"] for entry in rendered["hooks"]["preToolUse"] if entry.get("matcher")}
    # The uncollapsed destructive-shell-guard matcher (shell-only) must survive untouched.
    assert "Bash|bash|run_shell_command|shell|terminal" in matchers


def test_worker_tier_matcher_matches_bundle_tier():
    """T-RV-020h: the worker tier's collapsed matcher must equal the bundle tier's."""
    registry = _registry()
    bundle_rendered = render_cursor_hooks(registry, perf_tier="bundle")
    worker_rendered = render_cursor_hooks(registry, perf_tier="worker")
    assert bundle_rendered is not None
    assert worker_rendered is not None
    bundle_entry = _cursor_bundle_entry(bundle_rendered["hooks"]["preToolUse"], "cursor-destructive-shell-guard")
    worker_entry = _cursor_bundle_entry(worker_rendered["hooks"]["preToolUse"], "cursor-destructive-shell-guard")
    assert bundle_entry["matcher"] == worker_entry["matcher"]


def test_bundle_tier_reduces_cursor_pre_tool_use_entry_count():
    """T-042b-g: bundle tier collapses cursor-shell-file-guards into fewer preToolUse rows."""
    registry = _registry()
    legacy = render_cursor_hooks(registry, perf_tier="legacy")
    bundle = render_cursor_hooks(registry, perf_tier="bundle")
    assert legacy is not None
    assert bundle is not None
    assert len(bundle["hooks"]["preToolUse"]) < len(legacy["hooks"]["preToolUse"])


def test_bundle_tier_reduces_codex_pre_tool_use_group_count():
    """T-042b-g: bundle tier collapses codex PreToolUse groups vs legacy fan-out."""
    registry = _registry()
    legacy = render_codex_hooks(registry, repo_root="/repo", perf_tier="legacy")
    bundle = render_codex_hooks(registry, repo_root="/repo", perf_tier="bundle")
    legacy_count = sum(len(groups) for groups in legacy["hooks"].values())
    bundle_count = sum(len(groups) for groups in bundle["hooks"].values())
    assert bundle_count < legacy_count


def test_cursor_event_dedupe_drops_generic_duplicate_only_under_bundle_tier():
    """T-060d: Cursor bundle tier keeps the more-specific native event."""
    hooks = [
        {"id": "generic", "logical_policy": "same-shell-policy", "logical_event": "PreToolUse"},
        {"id": "specific", "logical_policy": "same-shell-policy", "logical_event": "BeforeShellExecution"},
    ]

    assert dedupe_logical_policy_across_events(hooks, "cursor", perf_tier="legacy") == hooks
    deduped = dedupe_logical_policy_across_events(hooks, "cursor", perf_tier="bundle")

    assert [hook["id"] for hook in deduped] == ["specific"]


def test_codex_event_dedupe_is_intentionally_disabled_for_permission_flow():
    """T-060e: Codex PreToolUse and PermissionRequest remain separate gates."""
    hooks = [
        {"id": "pre", "logical_policy": "codex-shell-policy", "logical_event": "PreToolUse"},
        {"id": "permission", "logical_policy": "codex-shell-policy", "logical_event": "PermissionRequest"},
    ]

    assert dedupe_logical_policy_across_events(hooks, "codex", perf_tier="bundle") == hooks


def test_copilot_bundle_tier_collapses_post_edit_quality_shell_scripts():
    """T-080f: Copilot render emits the parallel post-edit quality wrapper."""
    registry = _registry()
    rendered = render_copilot_hooks(registry, repo_root=".", perf_tier="bundle")

    post_tool = rendered["hooks"]["postToolUse"]
    commands = [entry["bash"] for entry in post_tool]

    assert commands.count("./hooks/post-edit-quality.sh") == 1
    assert all("./hooks/auto-format.sh" not in command for command in commands)
    assert all("./hooks/lint-check.sh" not in command for command in commands)
