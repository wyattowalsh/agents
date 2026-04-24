#!/usr/bin/env python3
"""Deduplicate sources across multiple subagent research results.

Reads a JSON array of finding arrays (one per subagent) from stdin,
deduplicates by claim similarity, merges evidence chains, and outputs
a unified findings array.

Usage:
  cat subagent-results.json | python source-deduplicator.py
  cat subagent-results.json | python source-deduplicator.py --verbose
  cat subagent-results.json | python source-deduplicator.py --threshold 0.9
"""
import argparse
import json
import re
import string
import sys
from typing import Any
from urllib.parse import urlparse


def normalize_claim(claim: str) -> str:
    """Normalize a claim for comparison: lowercase, strip punctuation, collapse whitespace."""
    text = claim.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def jaccard_similarity(a: str, b: str) -> float:
    """Compute Jaccard similarity between two normalized claim strings."""
    words_a = set(a.split())
    words_b = set(b.split())
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def merge_confidence(confidences: list[float]) -> float:
    """Merge confidences: c_merged = 1 - (1-c1)(1-c2)...(1-cN), capped at 0.99."""
    if not confidences:
        return 0.0
    product = 1.0
    for c in confidences:
        product *= (1.0 - max(0.0, min(1.0, c)))
    return min(0.99, round(1.0 - product, 4))


def normalize_evidence(finding: dict[str, Any]) -> list[dict[str, Any]]:
    """Return canonical evidence[] items, accepting legacy top-level source fields."""
    raw_evidence = finding.get("evidence", [])
    evidence: list[dict[str, Any]] = []
    if isinstance(raw_evidence, list):
        evidence = [dict(e) for e in raw_evidence if isinstance(e, dict)]

    legacy_url = finding.get("source_url") or finding.get("url")
    legacy_tool = finding.get("source_tool") or finding.get("tool")
    legacy_excerpt = finding.get("excerpt")
    if legacy_url and not evidence:
        evidence.append({
            "tool": legacy_tool or "unknown",
            "url": legacy_url,
            "timestamp": finding.get("timestamp", "N/A"),
            "excerpt": legacy_excerpt or "",
        })

    normalized: list[dict[str, Any]] = []
    for ev in evidence:
        item = dict(ev)
        if "source_tool" in item and "tool" not in item:
            item["tool"] = item.pop("source_tool")
        if "source_url" in item and "url" not in item:
            item["url"] = item.pop("source_url")
        item.setdefault("tool", "unknown")
        item.setdefault("url", "N/A")
        item.setdefault("timestamp", "N/A")
        item.setdefault("excerpt", "")
        item.setdefault("independent", True)
        normalized.append(item)
    return normalized


def get_confidence(finding: dict[str, Any]) -> float | None:
    """Return canonical confidence, accepting legacy confidence_raw."""
    conf = finding.get("confidence", finding.get("confidence_raw"))
    if isinstance(conf, (int, float)):
        return max(0.0, min(1.0, float(conf)))
    return None


def get_evidence_domain(evidence: dict[str, Any]) -> str | None:
    """Extract domain from an evidence item's URL."""
    url = evidence.get("url", "")
    if not url:
        return None
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower() if parsed.netloc else None
    except Exception:
        return None


