from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from wagents.candidate_plugin_provenance import (
    PLUGIN_CONTENT_DIGEST_ALGORITHM,
    codex_plugin_live_state,
    load_plugin_provenance_lock,
    plugin_content_sha256,
    verify_upstream_projection,
)


def _entry(*, approved: str, commit: str = "1" * 40, tree: str = "2" * 40) -> dict[str, object]:
    return {
        "plugin_id": "demo@marketplace",
        "registry_id": "candidate-demo-plugin",
        "normalized_url": "https://github.com/example/demo",
        "resolved_version": "1.0.0",
        "audited_source_commit_sha": commit,
        "upstream_subpath": "plugin",
        "upstream_git_tree_oid": tree,
        "source_projection": {"mode": "all", "paths": []},
        "marketplace": "marketplace",
        "marketplace_path": "plugins/demo",
        "marketplace_snapshot_kind": "git-checkout",
        "marketplace_commit_sha": commit,
        "marketplace_git_subpath": "plugin",
        "marketplace_git_tree_oid": tree,
        "approved_content_sha256": approved,
        "digest_algorithm": PLUGIN_CONTENT_DIGEST_ALGORITHM,
        "ignored_dirs": [".git"],
    }


def test_content_digest_is_path_independent_and_includes_runtime_cache(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "SKILL.md").write_text("same\n", encoding="utf-8")
    (second / "SKILL.md").write_text("same\n", encoding="utf-8")

    before = plugin_content_sha256(first)
    assert before == plugin_content_sha256(second)

    cache = first / "__pycache__"
    cache.mkdir()
    (cache / "probe.pyc").write_bytes(b"runtime")
    assert plugin_content_sha256(first) != before


def test_content_digest_rejects_symlinks_instead_of_trusting_target_text(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    outside = tmp_path / "outside"
    outside.write_text("first\n", encoding="utf-8")
    (plugin / "linked").symlink_to(outside)

    with pytest.raises(ValueError, match="contains a symlink"):
        plugin_content_sha256(plugin)


def test_lock_loader_rejects_schema_extension_and_unsafe_version(tmp_path: Path) -> None:
    plugin = tmp_path / "plugin"
    plugin.mkdir()
    approved = plugin_content_sha256(plugin)
    entry = _entry(approved=approved)
    path = tmp_path / "lock.json"

    path.write_text(json.dumps({"version": 1, "plugins": [entry], "unexpected": True}), encoding="utf-8")
    with pytest.raises(ValueError, match="fields drifted"):
        load_plugin_provenance_lock(path)

    entry["resolved_version"] = "../escape"
    path.write_text(json.dumps({"version": 1, "plugins": [entry]}), encoding="utf-8")
    with pytest.raises(ValueError, match="safe path component"):
        load_plugin_provenance_lock(path)


def test_live_state_binds_config_activation_and_locked_cache_path(tmp_path: Path) -> None:
    cache = tmp_path / "cache"
    installed = cache / "marketplace" / "demo" / "1.0.0"
    installed.mkdir(parents=True)
    config = tmp_path / "config.toml"
    config.write_text('[plugins."demo@marketplace"]\nenabled = true\n', encoding="utf-8")
    entry = _entry(approved=plugin_content_sha256(installed))

    state = codex_plugin_live_state(config, cache, entry)

    assert state == {
        "plugin_id": "demo@marketplace",
        "version": "1.0.0",
        "enabled": True,
        "installed": True,
        "installed_path": str(installed),
    }

    config.write_text('[plugins."demo@marketplace"]\nenabled = false\n', encoding="utf-8")
    assert codex_plugin_live_state(config, cache, entry)["enabled"] is False


def test_upstream_projection_reproduces_approved_digest_from_clean_pinned_tree(tmp_path: Path) -> None:
    git = Path("/usr/bin/git")
    if not git.is_file():
        pytest.skip("system Git is unavailable")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    plugin = checkout / "plugin"
    plugin.mkdir()
    (plugin / "SKILL.md").write_text("audited\n", encoding="utf-8")
    subprocess.run([str(git), "-C", str(checkout), "init", "-q"], check=True)
    subprocess.run([str(git), "-C", str(checkout), "add", "plugin"], check=True)
    subprocess.run(
        [
            str(git),
            "-c",
            "user.name=Provenance Test",
            "-c",
            "user.email=provenance@example.invalid",
            "-C",
            str(checkout),
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    commit = subprocess.run(
        [str(git), "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        [str(git), "-C", str(checkout), "rev-parse", "HEAD:plugin"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    entry = _entry(approved=plugin_content_sha256(plugin), commit=commit, tree=tree)

    assert verify_upstream_projection(checkout, entry) == entry["approved_content_sha256"]

    (plugin / "SKILL.md").write_text("tampered\n", encoding="utf-8")
    assert verify_upstream_projection(checkout, entry) == entry["approved_content_sha256"]


def test_upstream_projection_verifies_a_repository_root_tree(tmp_path: Path) -> None:
    git = Path("/usr/bin/git")
    if not git.is_file():
        pytest.skip("system Git is unavailable")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    (checkout / "SKILL.md").write_text("audited\n", encoding="utf-8")
    subprocess.run([str(git), "-C", str(checkout), "init", "-q"], check=True)
    subprocess.run([str(git), "-C", str(checkout), "add", "SKILL.md"], check=True)
    subprocess.run(
        [
            str(git),
            "-c",
            "user.name=Provenance Test",
            "-c",
            "user.email=provenance@example.invalid",
            "-C",
            str(checkout),
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    commit = subprocess.run(
        [str(git), "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        [str(git), "-C", str(checkout), "rev-parse", "HEAD^{tree}"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    entry = _entry(approved=plugin_content_sha256(checkout), commit=commit, tree=tree)
    entry["upstream_subpath"] = "."

    assert verify_upstream_projection(checkout, entry) == entry["approved_content_sha256"]


def test_upstream_projection_rejects_git_symlink_objects(tmp_path: Path) -> None:
    git = Path("/usr/bin/git")
    if not git.is_file():
        pytest.skip("system Git is unavailable")
    checkout = tmp_path / "checkout"
    checkout.mkdir()
    plugin = checkout / "plugin"
    plugin.mkdir()
    (plugin / "target").write_text("audited\n", encoding="utf-8")
    (plugin / "linked").symlink_to("target")
    subprocess.run([str(git), "-C", str(checkout), "init", "-q"], check=True)
    subprocess.run([str(git), "-C", str(checkout), "add", "plugin"], check=True)
    subprocess.run(
        [
            str(git),
            "-c",
            "user.name=Provenance Test",
            "-c",
            "user.email=provenance@example.invalid",
            "-C",
            str(checkout),
            "commit",
            "-qm",
            "fixture",
        ],
        check=True,
    )
    commit = subprocess.run(
        [str(git), "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        [str(git), "-C", str(checkout), "rev-parse", "HEAD:plugin"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    entry = _entry(approved="0" * 64, commit=commit, tree=tree)

    with pytest.raises(ValueError, match="unsupported Git object"):
        verify_upstream_projection(checkout, entry)
