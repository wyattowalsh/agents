#!/usr/bin/env python3
"""Package skills into portable ZIP files for Claude Code Desktop import.

Runs portability checks, generates a manifest.json, and creates a
<name>-v<version>.skill.zip bundle. JSON to stdout, warnings to stderr.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from _shared import parse_frontmatter

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

EXCLUDE_PATTERNS = {"__pycache__", ".DS_Store", ".git", "*.pyc", "*.tmp"}
EXCLUDE_DIRS = {"__pycache__", ".git"}
EXCLUDE_EXTENSIONS = {".pyc", ".tmp"}
EXCLUDE_NAMES = {".DS_Store"}

PORTABLE_SUBDIRS = ("references", "scripts", "templates", "evals")

# Regex: absolute paths (start with /) that are NOT URLs (not preceded by ://)
ABSOLUTE_PATH_RE = re.compile(r"(?<!:/)(?<!:/)(/(?:usr|tmp|home|etc|var|opt|Users|mnt|root|private)[^\s)*\]]*)")

# Regex: @ imports at the start of a line (repo-specific path assumptions)
AT_IMPORT_RE = re.compile(r"^@\S+", re.MULTILINE)


def _warn(msg: str) -> None:
    print(f"[package] {msg}", file=sys.stderr)


def _now() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# File filtering
# ---------------------------------------------------------------------------

def _should_exclude(path: Path) -> bool:
    """Return True if the path should be excluded from the ZIP."""
    if path.name in EXCLUDE_NAMES:
        return True
    if path.suffix in EXCLUDE_EXTENSIONS:
        return True
    return any(part in EXCLUDE_DIRS for part in path.parts)


def _collect_files(skill_dir: Path) -> tuple[list[Path], list[Path]]:
    """Collect files to include and exclude from the skill directory.

    Returns (included, excluded) as lists of paths relative to skill_dir.
    """
    included: list[Path] = []
    excluded: list[Path] = []

    # Always include SKILL.md
    skill_md = skill_dir / "SKILL.md"
    if skill_md.is_file():
        included.append(Path("SKILL.md"))

    # Walk portable subdirectories
    for subdir_name in PORTABLE_SUBDIRS:
        subdir = skill_dir / subdir_name
        if not subdir.is_dir():
            continue
        for file_path in sorted(subdir.rglob("*")):
            if not file_path.is_file():
                continue
            rel = file_path.relative_to(skill_dir)
            if _should_exclude(rel):
                excluded.append(rel)
            else:
                included.append(rel)

    return included, excluded


# ---------------------------------------------------------------------------
# Portability checks
# ---------------------------------------------------------------------------

def check_frontmatter_fields(fm: dict) -> list[dict]:
    """Check cross-platform frontmatter fields are populated."""
    checks = []
    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}

    license_val = fm.get("license", "")
    checks.append({
        "check": "frontmatter_license",
        "passed": bool(license_val),
        "details": str(license_val) if license_val else "Missing license field",
    })

    author_val = meta.get("author", "")
    checks.append({
        "check": "frontmatter_author",
        "passed": bool(author_val),
        "details": str(author_val) if author_val else "Missing metadata.author field",
    })

    version_val = meta.get("version", "")
    checks.append({
        "check": "frontmatter_version",
        "passed": bool(version_val),
        "details": str(version_val) if version_val else "Missing metadata.version field",
    })

    return checks


def check_no_absolute_paths(body: str) -> dict:
    """Check for absolute filesystem paths in the body."""
    matches = []
    for i, line in enumerate(body.splitlines(), 1):
        for m in ABSOLUTE_PATH_RE.finditer(line):
            matches.append(f"line {i}: {m.group(0)}")
    return {
        "check": "no_absolute_paths",
        "passed": len(matches) == 0,
        "details": "; ".join(matches[:5]) if matches else "No absolute paths found",
    }


def check_reference_files(skill_dir: Path, body: str) -> dict:
    """Check that all referenced files in the body exist on disk."""
    mentioned = set(re.findall(r"references/([a-zA-Z0-9_.-]+)", body))
    missing = []
    ref_dir = skill_dir / "references"
    for name in sorted(mentioned):
        ref_path = ref_dir / name
        if not ref_path.is_file():
            missing.append(name)
    if not mentioned:
        return {
            "check": "reference_files_exist",
            "passed": True,
            "details": "No reference file mentions found in body",
        }
    return {
        "check": "reference_files_exist",
        "passed": len(missing) == 0,
        "details": f"Missing: {', '.join(missing)}" if missing else f"All {len(mentioned)} references resolve",
    }


def check_no_at_imports(body: str) -> dict:
    """Check for @ imports or repo-specific path assumptions.

    Skips lines inside fenced code blocks (``` ... ```) since those
    commonly contain Python decorators like @mcp.tool.
    """
    matches = []
    in_code_block = False
    for i, line in enumerate(body.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if AT_IMPORT_RE.match(line):
            matches.append(f"line {i}: {line.strip()}")
    return {
        "check": "no_at_imports",
        "passed": len(matches) == 0,
        "details": "; ".join(matches[:5]) if matches else "No @ imports found",
    }


def check_name_directory_match(fm: dict, dir_name: str) -> dict:
    """Check that frontmatter name matches the directory name."""
    fm_name = fm.get("name", "")
    return {
        "check": "name_directory_match",
        "passed": fm_name == dir_name,
        "details": (
            f"OK ({fm_name})" if fm_name == dir_name
            else f"Mismatch: frontmatter '{fm_name}' != directory '{dir_name}'"
        ),
    }


def check_required_fields(fm: dict) -> list[dict]:
    """Check that required frontmatter fields (name, description) are present."""
    checks = []
    for field in ("name", "description"):
        val = fm.get(field, "")
        checks.append({
            "check": f"required_{field}",
            "passed": bool(val),
            "details": f"OK ({val[:60]})" if val else f"Missing required field: {field}",
        })
    return checks


def run_portability_checks(skill_dir: Path, fm: dict, body: str) -> list[dict]:
    """Run all portability checks and return results."""
    checks: list[dict] = []
    checks.extend(check_required_fields(fm))
    checks.extend(check_frontmatter_fields(fm))
    checks.append(check_no_absolute_paths(body))
    checks.append(check_reference_files(skill_dir, body))
    checks.append(check_no_at_imports(body))
    checks.append(check_name_directory_match(fm, skill_dir.name))
    return checks


# ---------------------------------------------------------------------------
# Manifest generation
# ---------------------------------------------------------------------------

def generate_manifest(fm: dict, files: list[Path]) -> dict:
    """Generate a manifest.json dict for the ZIP bundle."""
    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
    return {
        "name": fm.get("name", "unknown"),
        "version": str(meta.get("version", "0.0.0")),
        "description": fm.get("description", ""),
        "license": fm.get("license", ""),
        "author": meta.get("author", ""),
        "files": [str(f) for f in sorted(files)],
        "created_at": _now(),
        "packaged_by": "package.py",
    }


# ---------------------------------------------------------------------------
# ZIP creation
# ---------------------------------------------------------------------------

def create_zip(skill_dir: Path, output_dir: Path, files: list[Path],
               manifest: dict) -> tuple[Path, list[str]]:
    """Create the .skill.zip bundle and return (path, errors)."""
    name = manifest["name"]
    version = manifest["version"]
    zip_name = f"{name}-v{version}.skill.zip"
    zip_path = output_dir / zip_name
    errors: list[str] = []

    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for rel_path in sorted(files):
                abs_path = skill_dir / rel_path
                try:
                    zf.write(abs_path, str(rel_path))
                except OSError as exc:
                    errors.append(f"Failed to add {rel_path}: {exc}")
                    _warn(f"Skipping {rel_path}: {exc}")

            manifest_json = json.dumps(manifest, indent=2) + "\n"
            zf.writestr("manifest.json", manifest_json)
    except Exception:
        # Clean up partial ZIP on failure
        if zip_path.exists():
            zip_path.unlink()
        raise

    return zip_path, errors


# ---------------------------------------------------------------------------
# Package a single skill
# ---------------------------------------------------------------------------

def package_skill(skill_dir: Path, output_dir: Path,
                  dry_run: bool = False) -> dict:
    """Package a single skill and return a result dict."""
    skill_dir = skill_dir.resolve()
    skill_md = skill_dir / "SKILL.md"

    result: dict = {
        "skill": skill_dir.name,
        "version": "0.0.0",
        "output_path": None,
        "files_included": [],
        "files_excluded": [],
        "portability_checks": [],
        "warnings": [],
        "errors": [],
    }

    if not skill_md.is_file():
        result["errors"].append(f"SKILL.md not found in {skill_dir}")
        return result

    content = skill_md.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_frontmatter(content)

    meta = fm.get("metadata", {}) if isinstance(fm.get("metadata"), dict) else {}
    version = str(meta.get("version", "0.0.0"))
    result["version"] = version

    # Portability checks
    checks = run_portability_checks(skill_dir, fm, body)
    result["portability_checks"] = checks

    failed = [c for c in checks if not c["passed"]]
    for c in failed:
        result["warnings"].append(f"{c['check']}: {c['details']}")

    # Collect files
    included, excluded = _collect_files(skill_dir)
    result["files_included"] = [str(f) for f in included]
    result["files_excluded"] = [str(f) for f in excluded]

    if dry_run:
        name = fm.get("name", skill_dir.name)
        result["output_path"] = str(output_dir / f"{name}-v{version}.skill.zip")
        return result

    # Create ZIP, then generate manifest from what was actually packaged
    manifest = generate_manifest(fm, included)
    zip_path, zip_errors = create_zip(skill_dir, output_dir, included, manifest)
    result["output_path"] = str(zip_path)
    result["errors"].extend(zip_errors)

    return result


# ---------------------------------------------------------------------------
# Package all skills
# ---------------------------------------------------------------------------

def package_all(skills_dir: Path, output_dir: Path,
                dry_run: bool = False) -> dict:
    """Package all skills under skills_dir and return a summary dict."""
    skills_dir = skills_dir.resolve()
    results: list[dict] = []

    if not skills_dir.is_dir():
        _warn(f"Skills directory not found: {skills_dir}")
        return {"skills": [], "created_at": _now(), "errors": ["Skills directory not found"]}

    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and (d / "SKILL.md").is_file():
            result = package_skill(d, output_dir, dry_run=dry_run)
            results.append(result)

    # Generate top-level manifest (unless dry-run)
    top_manifest = {
        "skills": [
            {
                "name": r["skill"],
                "version": r["version"],
                "description": "",
                "zip": Path(r["output_path"]).name if r["output_path"] else None,
            }
            for r in results
        ],
        "created_at": _now(),
    }

    # Fill in descriptions from frontmatter
    for entry in top_manifest["skills"]:
        skill_md = skills_dir / entry["name"] / "SKILL.md"
        if skill_md.is_file():
            content = skill_md.read_text(encoding="utf-8", errors="replace")
            fm, _ = parse_frontmatter(content)
            entry["description"] = fm.get("description", "")

    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = output_dir / "manifest.json"
        manifest_path.write_text(
            json.dumps(top_manifest, indent=2) + "\n", encoding="utf-8"
        )

    return {"results": results, "manifest": top_manifest}


# ---------------------------------------------------------------------------
# Table formatters
# ---------------------------------------------------------------------------

def format_table(result: dict) -> str:
    """Format a single skill package result as a human-readable table."""
    out = [f"Package: {result['skill']}", "=" * 40]
    out.append(f"Version: {result['version']}")
    if result["output_path"]:
        out.append(f"Output:  {result['output_path']}")
    out.append("")

    out.append(f"{'Check':<28} {'Result':>6}  Details")
    out.append("\u2500" * 70)
    for c in result.get("portability_checks", []):
        status = "PASS" if c["passed"] else "FAIL"
        out.append(f"{c['check']:<28} {status:>6}  {c['details']}")

    out.append("")
    out.append(f"Files included: {len(result.get('files_included', []))}")
    out.append(f"Files excluded: {len(result.get('files_excluded', []))}")

    if result.get("warnings"):
        out.append("")
        out.append("Warnings:")
        for w in result["warnings"]:
            out.append(f"  - {w}")
    if result.get("errors"):
        out.append("")
        out.append("Errors:")
        for e in result["errors"]:
            out.append(f"  - {e}")

    all_passed = all(c["passed"] for c in result.get("portability_checks", []))
    out.append("")
    out.append(f"Overall: {'PASS' if all_passed and not result.get('errors') else 'FAIL'}")
    return "\n".join(out)


def format_all_table(data: dict) -> str:
    """Format all-skills package results as a summary table."""
    results = data.get("results", [])
    out = ["Skill Package Report", "=" * 20, ""]

    hdr = f"{'Skill':<22} {'Version':>8}  {'Files':>5}  {'Checks':>8}  {'Status':>6}"
    out.append(hdr)
    out.append("\u2500" * len(hdr))

    for r in results:
        checks = r.get("portability_checks", [])
        passed = sum(1 for c in checks if c["passed"])
        total = len(checks)
        has_errors = bool(r.get("errors"))
        all_ok = passed == total and not has_errors
        fc = len(r.get("files_included", []))
        out.append(
            f"{r['skill']:<22} {r['version']:>8}  {fc:>5}  "
            f"{passed}/{total:>3}  {'PASS' if all_ok else 'FAIL':>6}"
        )

    out.append("")
    out.append(f"Total skills: {len(results)}")
    pass_count = sum(
        1 for r in results
        if all(c["passed"] for c in r.get("portability_checks", []))
        and not r.get("errors")
    )
    out.append(f"Passing: {pass_count}/{len(results)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Package skills into portable ZIP files"
    )
    parser.add_argument("path", nargs="?", help="Path to skill directory")
    parser.add_argument("--all", action="store_true",
                        help="Package all skills under skills/")
    parser.add_argument("--output", "-o", default=None,
                        help="Output directory (default: dist/)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Run portability checks only, do not create ZIP")
    parser.add_argument("--format", choices=["json", "table"], default="json",
                        dest="output_format")
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error("Provide a skill path or use --all")

    if args.path and args.all:
        parser.error("Cannot use both a path and --all; choose one")

    # Resolve output directory
    if args.output:
        output_dir = Path(args.output).resolve()
    else:
        # Default: dist/ relative to repo root (two levels up from this script)
        script_dir = Path(__file__).resolve().parent
        repo_root = script_dir.parent.parent.parent
        output_dir = repo_root / "dist"

    if args.all:
        script_dir = Path(__file__).resolve().parent
        skills_dir = script_dir.parent.parent  # skills/skill-creator/scripts -> skills/
        if not skills_dir.is_dir():
            skills_dir = Path.cwd() / "skills"
        data = package_all(skills_dir, output_dir, dry_run=args.dry_run)
        if args.output_format == "table":
            print(format_all_table(data))
        else:
            json.dump(data, sys.stdout, indent=2)
            sys.stdout.write("\n")
    else:
        result = package_skill(Path(args.path), output_dir, dry_run=args.dry_run)
        if args.output_format == "table":
            print(format_table(result))
        else:
            json.dump(result, sys.stdout, indent=2)
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()