def flag_same_domain_sources(evidence_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Flag evidence items that share a domain as potentially non-independent."""
    domain_counts: dict[str, int] = {}
    for ev in evidence_list:
        domain = get_evidence_domain(ev)
        if domain:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    duplicated_domains = {d for d, c in domain_counts.items() if c > 1}

    flagged: list[dict[str, Any]] = []
    for ev in evidence_list:
        ev_copy = dict(ev)
        domain = get_evidence_domain(ev)
        if domain and domain in duplicated_domains:
            ev_copy["same_domain_warning"] = True
        flagged.append(ev_copy)
    return flagged


def deduplicate_evidence(evidence_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate evidence items based on URL."""
    seen_urls: set[str] = set()
    unique: list[dict[str, Any]] = []
    for ev in evidence_list:
        url = ev.get("url", "")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        unique.append(ev)
    return unique


def independent_source_count(evidence_list: list[dict[str, Any]]) -> int:
    """Count distinct independent URLs, falling back to anonymous evidence count."""
    urls: set[str] = set()
    anonymous = 0
    for ev in evidence_list:
        if ev.get("independent") is False:
            continue
        url = str(ev.get("url") or "").strip()
        if url:
            urls.add(url)
        else:
            anonymous += 1
    return len(urls) + anonymous


def normalize_cross_validation_status(status: Any) -> str:
    """Normalize descriptive cross-validation text to the canonical status."""
    text = str(status or "unknown").lower()
    if "contradict" in text:
        return "contradicts"
    if "agree" in text:
        return "agrees"
    if "partial" in text:
        return "partial"
    if "unverified" in text:
        return "unverified"
    return "unknown"


def determine_cross_validation(findings: list[dict[str, Any]]) -> str:
    """Determine cross-validation status from merged findings."""
    statuses = [normalize_cross_validation_status(f.get("cross_validation", "unknown")) for f in findings]
    if "contradicts" in statuses:
        return "partial"
    non_unknown = [s for s in statuses if s != "unknown"]
    if non_unknown and all(s == "agrees" for s in non_unknown):
        return "agrees"
    if non_unknown:
        return "partial"
    if len(findings) > 1:
        return "partial"
    return "unknown"


def apply_confidence_caps(confidence: float, evidence: list[dict[str, Any]], cross_validation: str) -> float:
    """Apply hard scoring caps from the research confidence rubric."""
    independent_count = independent_source_count(evidence)
    status = normalize_cross_validation_status(cross_validation)
    capped = confidence
    if independent_count == 0:
        capped = min(capped, 0.29)
    elif independent_count == 1:
        capped = min(capped, 0.6)
    elif status != "agrees":
        capped = min(capped, 0.69)
    return round(capped, 4)


def deduplicate(
    subagent_results: list[list[dict[str, Any]]],
    threshold: float,
    verbose: bool,
) -> list[dict[str, Any]]:
    """Deduplicate findings across subagent results."""
    # Flatten all findings
    all_findings: list[dict[str, Any]] = []
    for result_set in subagent_results:
        if isinstance(result_set, list):
            all_findings.extend(result_set)
        elif isinstance(result_set, dict):
            all_findings.append(result_set)

    input_count = len(all_findings)

    if not all_findings:
        if verbose:
            print("No findings to deduplicate.", file=sys.stderr)
        return []

    # Group by claim similarity
    groups: list[list[dict[str, Any]]] = []
    used: list[bool] = [False] * len(all_findings)
    normalized_claims = [normalize_claim(f.get("claim", "")) for f in all_findings]

    for i in range(len(all_findings)):
        if used[i]:
            continue
        group = [all_findings[i]]
        used[i] = True

        for j in range(i + 1, len(all_findings)):
            if used[j]:
                continue
            if threshold >= 1.0:
                # Exact match mode
                if normalized_claims[i] == normalized_claims[j]:
                    group.append(all_findings[j])
                    used[j] = True
            else:
                # Similarity threshold mode
                sim = jaccard_similarity(normalized_claims[i], normalized_claims[j])
                if sim >= threshold:
                    group.append(all_findings[j])
                    used[j] = True

        groups.append(group)

    # Merge each group into a single finding
    merged_findings: list[dict[str, Any]] = []
    duplicates_merged = 0

    for group in groups:
        if len(group) == 1:
            finding = dict(group[0])
            evidence = normalize_evidence(finding)
            cv = str(finding.get("cross_validation", "unknown"))
            finding["evidence"] = flag_same_domain_sources(evidence)
            finding["source_count"] = len(finding["evidence"])
            finding["independent_source_count"] = independent_source_count(finding["evidence"])
            conf = get_confidence(finding)
            if conf is not None:
                finding["confidence"] = apply_confidence_caps(conf, finding["evidence"], cv)
            finding.pop("confidence_raw", None)
            merged_findings.append(finding)
            continue

        duplicates_merged += len(group) - 1

        # Take the longest claim as representative
        primary = max(group, key=lambda f: len(f.get("claim", "")))
        claim = primary.get("claim", "")

        # Merge evidence
        all_evidence: list[dict[str, Any]] = []
        for f in group:
            all_evidence.extend(normalize_evidence(f))
        all_evidence = deduplicate_evidence(all_evidence)
        all_evidence = flag_same_domain_sources(all_evidence)

        # Merge confidence
        confidences = [conf for f in group if (conf := get_confidence(f)) is not None]
        merged_conf = merge_confidence(confidences)

        # Union bias markers and gaps
        bias_markers: list[str] = []
        gaps: list[str] = []
        for f in group:
            for bm in f.get("bias_markers", []):
                if bm not in bias_markers:
                    bias_markers.append(bm)
            for gap in f.get("gaps", []):
                if gap not in gaps:
                    gaps.append(gap)

        # Cross-validation
        cv = determine_cross_validation(group)
        merged_conf = apply_confidence_caps(merged_conf, all_evidence, cv)

        merged_findings.append({
            "claim": claim,
            "confidence": merged_conf,
            "evidence": all_evidence,
            "cross_validation": cv,
            "bias_markers": bias_markers,
            "gaps": gaps,
            "source_count": len(all_evidence),
            "independent_source_count": independent_source_count(all_evidence),
            "merged_from": len(group),
        })

    # Sort by confidence descending
    merged_findings.sort(key=lambda f: f.get("confidence", 0.0), reverse=True)

    if verbose:
        print(
            f"Dedup stats: {input_count} input findings -> "
            f"{len(merged_findings)} output findings, "
            f"{duplicates_merged} duplicates merged",
            file=sys.stderr,
        )

    return merged_findings


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Deduplicate sources across multiple subagent research results. "
        "Reads a JSON array of finding arrays from stdin, merges evidence chains "
        "for duplicate claims, and outputs unified findings.",
    )
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="Print dedup statistics to stderr.",
    )
    ap.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Similarity threshold for claim matching (0.0-1.0). "
        "Default 1.0 = exact match on normalized text. "
        "Lower values use Jaccard word similarity.",
    )
    args = ap.parse_args()

    if args.threshold < 0.0 or args.threshold > 1.0:
        print("Error: --threshold must be between 0.0 and 1.0", file=sys.stderr)
        sys.exit(1)

    raw = sys.stdin.read()
    if not raw or not raw.strip():
        print("[]")
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON input: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, list):
        print("Error: input must be a JSON array of finding arrays.", file=sys.stderr)
        sys.exit(1)

    result = deduplicate(data, args.threshold, args.verbose)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
