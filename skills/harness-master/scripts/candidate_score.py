#!/usr/bin/env python3
"""Score normalized harness ecosystem candidate evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DIMENSIONS = [
    "authority",
    "programmatic_evidence",
    "harness_fit",
    "overlap_dry",
    "install_friction",
    "maintenance",
    "popularity",
    "security",
    "permissions_auth_risk",
    "validation_path",
    "rollback_path",
]


def _clamp(value: Any) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(3, number))


def _int_value(value: Any) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return int(value)
    if isinstance(value, str):
        normalized = value.strip().replace(",", "")
        multipliers = {"k": 1_000, "m": 1_000_000}
        suffix = normalized[-1:].lower()
        if suffix in multipliers:
            try:
                return int(float(normalized[:-1]) * multipliers[suffix])
            except ValueError:
                return 0
        try:
            return int(float(normalized))
        except ValueError:
            return 0
    return 0


def _truthy(candidate: dict[str, Any], *keys: str) -> bool:
    return any(bool(candidate.get(key)) for key in keys)


def _list(candidate: dict[str, Any], key: str) -> list[Any]:
    value = candidate.get(key, [])
    if isinstance(value, list):
        return value
    if value:
        return [value]
    return []


def _score_authority(candidate: dict[str, Any]) -> int:
    sources = {str(item).lower() for item in _list(candidate, "evidence_sources")}
    if _truthy(candidate, "official", "local_registry_match") or sources & {"official", "local-registry", "primary"}:
        return 3
    if sources & {"mcp-registry", "skills-sh", "npm", "pypi", "open-vsx", "docker-mcp-catalog", "registry"}:
        return 2
    if sources & {"github", "package", "security"}:
        return 1
    return 0


def _score_programmatic(candidate: dict[str, Any]) -> int:
    fields = _list(candidate, "evidence_fields")
    sources = _list(candidate, "programmatic_sources")
    if len(sources) >= 3 or len(fields) >= 8:
        return 3
    if len(sources) >= 2 or len(fields) >= 4 or candidate.get("machine_readable"):
        return 2
    if sources or fields:
        return 1
    return 0


def _score_harness_fit(candidate: dict[str, Any], harness: str | None) -> int:
    supported = {str(item) for item in _list(candidate, "supported_harnesses")}
    if candidate.get("harness_fit") is not None:
        return _clamp(candidate["harness_fit"])
    if "all" in supported:
        return 3
    if harness and harness in supported:
        return 3
    if supported:
        return 2
    return 0


def _score_security(candidate: dict[str, Any]) -> int:
    if _truthy(candidate, "known_malware", "active_exploit", "unpatched_critical_vulnerability"):
        return 0
    if _truthy(candidate, "osv_clear", "security_reviewed", "signed_release"):
        return 3
    if candidate.get("vulnerabilities") in ([], 0, None) and _truthy(candidate, "package_metadata"):
        return 2
    if candidate.get("vulnerabilities"):
        return 1
    return 1


def _score_permissions(candidate: dict[str, Any]) -> int:
    if _truthy(candidate, "credential_proxy", "auth_bridge", "offensive_tooling", "broad_destructive_tools"):
        return 0
    if _truthy(candidate, "broad_filesystem", "broad_network", "shell_exec"):
        return 1
    if _truthy(candidate, "scoped_permissions", "no_auth_required", "read_only"):
        return 3
    return 2


def _infer_scores(candidate: dict[str, Any], harness: str | None) -> dict[str, int]:
    explicit = candidate.get("scores", {})
    scores: dict[str, int] = {}
    for dimension in DIMENSIONS:
        if dimension in explicit:
            scores[dimension] = _clamp(explicit[dimension])
    scores.setdefault("authority", _score_authority(candidate))
    scores.setdefault("programmatic_evidence", _score_programmatic(candidate))
    scores.setdefault("harness_fit", _score_harness_fit(candidate, harness))
    scores.setdefault(
        "overlap_dry", 1 if candidate.get("duplicates_existing_owner") else 3 if candidate.get("canonical_home") else 2
    )
    scores.setdefault(
        "install_friction",
        1
        if _truthy(candidate, "requires_manual_ui", "requires_compilation")
        else 2
        if candidate.get("auth_env")
        else 3,
    )
    scores.setdefault(
        "maintenance",
        3
        if _truthy(candidate, "recent_release", "active_maintainers")
        else 2
        if candidate.get("pushed_recently")
        else 1,
    )
    stars = _int_value(candidate.get("stars", 0))
    scores.setdefault("popularity", 3 if stars >= 1000 else 2 if stars >= 100 else 1)
    scores.setdefault("security", _score_security(candidate))
    scores.setdefault("permissions_auth_risk", _score_permissions(candidate))
    scores.setdefault(
        "validation_path", 3 if candidate.get("validation_fixtures") else 2 if candidate.get("validation_plan") else 0
    )
    scores.setdefault(
        "rollback_path", 3 if candidate.get("rollback_tested") else 2 if candidate.get("rollback_plan") else 0
    )
    return scores


def _community_only(candidate: dict[str, Any]) -> bool:
    sources = {str(item).lower() for item in _list(candidate, "evidence_sources")}
    return bool(sources) and sources <= {"community", "reddit", "hn", "blog", "forum", "social"}


def _verdict(candidate: dict[str, Any], scores: dict[str, int]) -> tuple[str, str]:
    total = sum(scores.values())
    if _truthy(candidate, "credential_proxy", "auth_bridge", "offensive_tooling", "broad_destructive_tools"):
        return "quarantine", "quarantine"
    if _community_only(candidate):
        return "avoid", "experimental"
    if scores["security"] == 0 or scores["permissions_auth_risk"] == 0:
        return "quarantine", "quarantine"
    if candidate.get("docs_only"):
        return "docs-only", "planned-research-backed"
    if candidate.get("global_only"):
        return "global-only", "planned-research-backed"
    if scores["validation_path"] == 3 and scores["rollback_path"] >= 2 and total >= 27:
        return "adopt", "validated"
    if candidate.get("local_registry_match") and scores["validation_path"] < 3:
        return "inspect", "repo-present-validation-required"
    if total >= 23 and scores["authority"] >= 2 and scores["programmatic_evidence"] >= 2:
        return "inspect", "planned-research-backed"
    if total >= 17:
        return "inspect", "experimental"
    return "avoid", "experimental"


def _load_candidate(path: str) -> dict[str, Any]:
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", nargs="?", default="-", help="Candidate JSON path, or stdin when omitted/-")
    parser.add_argument("--harness", help="Target harness for fit scoring.")
    parser.add_argument("--json", action="store_true", help="Emit JSON.")
    args = parser.parse_args(argv)

    candidate = _load_candidate(args.candidate)
    scores = _infer_scores(candidate, args.harness)
    verdict, support_tier = _verdict(candidate, scores)
    payload = {
        "candidate": candidate.get("name") or candidate.get("url") or candidate.get("package") or "unknown",
        "verdict": verdict,
        "support_tier": support_tier,
        "total": sum(scores.values()),
        "max_total": len(DIMENSIONS) * 3,
        "scores": scores,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"candidate: {payload['candidate']}")
        print(f"verdict: {verdict}")
        print(f"support_tier: {support_tier}")
        print(f"score: {payload['total']}/{payload['max_total']}")
        for key in DIMENSIONS:
            print(f"{key}: {scores[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
