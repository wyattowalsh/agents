"""Consistency guards for repeated nerdbot schema surfaces.

These tests catch drift between the reference docs and template assets that
define the same structural contracts (source-map columns, coverage columns,
activity-log entry fields).  A failure here means someone edited one surface
without updating the others.

Surfaces under guard:
  references/kb-architecture.md    (arch)
  references/page-templates.md     (templates)
  assets/activity-log-template.md  (log-tpl)
  assets/kb-bootstrap-template.md  (bootstrap)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_NERDBOT = Path(__file__).resolve().parents[1] / "skills" / "nerdbot"
_SCRIPT_DIR = _NERDBOT / "scripts"
_SRC_DIR = _NERDBOT / "src"
for _path in (_SCRIPT_DIR, _SRC_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from kb_bootstrap import render_activity_log, render_packet_starter  # noqa: E402
from nerdbot import contracts  # noqa: E402

KB_ARCHITECTURE = _NERDBOT / "references" / "kb-architecture.md"
PAGE_TEMPLATES = _NERDBOT / "references" / "page-templates.md"
ACTIVITY_LOG_TEMPLATE = _NERDBOT / "assets" / "activity-log-template.md"
KB_BOOTSTRAP_TEMPLATE = _NERDBOT / "assets" / "kb-bootstrap-template.md"
SOURCE_SUMMARY_TEMPLATE = _NERDBOT / "assets" / "source-summary-template.md"
EVALS_DIR = _NERDBOT / "evals"

# ---------------------------------------------------------------------------
# Lightweight helpers
# ---------------------------------------------------------------------------


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _extract_table_columns(text: str, anchor_cell: str) -> list[str] | None:
    """Return column names from the first markdown table whose first data
    column matches *anchor_cell* (case-sensitive, stripped).

    Looks for a header row like ``| Col A | Col B | ...`` where the first
    non-separator cell equals *anchor_cell*.  Returns the list of stripped
    column names, or ``None`` if no matching table is found.
    """
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0] == anchor_cell:
            return cells
    return None


_FIELD_KEY_RE = re.compile(
    r"^- (?:`([^`]+)`|([A-Z][\w /:-]+\w)):",  # backtick-wrapped or plain label
    re.MULTILINE,
)


def _extract_entry_field_keys(text: str) -> list[str]:
    """Return the ordered list of field keys from an activity-log entry
    template block.

    Handles both backtick-wrapped keys (``- `raw`: ...``) and plain keys
    (``- Mode: ...``).  Stops collecting if a non-field continuation line
    (like ``  - [next safe batch]``) is encountered after at least one key.
    """
    keys: list[str] = []
    for m in _FIELD_KEY_RE.finditer(text):
        key = m.group(1) or m.group(2)
        keys.append(key.strip())
    return keys


def _extract_entry_block(text: str) -> str:
    """Return the first activity-log entry block starting with ``### [``."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("### ["):
            start = i
            break
    if start is None:
        return ""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        line = lines[i].strip()
        # Another heading or horizontal rule signals end of the block
        if line.startswith("## ") or line.startswith("### [") or line == "---":
            end = i
            break
    return "\n".join(lines[start:end])


def _extract_operating_rules(text: str) -> list[str]:
    """Return the bullet items under the ``## Operating rules`` heading."""
    lines = text.splitlines()
    in_section = False
    rules: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped == "## Operating rules":
            in_section = True
            continue
        if in_section:
            if stripped.startswith("## ") or stripped.startswith("### "):
                break
            if stripped.startswith("- "):
                rules.append(stripped)
    return rules


_MODE_LINE_RE = re.compile(r"^- Mode: \[([^\]]+)\]", re.MULTILINE)


def _extract_mode_options(text: str) -> list[str]:
    match = _MODE_LINE_RE.search(text)
    assert match, "No activity-log mode option line found"
    return match.group(1).split("|")


# ===================================================================
# 1. Source-map columns stay aligned
# ===================================================================


