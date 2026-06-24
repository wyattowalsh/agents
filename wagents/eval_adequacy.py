"""Structural E3/E4 eval adequacy assessment for skills.

Provides risk tier inference from skill metadata/keywords and detection of
E3 (explicit/implicit/negative/refusal) and E4 (approval, boundary, refusal,
no-mutation, credential/network, destructive) signals from eval manifests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from wagents.context import get_repo_root
from wagents.parsing import parse_frontmatter

# Risk tier keywords (checked in frontmatter + body + tools + name)
_R4_KEYWORDS = {
    "gmail",
    "email-whiz",
    "gmail_delete",
    "batch_delete",
    "gmail_send",
    "send_email",
    "destructive",
    "delete filter",
    "permanent delete",
    "type delete",
    "broad delete",
}
_R3_KEYWORDS = {
    "chrome-devtools",
    "devtools",
    "browser",
    "mcp-creator",
    "opencode-ensemble",
    "openspec-workflow",
    "security-scanner",
    "infrastructure-coder",
    "devops-engineer",
    "reasoning-router",
    "mcp server",
    "execute shell",
    "network",
    "external call",
    "harness",
    "live mutation",
}
_R2_KEYWORDS = {
    "write file",
    "create file",
    "edit ",
    "mutate",
    "generate code",
    "apply patch",
}
_R1_KEYWORDS = {
    "read-only",
    "analyze",
    "scan",
    "audit",
    "review",
    "detect",
}

# E3 signals (prefix/phrase, avoid "no-explicit" substr etc)
_E3_EXPLICIT = {"explicit-", "explicit ", "explicit invocation"}
_E3_IMPLICIT = {
    "implicit",
    "implicit trigger",
    "natural language",
    "without slash",
    "generic request activates",
}
_E3_NEGATIVE = {
    "negative",
    "negative control",
    "negative-",
    "does not auto-activate",
    "does not claim",
    "does not treat",
    "handoff to",
    "not auto-activate",
}
_E3_REFUSAL = {"refus", "refusal", "do not", "never call", "forbidden unless", "refuses to"}

# E4 boundary signals
_E4_APPROVAL = {"approval", "approve", "confirm", "confirmation", "gate", "requires .* approval", "before write"}
_E4_NO_MUTATION = {"no mutation", "no write", "read-only", "does not execute", "without confirmation", "plan only"}
_E4_DESTRUCTIVE = {"destructive", "delete", "destroy", "permanent", "cleanup that deletes"}
_E4_BOUNDARY = {
    "boundary",
    "out of scope",
    "not for",
    "untrusted",
    "credential",
    "secret",
    "network boundary",
    "no config change",
}
_E4_CRED_NET = {"credential", "secret", "token", "password", "api key", "network", "mcp.json", "launch config"}


def _read_skill_text(skill_dir: Path) -> tuple[dict[str, Any], str]:
    """Return (frontmatter, body) for SKILL.md or empty."""
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        return {}, ""
    try:
        content = skill_file.read_text(encoding="utf-8", errors="replace")
        if content.startswith("---\n"):
            return parse_frontmatter(content)
        return {}, content
    except Exception:
        return {}, ""


def _infer_risk_tier(skill_dir: Path) -> str:
    """Infer R0-R4 from skill name, frontmatter, description, allowed-tools, body."""
    name = skill_dir.name.lower()
    fm, body = _read_skill_text(skill_dir)
    allowed = str(fm.get("allowed-tools", "") or "").lower()
    desc = str(fm.get("description", "") or "").lower()
    combined = f"{name} {allowed} {desc} {body.lower()}"

    # Name-based hard rules for known high-risk
    r4_names = {"email-whiz"}
    r3_names = {
        "chrome-devtools",
        "chrome-devtools-a11y-debugging",
        "chrome-devtools-cli",
        "chrome-devtools-debug-optimize-lcp",
        "chrome-devtools-memory-leak-debugging",
        "chrome-devtools-troubleshooting",
        "mcp-creator",
        "opencode-ensemble",
        "openspec-workflow",
        "security-scanner",
        "infrastructure-coder",
        "devops-engineer",
        "reasoning-router",
    }
    if name in r4_names or any(k in combined for k in _R4_KEYWORDS):
        return "R4"
    if name in r3_names or any(k in combined for k in _R3_KEYWORDS):
        return "R3"
    if any(k in combined for k in _R2_KEYWORDS) or "Write" in str(fm.get("allowed-tools", "")):
        return "R2"
    if any(k in combined for k in _R1_KEYWORDS) or "read" in allowed:
        return "R1"
    # Heuristic: presence of write-like or tools implies at least R2
    if "write" in allowed or "grep" in allowed or "read" in allowed:
        return "R2"
    return "R0"


def _collect_eval_text(e: dict[str, Any]) -> str:
    """Concat id + prompt + expected + assertions for keyword scan."""
    iid = str(e.get("id", "") or "").lower()
    prompt = str(e.get("prompt", "") or "").lower()
    eo = str(e.get("expected_output", "") or "").lower()
    asserts = " ".join(str(a or "").lower() for a in e.get("assertions", []) or [])
    return f"{iid} {prompt} {eo} {asserts}"


def _detect_e3_cases(evals: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Detect presence of E3 case types by keyword in eval entries."""
    buckets: dict[str, list[str]] = {"explicit": [], "implicit": [], "negative": [], "refusal": []}
    for e in evals or []:
        if not isinstance(e, dict):
            continue
        txt = _collect_eval_text(e)
        iid = str(e.get("id", "") or "")
        pid = str(e.get("prompt", "") or "")[:40]
        # Prefer id-based buckets first (negative/refusal/destructive are strong signals even if text mentions "explicit")
        if iid.startswith("negative-") or any(k in txt for k in _E3_NEGATIVE):
            buckets["negative"].append(iid or pid)
        if iid.startswith(("refusal-", "destructive-")) or "refus" in iid or any(k in txt for k in _E3_REFUSAL):
            buckets["refusal"].append(iid or pid)
        if iid.startswith("implicit-") or any(k in txt for k in _E3_IMPLICIT):
            buckets["implicit"].append(iid or pid)
        # Explicit only if id-prefixed or phrase and NOT already classified as negative/refusal style (avoid "need explicit" phrases in neg tests)
        is_neg_ref = iid.startswith(("negative-", "refusal-", "destructive-")) or any(x in iid for x in ("negative", "refus", "destructive", "boundary"))
        if (iid.startswith("explicit-") or iid == "explicit" or any(k in txt for k in _E3_EXPLICIT)) and not is_neg_ref:
            buckets["explicit"].append(iid or pid)
        # Fallback implicit for non-/ prompts that look like natural activation (only if no negative/refusal id)
        if not any(iid.startswith(p) for p in ("negative-", "refusal-", "destructive-", "boundary-", "explicit-")) and not (pid or "").strip().startswith("/") and any(k in txt for k in ("activate", "trigger", "natural")):
            if iid not in buckets["implicit"]:
                buckets["implicit"].append(iid or pid)
    # Dedup preserve order
    for k in buckets:
        seen: set[str] = set()
        uniq = []
        for v in buckets[k]:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        buckets[k] = uniq[:5]  # cap samples
    return buckets


