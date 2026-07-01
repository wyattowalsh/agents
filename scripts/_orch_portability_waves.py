#!/usr/bin/env python3
"""One-shot orchestration for remaining skill portability waves."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import textwrap
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tests"))
from tests.skill_portability_ids import (  # noqa: E402
    COMPOSED_CATALOG_PAGES,
    CUSTOM_CHECK_SKILLS,
    PLAN_SKILL_IDS,
)

SKILL_SCRIPTS = REPO / "skills" / "skill-creator" / "scripts"
PORTABLE_PYTEST_CMD = (
    "SKILL_PORTABLE_CI=1 uv run pytest tests/test_skill_portability.py "
    "tests/test_skill_bundled_toolkit.py tests/test_skills_no_wagents.py "
    "tests/test_skills_p7_operator_paths.py tests/test_namer_catalog_parity.py "
    "tests/test_composed_catalog_script_parity.py tests/test_package.py -q --tb=line"
)
MAKEFILE_PORTABLE_PYTEST = "\t" + PORTABLE_PYTEST_CMD.replace("SKILL_PORTABLE_CI=1 ", "") + "\n"


def repair_shared() -> None:
    asset = (SKILL_SCRIPTS / "asset_toolkit" / "_shared.py").read_text(encoding="utf-8")
    canon = (SKILL_SCRIPTS / "_shared.py").read_text(encoding="utf-8")
    if "BODY_OPERATOR_SKILLS_PATH_RE" not in canon:
        needle = "FRONTMATTER_SKILLS_PATH_RE = re.compile"
        idx = canon.index(needle)
        line_end = canon.index("\n", idx)
        insert = (
            "\nBODY_OPERATOR_SKILLS_PATH_RE = re.compile(\n"
            r'    r"(?<![A-Za-z0-9_./-])(?:\./)?skills/[a-z0-9][a-z0-9-]*/scripts/[^\s\'"`)]*"'
            "\n"
            ")\n"
        )
        canon = canon[: line_end + 1] + insert + canon[line_end + 1 :]
    if "find_nonportable_body_operator_lines" not in canon:
        tail = asset[asset.index("def find_nonportable_body_operator_lines") :]
        canon = canon.rstrip() + "\n\n\n" + tail
    (SKILL_SCRIPTS / "_shared.py").write_text(canon if canon.endswith("\n") else canon + "\n", encoding="utf-8")
    print("F-1: _shared.py repaired")


def repair_package() -> None:
    canon_pkg = SKILL_SCRIPTS / "package.py"
    asset_pkg = SKILL_SCRIPTS / "asset_toolkit" / "package.py"
    pkg = canon_pkg.read_text(encoding="utf-8")
    old_import = (
        "from _shared import (\n    ABSOLUTE_PATH_RE,\n    find_nonportable_frontmatter_commands,\n"
        "    format_frontmatter_command_issues,\n    parse_frontmatter,\n)"
    )
    new_import = (
        "from _shared import (\n    ABSOLUTE_PATH_RE,\n    find_nonportable_body_operator_lines,\n"
        "    find_nonportable_frontmatter_commands,\n    format_body_operator_issues,\n"
        "    format_frontmatter_command_issues,\n    parse_frontmatter,\n)"
    )
    if old_import in pkg:
        pkg = pkg.replace(old_import, new_import)
    block = asset_pkg.read_text(encoding="utf-8")
    if "def check_body_operator_commands_portable" not in pkg:
        start = block.index("def check_body_operator_commands_portable")
        end = block.index("def check_name_directory_match", start)
        fn_block = block[start:end]
        pkg = pkg.replace("def check_name_directory_match", fn_block + "\n\ndef check_name_directory_match")
    old_run = (
        "    checks.append(check_no_at_imports(body))\n"
        "    checks.append(check_name_directory_match(fm, skill_dir.name))"
    )
    new_run = (
        "    checks.append(check_no_at_imports(body))\n"
        "    checks.append(check_body_operator_commands_portable(body))\n"
        "    checks.append(check_name_directory_match(fm, skill_dir.name))"
    )
    if old_run in pkg:
        pkg = pkg.replace(old_run, new_run)
    canon_pkg.write_text(pkg, encoding="utf-8")
    print("F-2: package.py repaired")


def repair_test_package() -> None:
    test_pkg = REPO / "tests" / "test_package.py"
    tp = test_pkg.read_text(encoding="utf-8")
    if "class TestBodyOperatorPaths" in tp:
        return
    marker = (
        "# ---------------------------------------------------------------------------\n"
        "# Name / directory match\n"
        "# ---------------------------------------------------------------------------"
    )
    body = """

