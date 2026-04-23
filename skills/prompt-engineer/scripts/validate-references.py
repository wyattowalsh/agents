#!/usr/bin/env python3
"""Validate prompt-engineer reference integrity.

Checks are intentionally structural rather than prose-perfect. The script guards
against stale invisible references, missing provider metadata, and dispatch rows
that have no eval coverage.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from typing import Any


REFERENCE_RE = re.compile(r"`(references/[^`]+\.md|scripts/[^`]+\.py)`")
URL_RE = re.compile(r"https?://[^\s`,|)]+")


PROVIDERS = {
    "Claude": ["Claude", "Anthropic"],
    "GPT": ["GPT", "OpenAI"],
    "Gemini": ["Gemini", "Google Gemini"],
    "Llama": ["Llama", "Meta"],
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def extract_reference_index(skill_text: str) -> set[str]:
    start = skill_text.find("## Reference File Index")
    if start == -1:
        return set()
    end = skill_text.find("\n## ", start + 1)
    block = skill_text[start:] if end == -1 else skill_text[start:end]
    return set(REFERENCE_RE.findall(block))


def markdown_cells(line: str) -> list[str]:
    stripped = line.strip()
    if not stripped.startswith("|") or not stripped.endswith("|"):
        return []
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def is_separator_cell(cell: str) -> bool:
    return bool(cell) and all(char in "-: " for char in cell)


def normalize_dispatch_cell(cell: str) -> str | None:
    raw = re.sub(r"`([^`]+)`", r"\1", cell).strip().lower()
    if not raw or raw == "$arguments" or is_separator_cell(raw):
        return None
    if raw.startswith("empty"):
        return "empty"
    if raw.startswith("raw prompt text"):
        return "raw"
    if raw.startswith("natural-language request"):
        return "natural"
    return raw.split()[0]


def extract_dispatch_terms(skill_text: str) -> set[str]:
    start = skill_text.find("## Dispatch")
    if start == -1:
        return set()
    end = skill_text.find("\n### ", start + 1)
    block = skill_text[start:] if end == -1 else skill_text[start:end]
    terms: set[str] = set()
    for line in block.splitlines():
        cells = markdown_cells(line)
        if len(cells) < 2:
            continue
        term = normalize_dispatch_cell(cells[0])
        if term:
            terms.add(term)
    return terms


def load_eval_prompts(skill_dir: Path) -> str:
    eval_dir = skill_dir / "evals"
    prompts: list[str] = []
    for eval_file in sorted(eval_dir.glob("*.json")):
        try:
            data = json.loads(eval_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            prompts.append(f"__JSON_ERROR__:{eval_file}:{exc}")
            continue
        for item in data.get("evals", []):
            prompts.append(str(item.get("id", "")))
            prompts.append(str(item.get("prompt", "")))
            prompts.append(" ".join(map(str, item.get("assertions", []))))
    return "\n".join(prompts).lower()


def provider_matrix_urls(text: str, aliases: list[str]) -> list[str]:
    start = text.find("## Provider Verification Matrix")
    if start == -1:
        return []
    end = text.find("\n## ", start + 1)
    block = text[start:] if end == -1 else text[start:end]
    for line in block.splitlines():
        cells = markdown_cells(line)
        if len(cells) < 2 or is_separator_cell(cells[0]):
            continue
        provider_cell = cells[0].lower()
        if any(alias.lower() in provider_cell for alias in aliases):
            return URL_RE.findall(cells[1])
    return []


def section_text(text: str, heading: re.Match[str]) -> str:
    start = heading.start()
    next_heading = re.search(r"^## ", text[start + 1 :], re.MULTILINE)
    if not next_heading:
        return text[start:]
    return text[start : start + 1 + next_heading.start()]


def check_provider_metadata(model_playbook: Path, today: dt.date) -> tuple[list[str], list[str], dict[str, Any]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = read_text(model_playbook)
    meta: dict[str, Any] = {"sections": []}

    if "Evidence class" not in text and "Evidence Classes" not in text:
        errors.append("model-playbooks.md must define evidence classes")
    if not URL_RE.search(text):
        errors.append("model-playbooks.md must include source URLs")

    for provider, aliases in PROVIDERS.items():
        heading = re.search(rf"^## .*{provider}.*Last verified:\s*(\d{{4}}-\d{{2}}-\d{{2}})", text, re.MULTILINE)
        if not heading:
            errors.append(f"Missing Last verified date for provider section: {provider}")
            continue
        verified = dt.date.fromisoformat(heading.group(1))
        age_days = (today - verified).days
        source_urls = set(provider_matrix_urls(text, aliases)) | set(URL_RE.findall(section_text(text, heading)))
        meta["sections"].append(
            {
                "provider": provider,
                "last_verified": verified.isoformat(),
                "age_days": age_days,
                "source_url_count": len(source_urls),
            }
        )
        if not source_urls:
            errors.append(f"Missing source URL for provider guidance: {provider}")
        if age_days > 90:
            warnings.append(f"{provider} provider guidance is {age_days} days old")
    return errors, warnings, meta


def validate(skill_dir: Path) -> dict[str, Any]:
    today = dt.date.today()
    skill_file = skill_dir / "SKILL.md"
    skill_text = read_text(skill_file)
    errors: list[str] = []
    warnings: list[str] = []

    if not skill_text:
        errors.append(f"Missing SKILL.md at {skill_file}")
        return {"ok": False, "errors": errors, "warnings": warnings}

    indexed = extract_reference_index(skill_text)
    if not indexed:
        errors.append("Reference File Index is missing or empty")

    disk_refs = {f"references/{p.name}" for p in (skill_dir / "references").glob("*.md")}
    disk_scripts = {f"scripts/{p.name}" for p in (skill_dir / "scripts").glob("*.py")}
    disk_targets = disk_refs | disk_scripts

    missing = sorted(indexed - disk_targets)
    orphan_refs = sorted(disk_refs - {p for p in indexed if p.startswith("references/")})
    for path in missing:
        errors.append(f"Indexed file does not exist: {path}")
    for path in orphan_refs:
        errors.append(f"Reference file missing from index: {path}")

    provider_errors, provider_warnings, provider_meta = check_provider_metadata(skill_dir / "references" / "model-playbooks.md", today)
    errors.extend(provider_errors)
    warnings.extend(provider_warnings)

    dispatch_terms = extract_dispatch_terms(skill_text)
    eval_text = load_eval_prompts(skill_dir)
    expected_eval_terms = {
        "craft": ["craft", "auto-craft"],
        "analyze": ["analyze", "auto-detect-existing"],
        "audit": ["audit"],
        "convert": ["convert"],
        "evaluate": ["evaluate"],
        "harden": ["harden"],
        "tool": ["tool"],
        "promptops": ["promptops"],
        "empty": ["empty-args", "/prompt-engineer"],
        "raw": ["auto-detect-existing", "<system>"],
        "natural": ["auto-craft", "natural-language"],
    }
    for term in sorted(dispatch_terms):
        probes = expected_eval_terms.get(term, [term])
        if not any(probe in eval_text for probe in probes):
            errors.append(f"Dispatch term lacks eval coverage: {term}")

    if "__JSON_ERROR__" in eval_text:
        errors.append("One or more eval JSON files failed to parse")

    return {
        "ok": not errors,
        "skill": skill_dir.name,
        "indexed_files": sorted(indexed),
        "dispatch_terms": sorted(dispatch_terms),
        "provider_metadata": provider_meta,
        "errors": errors,
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate prompt-engineer reference integrity")
    parser.add_argument("skill_path", type=Path, help="Path to skills/prompt-engineer")
    parser.add_argument("--format", choices=["json"], default="json")
    args = parser.parse_args()

    result = validate(args.skill_path)
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    if result["errors"]:
        print(f"validate-references: {len(result['errors'])} error(s)", file=sys.stderr)
    if result["warnings"]:
        print(f"validate-references: {len(result['warnings'])} warning(s)", file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