def _has_full_e3(e3: dict[str, list[str]]) -> bool:
    """E3 requires at least one of each: explicit, implicit, negative, refusal."""
    return all(len(e3.get(k, [])) >= 1 for k in ("explicit", "implicit", "negative", "refusal"))


def _detect_e4_signals(evals: list[dict[str, Any]]) -> list[str]:
    """Collect E4 boundary signals found across evals."""
    signals: list[str] = []
    all_txt = " ".join(_collect_eval_text(e) for e in evals or [])
    if any(k in all_txt for k in _E4_APPROVAL):
        signals.append("approval-gate")
    if any(k in all_txt for k in _E4_NO_MUTATION):
        signals.append("no-mutation-fallback")
    if any(k in all_txt for k in _E4_DESTRUCTIVE):
        signals.append("destructive-refusal")
    if any(k in all_txt for k in _E4_BOUNDARY):
        signals.append("boundary-handling")
    if any(k in all_txt for k in _E4_CRED_NET):
        signals.append("credential-network-boundary")
    # Also check individual for specific ids that are strong signals
    for e in evals or []:
        iid = str(e.get("id", "")).lower()
        txt = _collect_eval_text(e)
        if "approval" in iid or "gate" in iid or "confirm" in iid:
            if "approval-gate" not in signals:
                signals.append("approval-gate")
        if "boundary" in iid or "refusal" in iid:
            if "boundary-handling" not in signals:
                signals.append("boundary-handling")
        if ("destructive" in txt or "delete" in txt) and "destructive" in iid:
            if "destructive-refusal" not in signals:
                signals.append("destructive-refusal")
    return sorted(set(signals))


