"""Behavioral checks for the narrow host-panel plugin exporter."""

from __future__ import annotations

import importlib.util
import json
import os
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("build_host_panel_plugin", ROOT / "scripts/build_host_panel_plugin.py")
assert SPEC is not None
assert SPEC.loader is not None
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


@pytest.fixture
def source(tmp_path: Path) -> Path:
    root = tmp_path / "source"
    template = root / "config/plugins/host-panel.json"
    template.parent.mkdir(parents=True)
    template.write_bytes((ROOT / "config/plugins/host-panel.json").read_bytes())
    skill = root / "skills/host-panel"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_bytes(
        b"---\nname: host-panel\ndescription: Fixture panel\n---\n\n# Panel\n\n"
        b"Read [methods](references/methods.md#principles).\n"
    )
    (skill / "references/methods.md").write_bytes(
        b"# Principles\r\n\r\n[Back](../SKILL.md) and [external](https://example.com/paper).\r\n"
    )
    return root


def test_build_preserves_canonical_bytes_and_excludes_unrelated_sources(source: Path, tmp_path: Path) -> None:
    skill = source / "skills/host-panel"
    for path in (
        skill / "scripts/run.py",
        skill / "evals/evals.json",
        source / "mcp.json",
        source / "skills/other/SKILL.md",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("do not include\n")
    template = source / "config/plugins/host-panel.json"
    original_template = template.read_bytes()
    original_skill_files = {
        path.relative_to(source).as_posix(): path.read_bytes()
        for path in (skill / "SKILL.md", skill / "references/methods.md")
    }
    output = tmp_path / "panel.zip"

    report = builder.build_plugin(source, output, "0.1.0")

    with zipfile.ZipFile(output) as archive:
        assert archive.namelist() == [
            "plugin.json",
            "skills/host-panel/SKILL.md",
            "skills/host-panel/references/methods.md",
        ]
        for name in archive.namelist()[1:]:
            assert archive.read(name) == original_skill_files[name]
            assert (source / name).read_bytes() == original_skill_files[name]
        manifest = json.loads(archive.read("plugin.json"))
        assert manifest["name"] == "host-panel"
        assert manifest["version"] == "0.1.0"
        assert "mcpServers" not in manifest
        assert "dependencies" not in manifest
    assert template.read_bytes() == original_template
    assert "version" not in json.loads(original_template)
    assert report["files"] == 3


def test_repeated_builds_are_byte_identical_despite_source_mtime_changes(source: Path, tmp_path: Path) -> None:
    first, second = tmp_path / "one.zip", tmp_path / "two.zip"
    report_one = builder.build_plugin(source, first, "0.1.0-rc.1+build.7")
    for path in source.rglob("*"):
        if path.is_file():
            os.utime(path, (1_700_000_000, 1_700_000_000))
    report_two = builder.build_plugin(source, second, "0.1.0-rc.1+build.7")
    assert first.read_bytes() == second.read_bytes()
    assert report_one["archive_sha256"] == report_two["archive_sha256"]
    assert report_one["source_sha256"] == report_two["source_sha256"]


@pytest.mark.parametrize(
    "version", ["", "latest", "v0.1.0", "01.1.0", "1.2", "1.2.3-01", "1.2.3-rc..1", "../1.2.3", "1.2.3+foo..bar"]
)
def test_invalid_versions_do_not_create_output(source: Path, tmp_path: Path, version: str) -> None:
    output = tmp_path / "bad.zip"
    with pytest.raises(builder.BuildError, match=r"version|identifier"):
        builder.build_plugin(source, output, version)
    assert not output.exists()


def test_existing_output_is_preserved(source: Path, tmp_path: Path) -> None:
    output = tmp_path / "existing.zip"
    output.write_bytes(b"existing output")
    with pytest.raises(builder.BuildError, match="overwrite"):
        builder.build_plugin(source, output, "0.1.0")
    assert output.read_bytes() == b"existing output"


def test_output_inside_source_is_rejected(source: Path) -> None:
    output = source / "dist/panel.zip"
    with pytest.raises(builder.BuildError, match="outside the source"):
        builder.build_plugin(source, output, "0.1.0")
    assert not output.parent.exists()


@pytest.mark.parametrize(
    "destination",
    [
        "references/missing.md",
        "../other/SKILL.md",
        "/etc/passwd",
        "references/%2e%2e/%2e%2e/secret.md",
        "file:///tmp/secret.md",
        "file://server/secret.md",
    ],
)
def test_missing_or_escaping_markdown_links_fail(source: Path, tmp_path: Path, destination: str) -> None:
    skill = source / "skills/host-panel/SKILL.md"
    with skill.open("a") as handle:
        handle.write(f"\n[invalid]({destination})\n")
    with pytest.raises(builder.BuildError, match="link"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")


def test_reference_style_links_are_checked(source: Path, tmp_path: Path) -> None:
    skill = source / "skills/host-panel/SKILL.md"
    with skill.open("a") as handle:
        handle.write("\n[missing]: references/absent.md#anchor\n")
    with pytest.raises(builder.BuildError, match="link"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")


@pytest.mark.parametrize(
    "relative",
    ["skills/host-panel/SKILL.md", "skills/host-panel/references/methods.md", "config/plugins/host-panel.json"],
)
def test_symlink_sources_are_rejected(source: Path, tmp_path: Path, relative: str) -> None:
    path = source / relative
    target = tmp_path / "outside"
    target.write_bytes(path.read_bytes())
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(builder.BuildError, match="symbolic"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")


def test_symlink_reference_directory_is_rejected(source: Path, tmp_path: Path) -> None:
    references = source / "skills/host-panel/references"
    target = tmp_path / "outside"
    references.rename(target)
    references.symlink_to(target, target_is_directory=True)
    with pytest.raises(builder.BuildError, match="symbolic"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")


def test_symlink_source_ancestor_is_rejected(source: Path, tmp_path: Path) -> None:
    alias = tmp_path / "alias"
    alias.symlink_to(tmp_path, target_is_directory=True)
    with pytest.raises(builder.BuildError, match="symbolic"):
        builder.build_plugin(alias / source.name, tmp_path / "bad.zip", "0.1.0")


def test_unsafe_archive_filename_is_rejected(source: Path, tmp_path: Path) -> None:
    (source / "skills/host-panel/references/..\\escape.md").write_text("unsafe name")
    with pytest.raises(builder.BuildError, match="filename"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")


def test_symlink_output_parent_is_rejected(source: Path, tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises(builder.BuildError, match="symbolic"):
        builder.build_plugin(source, alias / "bad.zip", "0.1.0")
    assert not (actual / "bad.zip").exists()


@pytest.mark.parametrize(
    ("field", "value"), [("name", "../bad"), ("version", "1.0.0"), ("dependencies", {}), ("policy", {})]
)
def test_invalid_or_overbroad_manifest_is_rejected(source: Path, tmp_path: Path, field: str, value: object) -> None:
    path = source / "config/plugins/host-panel.json"
    manifest = json.loads(path.read_bytes())
    manifest[field] = value
    path.write_text(json.dumps(manifest))
    with pytest.raises(builder.BuildError, match="manifest"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")


def test_overlong_short_description_is_rejected(source: Path, tmp_path: Path) -> None:
    path = source / "config/plugins/host-panel.json"
    manifest = json.loads(path.read_bytes())
    manifest["extensions"]["com.openai"]["interface"]["shortDescription"] = "x" * 31
    path.write_text(json.dumps(manifest))
    with pytest.raises(builder.BuildError, match="shortDescription"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")


def test_wrong_canonical_skill_name_is_rejected(source: Path, tmp_path: Path) -> None:
    path = source / "skills/host-panel/SKILL.md"
    path.write_text(path.read_text().replace("name: host-panel", "name: other-panel"))
    with pytest.raises(builder.BuildError, match="frontmatter"):
        builder.build_plugin(source, tmp_path / "bad.zip", "0.1.0")
