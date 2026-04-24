"""Tests for skills/skill-creator/scripts/package.py — ZIP packaging and portability checks."""

import json
import sys
import zipfile
from pathlib import Path

import pytest

# Insert the package script directory into sys.path so we can import directly.
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "skill-creator" / "scripts"))

from package import (
    ABSOLUTE_PATH_RE,
    check_name_directory_match,
    check_no_absolute_paths,
    check_referenced_files,
    format_table,
    main,
    package_all,
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
            assert "test-pkg/SKILL.md" in names
            assert "test-pkg/manifest.json" in names

    def test_manifest_json_is_valid(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)
        zip_path = Path(result["output_path"])

        with zipfile.ZipFile(zip_path) as zf:
            manifest = json.loads(zf.read("test-pkg/manifest.json"))
            assert manifest["name"] == "test-pkg"
            assert manifest["version"] == "1.0.0"
            assert manifest["packaged_by"] == "package.py"
            assert "created_at" in manifest

    def test_zip_includes_assets_and_extra_top_level_files(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        (skill_dir / "assets").mkdir()
        (skill_dir / "assets" / "logo.txt").write_text("logo")
        (skill_dir / "notes.md").write_text("pack me")
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)
        zip_path = Path(result["output_path"])

        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            assert "test-pkg/assets/logo.txt" in names
            assert "test-pkg/notes.md" in names

    def test_reports_files_excluded_by_default(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        (skill_dir / "reports").mkdir()
        (skill_dir / "reports" / "audit.md").write_text("local report")
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)
        zip_path = Path(result["output_path"])

        assert "reports/audit.md" in result["files_excluded"]
        assert "reports/audit.md" not in result["files_included"]
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            manifest = json.loads(zf.read("test-pkg/manifest.json"))
            assert "test-pkg/reports/audit.md" not in names
            assert "reports/audit.md" not in manifest["files"]

    def test_explicitly_referenced_reports_file_is_included(self, tmp_path: Path):
        skill_md = VALID_SKILL_MD.replace(
            "Body content here.",
            "Use reports/keep.md for the packaged evidence file.",
        )
        skill_dir = _make_skill(tmp_path, skill_md)
        (skill_dir / "reports").mkdir()
        (skill_dir / "reports" / "keep.md").write_text("packaged report")
        (skill_dir / "reports" / "scratch.md").write_text("local scratch report")
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)
        zip_path = Path(result["output_path"])

        assert "reports/keep.md" in result["files_included"]
        assert "reports/scratch.md" in result["files_excluded"]
        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            manifest = json.loads(zf.read("test-pkg/manifest.json"))
            assert "test-pkg/reports/keep.md" in names
            assert "test-pkg/reports/scratch.md" not in names
            assert "reports/keep.md" in manifest["files"]
            assert "reports/scratch.md" not in manifest["files"]


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

    def test_dry_run_reports_excluded_report_files(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path)
        (skill_dir / "reports").mkdir()
        (skill_dir / "reports" / "audit.md").write_text("local report")
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir, dry_run=True)
        table = format_table(result)

        assert "reports/audit.md" in result["files_excluded"]
        assert "reports/audit.md" in table

    def test_package_all_dry_run_manifest_reports_no_emitted_archives(self, tmp_path: Path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _make_skill(skills_dir)
        output_dir = tmp_path / "dist"

        data = package_all(skills_dir, output_dir, dry_run=True)

        assert data["manifest"]["skills"][0]["zip"] is None


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

    def test_dry_run_blocks_on_portability_failures(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path, MINIMAL_SKILL_MD)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir, dry_run=True)

        assert result["blocked"] is True
        assert result["portable"] is False

    def test_packaging_fails_closed_without_force(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path, MINIMAL_SKILL_MD)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir)

        assert result["blocked"] is True
        assert result["output_path"] is not None
        assert not Path(result["output_path"]).exists()
        assert result["errors"]

    def test_force_overrides_portability_failures(self, tmp_path: Path):
        skill_dir = _make_skill(tmp_path, MINIMAL_SKILL_MD)
        output_dir = tmp_path / "dist"

        result = package_skill(skill_dir, output_dir, force=True)

        assert result["blocked"] is False
        assert Path(result["output_path"]).exists()
        assert any("--force" in warning for warning in result["warnings"])

    def test_package_all_manifest_only_lists_emitted_archives(self, tmp_path: Path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        valid_dir = skills_dir / "valid-skill"
        valid_dir.mkdir()
        (valid_dir / "SKILL.md").write_text(
            """\
---
name: valid-skill
description: Valid skill
license: MIT
metadata:
  author: tester
  version: "1.0.0"
---

Body.
""",
            encoding="utf-8",
        )
        invalid_dir = skills_dir / "invalid-skill"
        invalid_dir.mkdir()
        (invalid_dir / "SKILL.md").write_text(
            """\
---
name: invalid-skill
description: Invalid skill
---

Body.
""",
            encoding="utf-8",
        )
        output_dir = tmp_path / "dist"

        data = package_all(skills_dir, output_dir, dry_run=False, force=False)
        manifest = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
        results = {result["skill"]: result for result in data["results"]}
        manifest_entries = {entry["name"]: entry for entry in manifest["skills"]}

        assert results["invalid-skill"]["blocked"] is True
        assert results["valid-skill"]["blocked"] is False
        assert (output_dir / "valid-skill-v1.0.0.skill.zip").exists()
        assert not (output_dir / "invalid-skill-v0.0.0.skill.zip").exists()
        assert manifest_entries["valid-skill"]["zip"] == "valid-skill-v1.0.0.skill.zip"
        assert manifest_entries["invalid-skill"]["zip"] is None

    def test_main_exits_nonzero_when_package_all_has_blocked_results(self, monkeypatch, tmp_path: Path):
        skills_dir = tmp_path / "skills"
        skills_dir.mkdir()
        _make_skill(skills_dir)
        output_dir = tmp_path / "dist"
        data = package_all(skills_dir, output_dir, dry_run=False)
        blocked_result = {
            "skill": "blocked-skill",
            "version": "0.0.0",
            "output_path": str(output_dir / "blocked-skill-v0.0.0.skill.zip"),
            "files_included": [],
            "files_excluded": [],
            "portability_checks": [],
            "portable": False,
            "blocked": True,
            "warnings": [],
            "errors": ["blocked"],
        }
        data["results"].append(blocked_result)
        data["manifest"]["skills"].append(
            {
                "name": "blocked-skill",
                "version": "0.0.0",
                "description": "Blocked skill",
                "zip": None,
            }
        )

        monkeypatch.setattr("package.package_all", lambda *args, **kwargs: data)
        monkeypatch.setattr(sys, "argv", ["package.py", "--all"])

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1


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
    def test_detects_missing_packaged_resource(self, tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "references").mkdir()
        body = "See scripts/helper.py and references/nonexistent.md for details."

        result = check_referenced_files(skill_dir, body)
        assert not result["passed"]
        assert "nonexistent.md" in result["details"]
        assert "scripts/helper.py" in result["details"]

    def test_passes_with_existing_referenced_resources(self, tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        ref_dir = skill_dir / "references"
        ref_dir.mkdir()
        (ref_dir / "guide.md").write_text("# Guide\n")
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir()
        (scripts_dir / "helper.py").write_text("print('ok')\n")
        assets_dir = skill_dir / "assets"
        assets_dir.mkdir()
        (assets_dir / "logo.svg").write_text("<svg />\n")
        body = (
            "See skills/my-skill/references/guide.md, scripts/helper.py, "
            "assets/logo.svg, and reports/run.md for details."
        )
        reports_dir = skill_dir / "reports"
        reports_dir.mkdir()
        (reports_dir / "run.md").write_text("report\n")

        result = check_referenced_files(skill_dir, body)
        assert result["passed"]

    def test_passes_with_no_references(self, tmp_path: Path):
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        body = "No reference mentions at all."

        result = check_referenced_files(skill_dir, body)
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