# ---------------------------------------------------------------------------
# Body operator paths (P7)
# ---------------------------------------------------------------------------


class TestBodyOperatorPaths:
    def test_detects_repo_root_script_path_in_prose(self):
        body = "Run skills/foo/scripts/bar.py before packaging."
        result = check_body_operator_commands_portable(body)
        assert not result["passed"]
        assert "skills/foo/scripts/bar.py" in result["details"]

    def test_ignores_paths_inside_fenced_code(self):
        body = "```bash\\nuv run python skills/foo/scripts/bar.py\\n```"
        result = check_body_operator_commands_portable(body)
        assert result["passed"]

    def test_accepts_portable_scripts_path(self):
        body = "Run scripts/bar.py from the skill directory."
        result = check_body_operator_commands_portable(body)
        assert result["passed"]


"""
    tp = tp.replace(marker, body + marker)
    tp = tp.replace(
        "from package import (\n    ABSOLUTE_PATH_RE,",
        "from package import (\n    ABSOLUTE_PATH_RE,\n    check_body_operator_commands_portable,",
    )
    test_pkg.write_text(tp, encoding="utf-8")
    print("F-6: test_package.py updated")


def sync_toolkit() -> None:
    subprocess.run(
        [sys.executable, str(SKILL_SCRIPTS / "sync_asset_toolkit.py"), "--skill-ids", *PLAN_SKILL_IDS, "--apply"],
        cwd=REPO,
        check=True,
    )
    print("F-apply: toolkit sync OK")


def fix_authoring_mdx() -> None:
    sys.path.insert(0, str(SKILL_SCRIPTS))
    from _shared import find_nonportable_body_operator_lines

    auth_dir = REPO / "docs/src/authoring/skills"
    fixed: list[str] = []
    for sid in PLAN_SKILL_IDS:
        mdx = auth_dir / f"{sid}.mdx"
        if not mdx.is_file():
            continue
        content = mdx.read_text(encoding="utf-8")
        if not content.startswith("---"):
            continue
        end = content.find("\n---\n", 3)
        if end < 0:
            continue
        fm_block = content[: end + 5]
        body = content[end + 5 :]
        issues = find_nonportable_body_operator_lines(body)
        if not issues:
            continue
        lines = body.splitlines()
        for issue in issues:
            ln = issue["line"] - 1
            old = issue["match"]
            portable = re.sub(r"^(?:\./)?skills/[a-z0-9][a-z0-9-]*/scripts/", "scripts/", old)
            lines[ln] = lines[ln].replace(old, portable)
        new_body = "\n".join(lines)
        if body.endswith("\n") and not new_body.endswith("\n"):
            new_body += "\n"
        mdx.write_text(fm_block + new_body, encoding="utf-8")
        fixed.append(sid)
    namer = auth_dir / "namer.mdx"
    if namer.is_file():
        t = namer.read_text(encoding="utf-8")
        t2 = t.replace("scripts/check.py check-all", "scripts/availability.py check-all").replace(
            "skills/namer/scripts/check.py", "scripts/availability.py"
        )
        if t2 != t:
            namer.write_text(t2, encoding="utf-8")
            if "namer" not in fixed:
                fixed.append("namer")
    print(f"P7 authoring: fixed {len(fixed)} files")


def write_openspec_and_manifest() -> None:
    os_dir = REPO / "openspec/changes/skill-portability-decouple"
    (os_dir / "specs/skills-lifecycle").mkdir(parents=True, exist_ok=True)
    (os_dir / "proposal.md").write_text(
        textwrap.dedent(
            """\
            # Proposal

            ## Problem

            Skill validators and packaging depended on repo-root paths and wagents CLI references,
            breaking portable ZIP installs and SKILL_PORTABLE_CI gates.

            ## Intent

            Bundle asset_toolkit per in-scope skill, standardize scripts/check.py with portable CI mode,
            enforce P7 body operator path hygiene, and gate CI via pytest.

            ## Validation

            - make skill-portability-check
            - make skill-toolkit-sync-check
            - SKILL_PORTABLE_CI=1 uv run pytest tests/test_skill_portability.py -q
            - uv run wagents validate
            """
        ),
        encoding="utf-8",
    )
    (os_dir / "tasks.md").write_text(
        textwrap.dedent(
            """\
            # Tasks

            - [x] F-core: _shared.py body-operator helpers, bundled package.py, sync_asset_toolkit.py
            - [x] F-apply: toolkit sync for PLAN_SKILL_IDS (50 skills)
            - [x] GEN: standard check.py with PORTABLE_CI
            - [x] CC+NAM: custom checks (5) + namer availability.py split
            - [x] P7: SKILL.md + authoring MDX prose path fixes
            - [x] T: portability pytest modules + skill_portability_ids.py SSOT
            - [x] G: Makefile + ci.yml SKILL_PORTABLE_CI gate
            - [ ] CAT: wagents docs generate refresh catalog from authoring
            - [ ] V: full gate green + portability-only commit isolation
            """
        ),
        encoding="utf-8",
    )
    (os_dir / "specs/skills-lifecycle/spec.md").write_text(
        textwrap.dedent(
            """\
            ## ADDED Requirements

            ### Requirement: Portable skill validation

            Each skill in PLAN_SKILL_IDS MUST ship scripts/check.py and bundled scripts/asset_toolkit/
            sufficient to validate without sibling skill paths when SKILL_PORTABLE_CI=1.

            #### Scenario: Portable CI check passes

            - **WHEN** SKILL_PORTABLE_CI=1 and uv run python scripts/check.py runs from the skill directory
            - **THEN** the command exits 0 using only bundled toolkit modules

            ### Requirement: P7 body operator paths

            SKILL.md prose outside fenced code blocks MUST reference local scripts as scripts/<file> only.

            #### Scenario: No repo-root script paths in prose

            - **WHEN** find_nonportable_body_operator_lines() scans the SKILL.md body
            - **THEN** zero matches are returned
            """
        ),
        encoding="utf-8",
    )
    manifest = {
        "plan_skill_ids": list(PLAN_SKILL_IDS),
        "excluded_skills": ["desktop-computer-use"],
        "custom_check_skills": sorted(CUSTOM_CHECK_SKILLS),
        "composed_catalog_pages": len(COMPOSED_CATALOG_PAGES),
        "denylist_paths": ["kb/activity/**", "integrate-open-computer-use", "docs-v2-wip"],
        "gates": {"makefile": "skill-portability-check", "ci_env": "SKILL_PORTABLE_CI=1"},
    }
    manifest_path = REPO / "planning/manifests/skill-portability.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("G-OS + R0-D: openspec + manifest written")


def add_gates() -> None:
    mk = REPO / "Makefile"
    mt = mk.read_text(encoding="utf-8")
    if "skill-portability-check:" not in mt:
        mt = mt.rstrip() + "\n\nskill-portability-check:  ## Run portable skill CI checks\n"
        mt += MAKEFILE_PORTABLE_PYTEST
        mt += "\nskill-toolkit-sync-check:  ## Verify bundled asset_toolkit SSOT\n"
        mt += "\tuv run python scripts/sync_skill_portability.py --check\n"
        mk.write_text(mt + "\n", encoding="utf-8")
        print("G-CI: Makefile targets added")
    ci = REPO / ".github/workflows/ci.yml"
    ct = ci.read_text(encoding="utf-8")
    if "SKILL_PORTABLE_CI=1" not in ct:
        anchor = "      - run: uv run wagents skills sync --dry-run\n"
        insert = (
            f"      - run: {PORTABLE_PYTEST_CMD}\n"
            "      - run: uv run python scripts/sync_skill_portability.py --check\n"
        )
        ci.write_text(ct.replace(anchor, insert + anchor), encoding="utf-8")
        print("G-CI: ci.yml gate added")
    sc = REPO / "skills/skill-creator/SKILL.md"
    sct = sc.read_text(encoding="utf-8")
    if "portability-contract.md" not in sct and "references/quality-rubric.md" in sct:
        sc.write_text(
            sct.replace(
                "| `references/quality-rubric.md`",
                (
                    "| `references/portability-contract.md` | P5/P6/P7 portable packaging contract |\n"
                    "| `references/quality-rubric.md`"
                ),
            ),
            encoding="utf-8",
        )
        print("G-OS-02: skill-creator index updated")


def main() -> int:
    repair_shared()
    repair_package()
    repair_test_package()
    sync_toolkit()
    fix_authoring_mdx()
    write_openspec_and_manifest()
    add_gates()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