class TestSourceMapColumns:
    """The source-map table header must be identical in every surface."""

    ANCHOR = "Source ID"

    def _columns_from(self, path: Path) -> list[str]:
        cols = _extract_table_columns(_read(path), self.ANCHOR)
        assert cols is not None, f"No source-map table found in {path.name}"
        return cols

    def test_architecture_defines_source_map_columns(self) -> None:
        cols = self._columns_from(KB_ARCHITECTURE)
        assert cols[0] == "Source ID"
        assert len(cols) >= 5, "source-map table should have at least 5 columns"

    def test_page_templates_matches_architecture(self) -> None:
        arch = self._columns_from(KB_ARCHITECTURE)
        tmpl = self._columns_from(PAGE_TEMPLATES)
        assert tmpl == arch, (
            f"source-map columns drifted between kb-architecture.md and page-templates.md:\n"
            f"  arch:      {arch}\n"
            f"  templates: {tmpl}"
        )

    def test_bootstrap_matches_architecture(self) -> None:
        arch = self._columns_from(KB_ARCHITECTURE)
        boot = self._columns_from(KB_BOOTSTRAP_TEMPLATE)
        assert boot == arch, (
            f"source-map columns drifted between kb-architecture.md and kb-bootstrap-template.md:\n"
            f"  arch:      {arch}\n"
            f"  bootstrap: {boot}"
        )


# ===================================================================
# 2. Coverage columns stay aligned
# ===================================================================


class TestCoverageColumns:
    """The coverage table header must be identical in every surface."""

    ANCHOR = "Wiki path"

    def _columns_from(self, path: Path) -> list[str]:
        cols = _extract_table_columns(_read(path), self.ANCHOR)
        assert cols is not None, f"No coverage table found in {path.name}"
        return cols

    def test_architecture_defines_coverage_columns(self) -> None:
        cols = self._columns_from(KB_ARCHITECTURE)
        assert cols[0] == "Wiki path"
        assert len(cols) >= 5, "coverage table should have at least 5 columns"

    def test_page_templates_matches_architecture(self) -> None:
        arch = self._columns_from(KB_ARCHITECTURE)
        tmpl = self._columns_from(PAGE_TEMPLATES)
        assert tmpl == arch, (
            f"coverage columns drifted between kb-architecture.md and page-templates.md:\n"
            f"  arch:      {arch}\n"
            f"  templates: {tmpl}"
        )

    def test_bootstrap_matches_architecture(self) -> None:
        arch = self._columns_from(KB_ARCHITECTURE)
        boot = self._columns_from(KB_BOOTSTRAP_TEMPLATE)
        assert boot == arch, (
            f"coverage columns drifted between kb-architecture.md and kb-bootstrap-template.md:\n"
            f"  arch:      {arch}\n"
            f"  bootstrap: {boot}"
        )


# ===================================================================
# 3. Activity-log entry fields stay aligned
# ===================================================================


class TestActivityLogEntryFields:
    """Every surface that defines an activity-log entry template must list
    the same field keys in the same order."""

    def _keys_from(self, path: Path) -> list[str]:
        block = _extract_entry_block(_read(path))
        assert block, f"No activity-log entry block found in {path.name}"
        keys = _extract_entry_field_keys(block)
        assert keys, f"No field keys parsed from entry block in {path.name}"
        return keys

    # -- sanity: the canonical template defines the expected field set ------

    def test_activity_log_template_defines_expected_fields(self) -> None:
        keys = self._keys_from(ACTIVITY_LOG_TEMPLATE)
        expected = [
            "Mode",
            "Summary",
            "raw",
            "wiki",
            "indexes",
            "schema",
            "config",
            "canonical material",
            "provenance",
            "derived output",
            "vault",
            "path map",
            "link/backlink impact",
            "Risks / rollback",
            "Follow-up",
        ]
        assert keys == expected, (
            f"Activity-log template field keys differ from expected canonical set:\n"
            f"  got:      {keys}\n"
            f"  expected: {expected}"
        )

    # -- cross-surface alignment -------------------------------------------

    def test_architecture_matches_activity_log_template(self) -> None:
        canon = self._keys_from(ACTIVITY_LOG_TEMPLATE)
        arch = self._keys_from(KB_ARCHITECTURE)
        assert arch == canon, (
            f"activity-log entry fields drifted between activity-log-template.md and kb-architecture.md:\n"
            f"  log-tpl: {canon}\n"
            f"  arch:    {arch}"
        )

    def test_page_templates_matches_activity_log_template(self) -> None:
        canon = self._keys_from(ACTIVITY_LOG_TEMPLATE)
        tmpl = self._keys_from(PAGE_TEMPLATES)
        assert tmpl == canon, (
            f"activity-log entry fields drifted between activity-log-template.md and page-templates.md:\n"
            f"  log-tpl:    {canon}\n"
            f"  templates:  {tmpl}"
        )

    def test_bootstrap_matches_activity_log_template(self) -> None:
        canon = self._keys_from(ACTIVITY_LOG_TEMPLATE)
        boot = self._keys_from(KB_BOOTSTRAP_TEMPLATE)
        assert boot == canon, (
            f"activity-log entry fields drifted between activity-log-template.md and kb-bootstrap-template.md:\n"
            f"  log-tpl:    {canon}\n"
            f"  bootstrap:  {boot}"
        )


