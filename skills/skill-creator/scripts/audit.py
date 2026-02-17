#!/usr/bin/env python3
"""Deterministic quality scoring for AI agent skills.

Reads skills/<name>/SKILL.md, evaluates frontmatter, body structure,
pattern coverage, references, scripts, and conciseness, then outputs
a structured JSON report to stdout. Warnings go to stderr.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

KEBAB_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
RESERVED_WORDS = {"anthropic", "claude"}
ACTION_VERBS = {
    "create", "detect", "analyze", "generate", "scan", "build", "run",
    "check", "validate", "review", "host", "simulate", "audit", "deploy",
    "transform", "convert", "extract", "parse", "install", "configure",
    "monitor", "test", "optimize", "refactor", "scaffold", "migrate",
    "evaluate", "research", "diagnose", "surface", "explore",
}
GRADE_THRESHOLDS = [(90, "A"), (75, "B"), (60, "C"), (40, "D"), (0, "F")]
PATTERN_NAMES = [
    "dispatch-table", "reference-file-index", "critical-rules",
    "canonical-vocabulary", "scope-boundaries", "classification-gating",
    "scaling-strategy", "state-management", "scripts", "templates",
    "hooks", "progressive-disclosure", "body-substitutions",
]


def _warn(msg: str) -> None:
    print(f"[audit] {msg}", file=sys.stderr)


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _grade(score: float) -> str:
    for threshold, letter in GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"


# ---------------------------------------------------------------------------
# Frontmatter parser
# ---------------------------------------------------------------------------

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML between --- delimiters and the body text below."""
    if not content.startswith("---"):
        return {}, content
    end = content.find("---", 3)
    if end == -1:
        return {}, content
    try:
        fm = yaml.safe_load(content[3:end].strip())
        if not isinstance(fm, dict):
            fm = {}
    except yaml.YAMLError as exc:
        _warn(f"YAML parse error: {exc}")
        fm = {}
    return fm, content[end + 3:].strip()


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def score_frontmatter(fm: dict, dir_name: str) -> dict:
    """Frontmatter completeness and correctness (0-10, weight 1.0)."""
    s, f = 0, []
    name = fm.get("name", "")
    if name:
        s += 1; f.append("name field present")
        if KEBAB_RE.match(name):
            s += 1; f.append("name is valid kebab-case")
        else:
            f.append("name is not valid kebab-case")
        if len(name) <= 64:
            s += 1
        else:
            f.append(f"name exceeds 64 chars ({len(name)})")
        if name == dir_name:
            s += 1; f.append("name matches directory name")
        else:
            f.append(f"name '{name}' does not match directory '{dir_name}'")
        if "--" in name:
            f.append("name contains consecutive hyphens"); s = max(s - 1, 0)
        if name.startswith("-") or name.endswith("-"):
            f.append("name has leading/trailing hyphens"); s = max(s - 1, 0)
        for w in RESERVED_WORDS:
            if w in name.lower():
                f.append(f"name contains reserved word '{w}'"); s = max(s - 1, 0)
    else:
        f.append("MISSING required field: name")
    desc = fm.get("description", "")
    if desc and str(desc).strip():
        s += 2; f.append("description field present")
        if re.search(r"<[a-zA-Z][^>]*>", str(desc)):
            f.append("description contains XML/HTML tags"); s = max(s - 1, 0)
    else:
        f.append("MISSING required field: description")
    if fm.get("license"):
        s += 1; f.append("license field present")
    meta = fm.get("metadata", {})
    if isinstance(meta, dict):
        if meta.get("author"):
            s += 1; f.append("metadata.author present")
        if meta.get("version"):
            s += 1; f.append("metadata.version present")
    return {"name": "Frontmatter Completeness", "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f}


def score_description(fm: dict) -> dict:
    """Description quality (0-20, weight 2.0)."""
    s, f = 0, []
    desc = str(fm.get("description", "")).strip()
    if not desc:
        f.append("No description to evaluate")
        return {"name": "Description Quality", "score": 0, "max": 20, "weight": 2.0, "findings": f}
    ln = len(desc)
    if 50 <= ln <= 200:
        s += 6; f.append(f"Description length optimal ({ln} chars)")
    elif 30 <= ln < 50:
        s += 3; f.append(f"Description slightly short ({ln} chars)")
    elif 200 < ln <= 300:
        s += 4; f.append(f"Description slightly long ({ln} chars)")
    elif ln > 300:
        s += 2; f.append(f"Description too long ({ln} chars, >300)")
    else:
        s += 1; f.append(f"Description too short ({ln} chars, <30)")
    words = set(re.findall(r"\b[a-z]+\b", desc.lower()))
    verbs = words & ACTION_VERBS
    if verbs:
        s += 4; f.append(f"Action verbs found: {', '.join(sorted(verbs)[:5])}")
    else:
        f.append("No action verbs detected")
    dl = desc.lower()
    if "use when" in dl or "use for" in dl:
        s += 3; f.append("Contains 'Use when/for' trigger clause")
    else:
        f.append("Missing 'Use when/for' trigger clause")
    if "not for" in dl or "not when" in dl:
        s += 3; f.append("Contains exclusion clause (NOT for)")
    else:
        f.append("Missing exclusion clause (NOT for)")
    first = desc.split()[0].lower() if desc.split() else ""
    if first in ("i", "you", "my", "your", "we"):
        f.append(f"Description starts with '{first}' — prefer third-person voice")
    else:
        s += 4; f.append("Third-person voice check passed")
    return {"name": "Description Quality", "score": min(s, 20), "max": 20, "weight": 2.0, "findings": f}


def score_dispatch_table(body: str) -> dict:
    """Dispatch table presence and quality (0-10, weight 1.0)."""
    s, f = 0, []
    has_args = any("$ARGUMENTS" in ln and "|" in ln for ln in body.splitlines())
    if not has_args:
        f.append("No dispatch table with $ARGUMENTS found")
        return {"name": "Dispatch Table", "score": 0, "max": 10, "weight": 1.0, "findings": f}
    s += 4; f.append("Dispatch table with $ARGUMENTS found")
    # Count data rows
    in_t, rows = False, 0
    for line in body.splitlines():
        if "$ARGUMENTS" in line and "|" in line:
            in_t = True; rows += 1; continue
        if in_t and "|" in line:
            stripped = line.strip().strip("|").strip()
            if stripped and not re.match(r"^[-:\s|]+$", stripped):
                rows += 1
            elif not re.match(r"^[-:\s|]+$", stripped):
                break
        elif in_t:
            break
    if rows >= 3:
        s += 3; f.append(f"Dispatch table has {rows} rows (>= 3)")
    else:
        s += 1; f.append(f"Dispatch table has only {rows} rows (< 3)")
    if any("empty" in ln.lower() and "|" in ln for ln in body.splitlines()):
        s += 3; f.append("Empty-args handler row found")
    else:
        f.append("No empty-args handler row in dispatch table")
    return {"name": "Dispatch Table", "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f}


def score_body_structure(body: str) -> dict:
    """Body structure quality (0-15, weight 1.5)."""
    s, f, lines = 0, [], body.splitlines()
    lc = len(lines)
    if lc <= 500:
        s += 4; f.append(f"Body length acceptable ({lc} lines)")
    else:
        s += 1; f.append(f"Body too long ({lc} lines, >500)")
    headings = [(len(m.group(1)), m.group(0).strip())
                for line in lines if (m := re.match(r"^(#{1,6})\s+", line))]
    h2 = sum(1 for lv, _ in headings if lv == 2)
    h3 = sum(1 for lv, _ in headings if lv == 3)
    first_h4 = next((i for i, (lv, _) in enumerate(headings) if lv == 4), None)
    first_h2 = next((i for i, (lv, _) in enumerate(headings) if lv == 2), None)
    if first_h4 is not None and (first_h2 is None or first_h4 < first_h2):
        f.append("Invalid heading hierarchy: #### appears before any ##")
    elif headings:
        s += 3; f.append("Heading hierarchy valid")
    else:
        f.append("No headings found in body")
    if h2 >= 3:
        s += 5; f.append(f"Good section coverage ({h2} ## sections)")
    elif h2 >= 1:
        s += 2; f.append(f"Limited section coverage ({h2} ## sections, need >= 3)")
    else:
        f.append("No ## sections found")
    if h2 >= 3 and h3 >= 2:
        s += 3; f.append(f"Good sub-section depth ({h3} ### sub-sections)")
    return {"name": "Body Structure", "score": min(s, 15), "max": 15, "weight": 1.5, "findings": f}


def score_pattern_coverage(body: str, dir_path: Path) -> dict:
    """Coverage of 13 skill patterns (0-15, weight 1.5)."""
    f, found = [], []
    bl = body.lower()
    # 1. Dispatch Table
    if any("$ARGUMENTS" in ln and "|" in ln for ln in body.splitlines()):
        found.append("dispatch-table")
    # 2. Reference File Index
    if any("references/" in ln.lower() and "|" in ln for ln in body.splitlines()):
        found.append("reference-file-index")
    # 3. Critical Rules
    if re.search(r"^#+\s*critical\s+rules", body, re.I | re.M):
        if re.findall(r"^\s*\d+[.)]\s+", body, re.M):
            found.append("critical-rules")
    # 4. Canonical Vocabulary
    if re.search(r"canonical\s+term|canonical\s+vocab|vocabulary", bl):
        found.append("canonical-vocabulary")
    # 5. Scope Boundaries
    if "not for" in bl or "not when" in bl:
        found.append("scope-boundaries")
    # 6. Classification / Gating Logic
    if re.search(r"scor(e|ing)|tier\s+assign|classif", bl):
        found.append("classification-gating")
    # 7. Scaling Strategy
    if re.search(r"scal(e|ing)|scope.based|dispatch.*table", bl) and "|" in body:
        found.append("scaling-strategy")
    # 8. State Management
    if re.search(r"state\s+manage|journal|save|resume", bl):
        found.append("state-management")
    # 9. Scripts
    sd = dir_path / "scripts"
    if sd.is_dir() and list(sd.glob("*.py")):
        found.append("scripts")
    # 10. Templates
    td = dir_path / "templates"
    if td.is_dir() and list(td.glob("*.html")):
        found.append("templates")
    # 11. Hooks — check body and frontmatter
    full = _read(dir_path / "SKILL.md") or ""
    fm_block = ""
    if full.startswith("---") and full.count("---") >= 2:
        fm_block = full.split("---")[1]
    if "hooks:" in body or "hooks:" in fm_block:
        found.append("hooks")
    # 12. Progressive Disclosure
    rd = dir_path / "references"
    if rd.is_dir() and any(rd.iterdir()):
        found.append("progressive-disclosure")
    # 13. Body Substitutions
    if "$ARGUMENTS" in body or re.search(r"\$\d+|\$N", body):
        found.append("body-substitutions")
    suggested = [p for p in PATTERN_NAMES if p not in found]
    pc = len(found)
    f.append(f"Patterns found: {pc}/13")
    for p in found:
        f.append(f"  [+] {p}")
    if suggested:
        f.append(f"Suggested additions: {', '.join(suggested[:5])}")
    return {
        "name": "Pattern Coverage", "score": min(pc * 2, 15), "max": 15,
        "weight": 1.5, "findings": f, "_found": found, "_suggested": suggested,
    }


def score_references(dir_path: Path, body: str) -> dict:
    """Reference file management (0-10, weight 1.0)."""
    s, f = 0, []
    rd = dir_path / "references"
    if not rd.is_dir():
        f.append("No references/ directory found")
        return {"name": "References", "score": 0, "max": 10, "weight": 1.0, "findings": f}
    if any("references/" in ln.lower() and "|" in ln for ln in body.splitlines()):
        s += 3; f.append("Reference index table found in body")
    else:
        f.append("No reference index table in body")
    on_disk = sorted(p.name for p in rd.iterdir() if p.is_file() and not p.name.startswith("."))
    mentioned = set(re.findall(r"references/([a-zA-Z0-9_.-]+\.md)", body))
    orphans = [n for n in on_disk if n not in mentioned]
    if orphans:
        f.append(f"Orphan reference files: {', '.join(orphans)}")
    else:
        s += 2; f.append("No orphan reference files")
    missing = [m for m in sorted(mentioned) if m not in on_disk]
    if missing:
        f.append(f"Missing reference files: {', '.join(missing)}")
    else:
        s += 2; f.append("No missing reference files")
    good = 0
    for name in on_disk:
        txt = _read(rd / name)
        if txt is None:
            continue
        lc = len(txt.splitlines())
        if lc < 50:
            f.append(f"Size warning: {name}: {lc} lines (<50)")
        elif lc > 500:
            f.append(f"Size warning: {name}: {lc} lines (>500)")
        else:
            good += 1
    if good:
        s += min(good, 3); f.append(f"{good} reference files with appropriate size")
    return {"name": "References", "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f}


def score_critical_rules(body: str) -> dict:
    """Critical rules section (0-10, weight 1.0)."""
    s, f = 0, []
    m = re.search(r"^#+\s*Critical\s+Rules", body, re.I | re.M)
    if not m:
        f.append("No 'Critical Rules' section found")
        return {"name": "Critical Rules", "score": 0, "max": 10, "weight": 1.0, "findings": f}
    s += 3; f.append("Critical Rules section found")
    nxt = re.search(r"^#{1,3}\s+", body[m.end():], re.M)
    section = body[m.end():m.end() + nxt.start()] if nxt else body[m.end():]
    items = re.findall(r"^\s*\d+[.)]\s+.+", section, re.M)
    ic = len(items)
    if ic >= 5:
        s += 4; f.append(f"Has {ic} numbered rules (>= 5)")
    elif ic >= 3:
        s += 2; f.append(f"Has {ic} numbered rules (3-4, prefer >= 5)")
    elif ic >= 1:
        s += 1; f.append(f"Has only {ic} numbered rules")
    else:
        f.append("No numbered rules found")
    imperative = ("never", "always", "must", "do not", "ensure", "require",
                  "check", "save", "force", "label", "allow", "flag", "name",
                  "read", "run", "skip", "acknowledge", "apply")
    ac = sum(1 for item in items if any(v in item.lower() for v in imperative))
    if ac >= 3:
        s += 3; f.append(f"{ac} rules appear actionable")
    elif ac >= 1:
        s += 1; f.append(f"Only {ac} rules appear actionable")
    else:
        f.append("Rules lack imperative verbs")
    return {"name": "Critical Rules", "score": min(s, 10), "max": 10, "weight": 1.0, "findings": f}


def score_scripts(dir_path: Path) -> dict:
    """Scripts directory quality (0-5, weight 0.5)."""
    s, f = 0, []
    sd = dir_path / "scripts"
    if not sd.is_dir():
        f.append("No scripts/ directory (optional)")
        return {"name": "Scripts", "score": 0, "max": 5, "weight": 0.5, "findings": f}
    py = list(sd.glob("*.py"))
    if not py:
        f.append("scripts/ exists but no .py files")
        return {"name": "Scripts", "score": 0, "max": 5, "weight": 0.5, "findings": f}
    s += 1; f.append(f"Found {len(py)} Python script(s)")
    ap, jo, ds = False, False, False
    for p in py:
        c = _read(p)
        if c is None:
            continue
        if "argparse" in c: ap = True
        if "json.dump" in c: jo = True
        if '"""' in c[:500] or "'''" in c[:500]: ds = True
    if ap: s += 1; f.append("Script(s) use argparse")
    if jo: s += 1; f.append("Script(s) produce JSON output")
    if ds: s += 1; f.append("Script(s) have docstrings")
    if len(py) >= 2: s += 1; f.append(f"Multiple scripts ({len(py)})")
    return {"name": "Scripts", "score": min(s, 5), "max": 5, "weight": 0.5, "findings": f}


def score_conciseness(body: str) -> dict:
    """Body conciseness (0-5, weight 0.5)."""
    s, f, lines = 5, [], body.splitlines()
    headings = [re.match(r"^#{1,6}\s+(.+)", ln).group(1).strip()  # type: ignore[union-attr]
                for ln in lines if re.match(r"^#{1,6}\s+", ln)]
    counts: dict[str, int] = {}
    for h in headings:
        k = h.lower()
        counts[k] = counts.get(k, 0) + 1
    dups = {h: c for h, c in counts.items() if c > 1}
    if dups:
        s -= 2
        for h, c in dups.items():
            f.append(f"Duplicate heading: '{h}' appears {c} times")
    else:
        f.append("No duplicate headings")
    non_empty = [ln.strip() for ln in lines if ln.strip()]
    streak = 1
    for i in range(1, len(non_empty)):
        if non_empty[i] == non_empty[i - 1] and len(non_empty[i]) > 10:
            streak += 1
            if streak >= 3:
                s -= 3; f.append("Repeated consecutive paragraphs detected"); break
        else:
            streak = 1
    else:
        f.append("No repeated paragraphs")
    return {"name": "Conciseness", "score": max(s, 0), "max": 5, "weight": 0.5, "findings": f}


def _canonical_bonus(body: str) -> int:
    """Return +5 if a dedicated canonical terms/vocabulary section exists."""
    if re.search(r"^#+\s*(canonical\s+(terms?|vocab(ulary)?)|vocabulary)", body, re.I | re.M):
        return 5
    if re.search(r"\*\*Canonical\s+terms?\*\*", body, re.I):
        return 5
    return 0


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def audit_skill(path: str) -> dict:
    """Audit a single skill directory and return a scored report."""
    dp = Path(path).resolve()
    skill_md = dp / "SKILL.md"
    empty = {
        "skill": dp.name, "path": str(dp) + "/", "score": 0, "max": 100,
        "grade": "F", "dimensions": [], "bonus": 0, "patterns_found": [],
        "patterns_suggested": PATTERN_NAMES[:],
        "meta": {"lines": 0, "refs": 0, "scripts": 0},
    }
    if not skill_md.is_file():
        _warn(f"SKILL.md not found in {dp}")
        return {**empty, "error": "SKILL.md not found"}
    content = _read(skill_md)
    if content is None:
        _warn(f"Cannot read {skill_md}")
        return {**empty, "error": "Cannot read SKILL.md"}

    fm, body = parse_frontmatter(content)
    dims = [
        score_frontmatter(fm, dp.name),
        score_description(fm),
        score_dispatch_table(body),
        score_body_structure(body),
        score_pattern_coverage(body, dp),
        score_references(dp, body),
        score_critical_rules(body),
        score_scripts(dp),
        score_conciseness(body),
    ]
    tw = sum(d["score"] * d["weight"] for d in dims)
    mw = sum(d["max"] * d["weight"] for d in dims)
    norm = (tw / mw * 100) if mw > 0 else 0
    bonus = _canonical_bonus(body)
    final = min(round(norm), 100) + bonus
    pf = dims[4].pop("_found", [])
    ps = dims[4].pop("_suggested", [])
    rd = dp / "references"
    sd = dp / "scripts"
    return {
        "skill": dp.name, "path": str(dp) + "/", "score": final, "max": 100,
        "grade": _grade(final), "dimensions": dims, "bonus": bonus,
        "patterns_found": pf, "patterns_suggested": ps,
        "meta": {
            "lines": len(body.splitlines()),
            "refs": len(list(rd.glob("*"))) if rd.is_dir() else 0,
            "scripts": len(list(sd.glob("*.py"))) if sd.is_dir() else 0,
        },
    }


def audit_all(skills_dir: str) -> list[dict]:
    """Audit all skills and return comparative rankings sorted by score."""
    sp = Path(skills_dir).resolve()
    if not sp.is_dir():
        _warn(f"Skills directory not found: {sp}")
        return []
    results = [
        audit_skill(str(d)) for d in sorted(sp.iterdir())
        if d.is_dir() and (d / "SKILL.md").is_file()
    ]
    results.sort(key=lambda r: r["score"], reverse=True)
    return results


# ---------------------------------------------------------------------------
# Table formatters
# ---------------------------------------------------------------------------

def format_table(results: list[dict]) -> str:
    """Format audit results as a human-readable summary table."""
    out = ["Skill Quality Report", "=" * 20, ""]
    hdr = f"{'Skill':<22} {'Score':>7}  {'Grade':>5}  {'Lines':>5}  {'Refs':>4}  {'Scripts':>7}  {'Patterns':>8}"
    out.append(hdr)
    out.append("\u2500" * len(hdr))
    for r in results:
        m = r.get("meta", {})
        pc = len(r.get("patterns_found", []))
        b = f"+{r['bonus']}" if r.get("bonus", 0) > 0 else ""
        sc = f"{r['score']}/{r['max']}{b}"
        out.append(
            f"{r['skill']:<22} {sc:>7}  {r['grade']:>5}  "
            f"{m.get('lines', 0):>5}  {m.get('refs', 0):>4}  "
            f"{m.get('scripts', 0):>7}  {pc:>3}/13"
        )
    out.append("")
    out.append(f"Total skills audited: {len(results)}")
    if results:
        out.append(f"Average score: {sum(r['score'] for r in results) / len(results):.1f}")
    return "\n".join(out)


def format_single_table(result: dict) -> str:
    """Format a single audit result as a detailed table."""
    out = [f"Skill Audit: {result['skill']}", "=" * 40]
    out.append(f"Score: {result['score']}/{result['max']}  Grade: {result['grade']}")
    if result.get("bonus", 0) > 0:
        out.append(f"Bonus: +{result['bonus']} (canonical vocabulary)")
    out.append("")
    out.append(f"{'Dimension':<28} {'Score':>7}  {'Weight':>6}")
    out.append("\u2500" * 45)
    for d in result.get("dimensions", []):
        out.append(f"{d['name']:<28} {d['score']}/{d['max']:>3}  {d['weight']:>5.1f}x")
        for finding in d.get("findings", []):
            out.append(f"  {finding}")
    out.append("")
    m = result.get("meta", {})
    out.append(f"Lines: {m.get('lines', 0)}  Refs: {m.get('refs', 0)}  Scripts: {m.get('scripts', 0)}")
    pf = result.get("patterns_found", [])
    out.append(f"Patterns: {len(pf)}/13")
    if pf:
        out.append(f"  Found: {', '.join(pf)}")
    ps = result.get("patterns_suggested", [])
    if ps:
        out.append(f"  Suggested: {', '.join(ps[:5])}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Audit skill quality")
    parser.add_argument("path", nargs="?", help="Path to skill directory")
    parser.add_argument("--all", action="store_true", help="Audit all skills")
    parser.add_argument("--format", choices=["json", "table"], default="json",
                        dest="output_format")
    args = parser.parse_args()

    if not args.path and not args.all:
        parser.error("Provide a skill path or use --all")

    if args.all:
        script_dir = Path(__file__).resolve().parent
        skills_dir = script_dir.parent.parent  # skills/skill-creator/scripts -> skills/
        if not skills_dir.is_dir():
            skills_dir = Path.cwd() / "skills"
        results = audit_all(str(skills_dir))
        if args.output_format == "table":
            print(format_table(results))
        else:
            json.dump(results, sys.stdout, indent=2)
            sys.stdout.write("\n")
    else:
        result = audit_skill(args.path)
        if args.output_format == "table":
            print(format_single_table(result))
        else:
            json.dump(result, sys.stdout, indent=2)
            sys.stdout.write("\n")


if __name__ == "__main__":
    main()
