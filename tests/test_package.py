"""Tests for skills/skill-creator/scripts/package.py — ZIP packaging and portability checks."""

import json
import sys
import zipfile
from pathlib import Path

# Insert the package script directory into sys.path so we can import directly.
sys.path.insert(
    0, str(Path(__file__).parent.parent / "skills" / "skill-creator" / "scripts")
)

from package import (
    ABSOLUTE_PATH_RE,
    check_name_directory_match,
    check_no_absolute_paths,
    check_reference_files,
    package_skill,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

VALID_SKILL_MD = """\
---
name: test-pkg
description: A test skill for packaging
license: MIT
metadata:
  author: tester
  version: "1.0.0"
---

# Test Pkg

Body content here.
"""

MINIMAL_SKILL_MD = """\
---
name: test-pkg
description: A minimal skill
---

Body only.
"""


def _make_skill(tmp_path: Path, content: str = VALID_SKILL_MD) -> Path:
    """Create a minimal skill directory and return its path."""
    skill_dir = tmp_path / "test-pkg"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(content)
    return skill_dir


# ---------------------------------------------------------------------------
# ZIP validity
# ---------------------------------------------------------------------------


class TestZipValidity:
    def test_package_creates_valid_zip(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)

        assert not result["errors"]
        zip_path = Path(result["output_path"])
        assert zip_path.exists()
        assert zip_path.suffix == ".zip"
        assert zipfile.is_zipfile(zip_path)

    def test_zip_contains_expected_files(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)
        zip_path = Path(result["output_path"])

        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            assert "SKILL.md" in names
            assert "manifest.json" in names

    def test_manifest_json_is_valid(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)
        zip_path = Path(result["output_path"])

        with zipfile.ZipFile(zip_path) as zf:
            manifest = json.loads(zf.read("manifest.json"))
            assert manifest["name"] == "test-pkg"
            assert manifest["version"] == "1.0.0"
            assert manifest["packaged_by"] == "package.py"
            assert "created_at" in manifest


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_does_not_create_zip(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir, dry_run=True)

        assert result["output_path"] is not None
        assert not Path(result["output_path"]).exists()
        assert not output_dir.exists()

    def test_dry_run_returns_portability_checks(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir, dry_run=True)

        assert len(result["portability_checks"]) > 0
        assert result["files_included"]


# ---------------------------------------------------------------------------
# Missing fields
# ---------------------------------------------------------------------------


class TestMissingFields:
    def test_missing_license_author_version_warns(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path, MINIMAL_SKILL_MD)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir, dry_run=True)

        check_names = {c["check"] for c in result["portability_checks"] if not c["passed"]}
        assert "frontmatter_license" in check_names
        assert "frontmatter_author" in check_names
        assert "frontmatter_version" in check_names

    def test_warnings_populated_for_missing_fields(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path, MINIMAL_SKILL_MD)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir, dry_run=True)

        assert len(result["warnings"]) >= 3


# ---------------------------------------------------------------------------
# Absolute path detection
# ---------------------------------------------------------------------------


class TestAbsolutePaths:
    def test_regex_detects_standalone_paths(self):
        """Standalone absolute paths should be matched."""
        for case in ["/Users/alice", "/home/bob", "/tmp/foo", "/var/log", "/usr/bin"]:
            assert ABSOLUTE_PATH_RE.search(case), f"Expected match for {case}"

    def test_regex_detects_path_preceded_by_word_char(self):
        """Paths preceded by word chars should also match."""
        for case in ["x/Users/alice", "see/home/bob"]:
            assert ABSOLUTE_PATH_RE.search(case), f"Expected match for {case}"

    def test_check_flags_body_with_absolute_paths(self):
        body = "Look at /Users/alice/projects/foo for details."
        result = check_no_absolute_paths(body)
        assert not result["passed"]

    def test_passes_clean_body(self):
        body = "Use relative paths like ./config or $HOME/.config"
        result = check_no_absolute_paths(body)
        assert result["passed"]

    def test_passes_body_without_paths(self):
        body = "Just a normal skill description with no paths."
        result = check_no_absolute_paths(body)
        assert result["passed"]

    def test_url_scheme_paths_not_matched(self):
        """Paths directly after :// (URL scheme) should not be matched."""
        body = "Visit https://usr/local/bin for details."
        result = check_no_absolute_paths(body)
        assert result["passed"]


# ---------------------------------------------------------------------------
# Broken reference detection
# ---------------------------------------------------------------------------


class TestBrokenRefs:
    def test_detects_missing_reference(self, tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "references").mkdir()
        body = "See references/nonexistent.md for details."

        result = check_reference_files(skill_dir, body)
        assert not result["passed"]
        assert "nonexistent.md" in result["details"]

    def test_passes_with_existing_reference(self, tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        ref_dir = skill_dir / "references"
        ref_dir.mkdir()
        (ref_dir / "guide.md").write_text("# Guide\n")
        body = "See references/guide.md for details."

        result = check_reference_files(skill_dir, body)
        assert result["passed"]

    def test_passes_with_no_references(self, tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        body = "No reference mentions at all."

        result = check_reference_files(skill_dir, body)
        assert result["passed"]


# ---------------------------------------------------------------------------
# Name / directory match
# ---------------------------------------------------------------------------


class TestNameDirectoryMatch:
    def test_matching_name_passes(self):
        fm = {"name": "my-skill"}
        result = check_name_directory_match(fm, "my-skill")
        assert result["passed"]

    def test_mismatched_name_fails(self):
        fm = {"name": "other-name"}
        result = check_name_directory_match(fm, "my-skill")
        assert not result["passed"]
        assert "Mismatch" in result["details"]

    def test_missing_name_fails(self):
        fm = {}
        result = check_name_directory_match(fm, "my-skill")
        assert not result["passed"]