# ===================================================================
# 4. Activity-log operating rules in bootstrap match the template
# ===================================================================


class TestActivityLogOperatingRules:
    """The operating-rules bullet list that the bootstrap template carries
    must stay in sync with the canonical activity-log template."""

    def test_bootstrap_operating_rules_match_template(self) -> None:
        canon = _extract_operating_rules(_read(ACTIVITY_LOG_TEMPLATE))
        boot = _extract_operating_rules(_read(KB_BOOTSTRAP_TEMPLATE))
        assert canon, "No operating rules found in activity-log-template.md"
        assert boot, "No operating rules found in kb-bootstrap-template.md"
        assert boot == canon, (
            f"Operating rules drifted between activity-log-template.md and kb-bootstrap-template.md:\n"
            f"  log-tpl:   {canon}\n"
            f"  bootstrap: {boot}"
        )


class TestEvalManifestAlignment:
    """The canonical eval manifest and per-case files must not drift."""

    def test_evals_manifest_ids_match_case_files(self) -> None:
        manifest = json.loads((EVALS_DIR / "evals.json").read_text(encoding="utf-8"))
        manifest_ids = {item["id"] for item in manifest["evals"]}
        case_ids = {path.stem for path in EVALS_DIR.glob("*.json") if path.name != "evals.json"}

        assert manifest_ids == case_ids


def test_bootstrap_packet_defines_obsidian_vault_starter_section() -> None:
    bootstrap_text = _read(KB_BOOTSTRAP_TEMPLATE)

    assert "Path: `config/obsidian-vault.md`" in bootstrap_text
    assert "Path: `.obsidian/templates/wiki-note-template.md`" in bootstrap_text
    assert "Path: `.obsidian/templates/source-note-template.md`" in bootstrap_text


# ===================================================================
# 5. Template source-record fields stay aligned with contracts.py
# ===================================================================


class TestSourceRecordFields:
    """Source-note surfaces must carry the full machine-readable source
    record contract from ``nerdbot.contracts``."""

    def test_source_summary_template_lists_contract_source_record_fields(self) -> None:
        template = _read(SOURCE_SUMMARY_TEMPLATE)

        for field in contracts.SOURCE_RECORD_FIELDS:
            assert f"`{field}`" in template, f"Missing SOURCE_RECORD_FIELDS item in source summary: {field}"

    def test_rendered_bootstrap_source_note_lists_contract_source_record_fields(self) -> None:
        rendered = render_packet_starter(Path("sample-kb"), ".obsidian/templates/source-note-template.md")

        for field in contracts.SOURCE_RECORD_FIELDS:
            assert f"`{field}`" in rendered, f"Missing SOURCE_RECORD_FIELDS item in source note: {field}"


# ===================================================================
# 6. Rendered bootstrap source note carries canonical provenance
# ===================================================================


class TestRenderedBootstrapSourceNote:
    """The actual source-note template written by bootstrap must include
    the same provenance surface as the canonical source-summary template."""

    def test_rendered_bootstrap_source_note_includes_provenance_section(self) -> None:
        rendered = render_packet_starter(Path("sample-kb"), ".obsidian/templates/source-note-template.md")

        assert "## Provenance" in rendered
        assert "| Claim or section | Raw path | Anchor | Notes |" in rendered
        assert "`raw/extracts/" in rendered


# ===================================================================
# 7. Activity-log mode vocabulary follows runtime contracts
# ===================================================================


class TestActivityLogModeVocabulary:
    """Activity-log examples list runtime mode tokens from contracts.py."""

    EXPECTED_OPTIONS = list(contracts.ACTIVITY_LOG_MODES)

    def test_activity_log_template_uses_runtime_mode_tokens(self) -> None:
        modes = _extract_mode_options(_read(ACTIVITY_LOG_TEMPLATE))
        assert modes == self.EXPECTED_OPTIONS

    def test_rendered_bootstrap_activity_log_uses_runtime_mode_tokens(self) -> None:
        modes = _extract_mode_options(render_activity_log(Path("sample-kb")))
        assert modes == self.EXPECTED_OPTIONS

    def test_architecture_uses_runtime_mode_tokens(self) -> None:
        modes = _extract_mode_options(_read(KB_ARCHITECTURE))
        assert modes == self.EXPECTED_OPTIONS

    def test_page_templates_uses_runtime_mode_tokens(self) -> None:
        modes = _extract_mode_options(_read(PAGE_TEMPLATES))
        assert modes == self.EXPECTED_OPTIONS