def _has_e4_signals(e4: list[str]) -> bool:
    return len(e4) >= 1


def assess_eval_adequacy(skill_dir: Path | str) -> dict[str, Any]:
    """Assess one skill dir for risk tier, E3/E4 coverage signals.

    Returns dict with keys: skill, risk_tier, eval_count, e3_cases, e4_signals,
    has_e3, has_e4, adequacy, needs_e4.
    """
    skill_dir = Path(skill_dir).resolve()
    name = skill_dir.name
    evals_path = skill_dir / "evals" / "evals.json"
    evals: list[dict[str, Any]] = []
    if evals_path.is_file():
        try:
            data = json.loads(evals_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("evals"), list):
                evals = [e for e in data["evals"] if isinstance(e, dict)]
        except (json.JSONDecodeError, OSError):
            evals = []

    risk = _infer_risk_tier(skill_dir)
    e3_cases = _detect_e3_cases(evals)
    e4_signals = _detect_e4_signals(evals)
    has_e3 = _has_full_e3(e3_cases)
    has_e4 = _has_e4_signals(e4_signals)

    adequacy = "E2"
    if has_e3:
        adequacy = "E3"
    if has_e4:
        adequacy = "E4"

    needs_e4 = risk in ("R3", "R4") and not has_e4

    return {
        "skill": name,
        "risk_tier": risk,
        "eval_count": len(evals),
        "e3_cases": e3_cases,
        "e4_signals": e4_signals,
        "has_e3": has_e3,
        "has_e4": has_e4,
        "adequacy": adequacy,
        "needs_e4": needs_e4,
    }


def build_adequacy_report() -> dict[str, Any]:
    """Build adequacy report for all skills in the repo."""
    try:
        root = get_repo_root()
    except Exception:
        root = Path.cwd()
    skills_dir = root / "skills"
    skills: list[dict[str, Any]] = []
    if not skills_dir.is_dir():
        return {"count": 0, "skills": skills, "summary": {"R4": 0, "R3": 0, "needs_e4": 0}}

    for entry in sorted(skills_dir.iterdir()):
        if entry.is_dir() and (entry / "SKILL.md").is_file():
            rep = assess_eval_adequacy(entry)
            skills.append(rep)

    by_risk: dict[str, int] = {}
    needs = 0
    for s in skills:
        rt = s["risk_tier"]
        by_risk[rt] = by_risk.get(rt, 0) + 1
        if s["needs_e4"]:
            needs += 1

    return {
        "count": len(skills),
        "skills": skills,
        "summary": {
            "by_risk": by_risk,
            "needs_e4": needs,
            "r3_r4_with_e4": sum(1 for s in skills if s["risk_tier"] in ("R3", "R4") and s["has_e4"]),
        },
    }


def filter_high_risk(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Return only the high-risk skill reports."""
    high_names = {
        "email-whiz",
        "chrome-devtools",
        "chrome-devtools-a11y-debugging",
        "chrome-devtools-cli",
        "chrome-devtools-debug-optimize-lcp",
        "chrome-devtools-memory-leak-debugging",
        "chrome-devtools-troubleshooting",
        "mcp-creator",
        "opencode-ensemble",
        "openspec-workflow",
        "security-scanner",
        "infrastructure-coder",
        "devops-engineer",
        "reasoning-router",
    }
    return [s for s in report.get("skills", []) if s["skill"] in high_names]
