"""Tests for wagents.mcp_shared.read_only_paths — allowlist guard for MCP servers."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from wagents.mcp_shared.read_only_paths import (
    PathNotAllowedError,
    is_read_only_path_allowed,
    read_text_within_allowlist,
    resolve_read_only_path,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def fake_repo(tmp_path: Path) -> Path:
    (tmp_path / "skills" / "review").mkdir(parents=True)
    (tmp_path / "skills" / "review" / "SKILL.md").write_text("---\nname: review\n---\nbody", encoding="utf-8")
    (tmp_path / "secrets").mkdir()
    (tmp_path / "secrets" / "token.txt").write_text("shh", encoding="utf-8")
    (tmp_path / "README.md").write_text("# readme", encoding="utf-8")
    return tmp_path


def test_resolve_allows_prefixed_path(fake_repo: Path) -> None:
    resolved = resolve_read_only_path("skills/review/SKILL.md", repo_root=fake_repo)
    assert resolved == (fake_repo / "skills" / "review" / "SKILL.md").resolve()


def test_resolve_allows_exact_file_prefix(fake_repo: Path) -> None:
    resolved = resolve_read_only_path("README.md", repo_root=fake_repo)
    assert resolved == (fake_repo / "README.md").resolve()


def test_resolve_rejects_path_outside_allowlist(fake_repo: Path) -> None:
    with pytest.raises(PathNotAllowedError):
        resolve_read_only_path("secrets/token.txt", repo_root=fake_repo)


def test_resolve_rejects_absolute_path(fake_repo: Path) -> None:
    with pytest.raises(PathNotAllowedError):
        resolve_read_only_path("/etc/passwd", repo_root=fake_repo)


@pytest.mark.parametrize(
    "traversal",
    [
        "skills/../secrets/token.txt",
        "../outside.txt",
        "skills/review/../../secrets/token.txt",
    ],
)
def test_resolve_rejects_traversal(fake_repo: Path, traversal: str) -> None:
    with pytest.raises(PathNotAllowedError):
        resolve_read_only_path(traversal, repo_root=fake_repo)


def test_resolve_rejects_empty_or_whitespace(fake_repo: Path) -> None:
    with pytest.raises(PathNotAllowedError):
        resolve_read_only_path("", repo_root=fake_repo)
    with pytest.raises(PathNotAllowedError):
        resolve_read_only_path("  skills/review/SKILL.md  ", repo_root=fake_repo)


def test_is_read_only_path_allowed_matches_resolve(fake_repo: Path) -> None:
    assert is_read_only_path_allowed("skills/review/SKILL.md", repo_root=fake_repo) is True
    assert is_read_only_path_allowed("secrets/token.txt", repo_root=fake_repo) is False
    assert is_read_only_path_allowed("../escape.txt", repo_root=fake_repo) is False


def test_custom_allowed_prefixes_override_default(fake_repo: Path) -> None:
    assert is_read_only_path_allowed("secrets/token.txt", allowed_prefixes=("secrets",), repo_root=fake_repo) is True
    assert (
        is_read_only_path_allowed("skills/review/SKILL.md", allowed_prefixes=("secrets",), repo_root=fake_repo)
        is False
    )


@pytest.mark.parametrize(
    "rel",
    [
        "mcp/secrets/token.env",
        "mcp/servers/local/config.json",
        "mcp/notes/private.md",
        "mcp/archives/old.zip",
        "mcp/cache/tmp.bin",
    ],
)
def test_resolve_rejects_denied_mcp_local_subdirs(fake_repo: Path, rel: str) -> None:
    parts = rel.split("/")
    target = fake_repo
    for part in parts[:-1]:
        target = target / part
        target.mkdir(parents=True, exist_ok=True)
    (fake_repo.joinpath(*parts)).write_text("x", encoding="utf-8")
    with pytest.raises(PathNotAllowedError):
        resolve_read_only_path(rel, repo_root=fake_repo)


def test_resolve_allows_first_party_mcp_server_path(fake_repo: Path) -> None:
    path = fake_repo / "mcp" / "source-url-health" / "server.py"
    path.parent.mkdir(parents=True)
    path.write_text("# ok", encoding="utf-8")
    resolved = resolve_read_only_path("mcp/source-url-health/server.py", repo_root=fake_repo)
    assert resolved == path.resolve()


def test_read_text_within_allowlist_reads_content(fake_repo: Path) -> None:
    content = read_text_within_allowlist("skills/review/SKILL.md", repo_root=fake_repo)
    assert "name: review" in content


def test_read_text_within_allowlist_rejects_disallowed(fake_repo: Path) -> None:
    with pytest.raises(PathNotAllowedError):
        read_text_within_allowlist("secrets/token.txt", repo_root=fake_repo)


def test_read_text_within_allowlist_missing_file(fake_repo: Path) -> None:
    with pytest.raises(FileNotFoundError):
        read_text_within_allowlist("skills/missing.md", repo_root=fake_repo)


def test_read_text_within_allowlist_rejects_directory(fake_repo: Path) -> None:
    with pytest.raises(IsADirectoryError):
        read_text_within_allowlist("skills/review", repo_root=fake_repo)


def test_read_text_within_allowlist_enforces_max_bytes(fake_repo: Path) -> None:
    big = fake_repo / "skills" / "big.md"
    big.write_text("x" * 100, encoding="utf-8")
    with pytest.raises(ValueError, match="exceeds max_bytes"):
        read_text_within_allowlist("skills/big.md", repo_root=fake_repo, max_bytes=10)
