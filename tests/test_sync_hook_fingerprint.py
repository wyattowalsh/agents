"""Regression coverage for hook projection sync skip fingerprints."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from wagents.hooks.registry import (
    content_sha256,
    hook_render_fingerprint,
    record_hook_render_fingerprint,
    should_skip_hook_render,
    sync_hook_projection,
)

if TYPE_CHECKING:
    from pathlib import Path


def _dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def test_hook_render_fingerprint_detects_destination_drift(tmp_path: Path):
    registry_path = tmp_path / "hook-registry.json"
    registry_path.write_text('{"version":1,"hooks":[]}\n', encoding="utf-8")
    cache_path = tmp_path / "cache.json"
    dest_path = tmp_path / "hooks.json"
    dest_path.write_text('{"version":1,"hooks":{}}\n', encoding="utf-8")

    fingerprint = hook_render_fingerprint("cursor", perf_tier="worker", registry_path=registry_path)
    record_hook_render_fingerprint(
        "cursor",
        fingerprint,
        content_sha256=content_sha256(dest_path.read_bytes()),
        cache_path=cache_path,
    )

    assert should_skip_hook_render("cursor", fingerprint, dest_path, cache_path=cache_path)

    dest_path.write_text('{"version":1,"hooks":{"preToolUse":[]}}\n', encoding="utf-8")
    assert not should_skip_hook_render("cursor", fingerprint, dest_path, cache_path=cache_path)


def test_hook_render_fingerprint_ignores_legacy_string_cache(tmp_path: Path):
    registry_path = tmp_path / "hook-registry.json"
    registry_path.write_text('{"version":1,"hooks":[]}\n', encoding="utf-8")
    cache_path = tmp_path / "cache.json"
    dest_path = tmp_path / "hooks.json"
    dest_path.write_text('{"version":1,"hooks":{}}\n', encoding="utf-8")
    cache_path.write_text(json.dumps({"cursor": "old-registry-only-hash"}), encoding="utf-8")

    fingerprint = hook_render_fingerprint("cursor", perf_tier="legacy", registry_path=registry_path)

    assert not should_skip_hook_render("cursor", fingerprint, dest_path, cache_path=cache_path)


def test_sync_hook_projection_skips_only_when_content_matches(tmp_path: Path):
    cache_path = tmp_path / "cache.json"
    dest_path = tmp_path / "policy.json"
    rendered = {"version": 1, "hooks": {"preToolUse": []}}
    _dump_json(dest_path, rendered)
    fingerprint = hook_render_fingerprint("cursor", perf_tier="legacy")
    record_hook_render_fingerprint(
        "cursor",
        fingerprint,
        content_sha256=content_sha256(dest_path.read_bytes()),
        cache_path=cache_path,
    )
    calls: list[str] = []

    def render() -> dict[str, Any]:
        calls.append("render")
        return rendered

    def write(dest: Path, data: Any) -> None:
        calls.append("write")
        _dump_json(dest, data)

    assert sync_hook_projection(
        write,
        harness="cursor",
        dest_path=dest_path,
        render_fn=render,
        perf_tier="legacy",
        apply=True,
        cache_path=cache_path,
    )
    assert calls == []

    dest_path.write_text("{}\n", encoding="utf-8")

    assert not sync_hook_projection(
        write,
        harness="cursor",
        dest_path=dest_path,
        render_fn=render,
        perf_tier="legacy",
        apply=True,
        cache_path=cache_path,
    )
    assert calls == ["render", "write"]
    assert json.loads(dest_path.read_text(encoding="utf-8")) == rendered
