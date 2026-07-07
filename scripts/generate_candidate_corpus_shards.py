#!/usr/bin/env python3
"""Process the candidate-corpus-jul2026 intake manifest.

This script is deliberately conservative: it gathers public Git metadata and
repo-local overlap evidence, but it does not install, execute, vendor, or enable
candidate code.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
RAW_URLS = MANIFEST_DIR / "raw-urls.txt"
NORMALIZED = MANIFEST_DIR / "normalized-urls.json"
RECORDS_DIR = MANIFEST_DIR / "records"
EXPECTED_RAW_COUNT = 293
EXPECTED_UNIQUE_COUNT = 289
MICRO_WAVE_SIZE = 49
MAX_WORKERS = 12

CATALOG_DIR = ROOT / "docs" / "src" / "authoring" / "skills"
MCP_REGISTRY = ROOT / "config" / "mcp-registry.json"
PLUGIN_REGISTRY = ROOT / "config" / "plugin-extension-registry.json"
CATALOG_ENTRY_PREFIX = "candidate-corpus"
CATALOG_ENTRY_MARKER = "GENERATED-CANDIDATE-CORPUS-JUL2026"

DOCS_SURFACES = [
    "README",
    "catalog-authoring",
    "catalog-generated",
    "skill-research",
    "mcp-tools",
    "auth-matrix",
    "install-docs",
    "openspec",
    "runbooks",
    "decision-log",
    "changelog",
    "reports",
    "agents-instructions",
    "generated-drift",
]

CLUSTERS = [
    ("CJ01", "exact-duplicates", ["terraform-skill", "ios-simulator-skill", "solid-skills", "unslop"]),
    ("CJ02", "malformed-inaccessible", ["skills-"]),
    ("CJ03", "official-vendor-platform", ["cloudflare", "wordpress", "supabase", "google", "huggingface", "elastic"]),
    ("CJ04", "apple-ios-macos-swift", ["swift", "ios", "app-store", "app-intents", "widgets"]),
    ("CJ05", "frontend-auth-web-quality", ["react", "typescript", "solid", "auth", "frontend", "web-quality"]),
    ("CJ06", "design-media-generative", ["design", "logo", "image", "figma", "visual", "motion"]),
    ("CJ07", "charts-diagrams-slides-cad-webgpu", ["chart", "diagram", "ppt", "cad", "webgpu", "mermaid"]),
    ("CJ08", "cloud-iac-devops-security", ["aws", "terraform", "cloud", "security", "devops"]),
    ("CJ09", "mcp-tools-plugins", ["mcp", "plugin", "inspector"]),
    ("CJ10", "openspec", ["openspec", "spec"]),
    ("CJ11", "composiohq", ["composiohq/awesome-codex-skills"]),
    ("CJ12", "pedronauck-curated", ["pedronauck/skills/tree/main/skills/curated"]),
    ("CJ13", "pedronauck-marketing", ["pedronauck/skills/tree/main/skills/marketing"]),
    ("CJ14", "pedronauck-community", ["pedronauck/skills/tree/main/skills/community"]),
    ("CJ15", "research-academic-papers", ["research", "academic", "paper", "zotero", "notebooklm"]),
    ("CJ16", "legal-finance-economics", ["legal", "finance", "econ", "buffett", "yahoo-finance"]),
    ("CJ17", "seo-aso-geo-gtm", ["seo", "aso", "geo", "gtm"]),
    ("CJ18", "sales-marketing-outbound", ["sales", "marketing", "outbound", "affiliate", "ads"]),
    ("CJ19", "pm-product-content-writing", ["pm", "product", "content", "writing", "novel"]),
    ("CJ20", "obsidian-docs-workflow", ["obsidian", "docs", "workflow", "readme"]),
]

HIGH_RISK = {
    "affiliate",
    "ads",
    "agent-reach",
    "app-store-connect",
    "aso",
    "buffett",
    "coldoutbound",
    "competitive-ads",
    "finance",
    "gtm",
    "legal",
    "sales",
    "scraping",
    "seo",
    "social-push",
    "upwork-autopilot",
    "video-downloader",
    "yahoo-finance",
}
QUARANTINE = {"competitive-ads-extractor", "social-push", "upwork-autopilot", "video-downloader"}

RAW_RESEARCH_LEAF_CHECKS = [
    ("URL", "R", "Preserve URL parse details.", "url_parse_packet"),
    ("LIVE", "R", "Verify upstream exists or record inaccessible/malformed evidence.", "git_remote_evidence"),
    ("HEAD", "R", "Record default branch and inspected commit SHA.", "commit_sha"),
    ("README", "R", "Read README and primary docs.", "readme_docs_summary"),
    ("LICENSE", "R", "Inspect license file and package license metadata.", "spdx_or_blocker"),
    ("PKG", "R", "Inspect package metadata, dependencies, scripts, hooks, and entrypoints.", "package_packet"),
    ("SKILL", "R", "Determine whether it is an agentskills-compatible skill.", "skill_compatibility_packet"),
    ("MCP", "R", "Determine whether it is an MCP server or MCP-adjacent tool.", "mcp_routing_packet"),
    ("PLUGIN", "R", "Determine whether it is an editor or harness plugin.", "plugin_routing_packet"),
    (
        "AGENT",
        "R",
        "Determine whether it includes agent definitions or instruction prompts.",
        "agent_instruction_packet",
    ),
    ("CLI", "R", "Determine whether it is a CLI/tool/library and whether a wrapper is justified.", "tool_packet"),
    ("AUTH", "R/E", "Extract env vars, credentials, OAuth scopes, and setup docs.", "auth_matrix_row"),
    ("SEC", "R/E", "Review scripts, network calls, eval/exec, filesystem writes, and telemetry.", "security_packet"),
    ("TOS", "R/E", "Review platform, compliance, anti-abuse, and sensitive-domain boundaries.", "compliance_packet"),
    (
        "IDIO",
        "R",
        "Capture malformed URLs, monorepo paths, runtimes, assets, and local-only behavior.",
        "idiosyncrasy_packet",
    ),
    ("DEDUPE", "R", "Compare duplicates, forks, official alternatives, and existing repo surfaces.", "dedupe_packet"),
    ("ROUTE", "R", "Select the target integration surface or blocker.", "routing_decision"),
    ("PROMOTE", "S/M", "Apply approved repo mutation or record blocker.", "changed_files_or_blocker"),
    ("VAL", "S/R", "Run target-specific validation.", "validation_result"),
]

UNIQUE_SYNTHESIS_LEAF_CHECKS = [
    ("RAW-MAP", "R", "List all raw entries that map to this normalized target.", "raw_index_list"),
    ("CANON", "R/E", "Choose canonical upstream among duplicates or forks.", "canonical_source"),
    ("SURFACE", "R", "Merge raw-lane routing into one terminal surface decision.", "terminal_decision"),
    ("ATTRIB", "R", "Consolidate license and attribution notes.", "attribution_note"),
    ("AUTH", "R/E", "Consolidate auth requirements and setup links.", "auth_guide"),
    ("INSTALL", "S/M/E", "Show exact install/apply command if live install is eligible.", "install_command_packet"),
    ("DOCS", "S/M", "Update docs-steward surfaces for the final decision.", "docs_update"),
    ("VAL", "S/R", "Validate generated rows, config, docs, and install preview/apply result.", "validation_result"),
]

RESEARCH_PACKET_FIELDS = [
    "raw_index",
    "raw_url",
    "normalized_url",
    "subresource",
    "source_name",
    "upstream_status",
    "inspected_commit_sha",
    "latest_release_or_commit_date",
    "license",
    "artifact_types_found",
    "idiosyncrasies",
    "auth_required",
    "env_vars_or_credentials",
    "security_notes",
    "attribution_notes",
    "surface_decision",
    "install_command",
    "live_install_eligible",
    "docs_steward_surfaces",
    "tests_or_checks_run",
    "blockers",
    "reviewer_notes",
]


@dataclass(frozen=True)
class Candidate:
    raw_index: int
    raw_url: str
    normalized_url: str
    source_name: str
    owner: str
    repo: str
    fragment: str
    tree_ref: str
    tree_subpath: str
    slug: str
    malformed_reason: str = ""

    @property
    def malformed(self) -> bool:
        return bool(self.malformed_reason)


def now() -> str:
    return datetime.now(UTC).isoformat()


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "unknown"


def yaml_string(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|")


def unquote_frontmatter_value(value: str) -> str:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        try:
            return str(json.loads(value))
        except json.JSONDecodeError:
            return value.strip('"')
    return value


def read_raw_urls() -> list[str]:
    if not RAW_URLS.exists():
        raise FileNotFoundError(f"Missing {RAW_URLS.relative_to(ROOT)}")
    return [line.strip() for line in RAW_URLS.read_text(encoding="utf-8").splitlines() if line.strip()]


def parse_candidate(raw_index: int, raw_url: str) -> Candidate:
    parsed = urlparse(raw_url)
    parts = [part for part in parsed.path.split("/") if part]
    malformed_reason = ""
    if parsed.netloc.lower() != "github.com" or len(parts) < 2:
        malformed_reason = "not a GitHub owner/repo URL"
        owner = parts[0] if parts else ""
        repo = parts[1] if len(parts) > 1 else ""
    else:
        owner, repo = parts[0], parts[1]
    tree_ref = ""
    tree_subpath = ""
    if len(parts) >= 5 and parts[2] == "tree":
        tree_ref = parts[3]
        tree_subpath = "/".join(parts[4:])
    base = f"https://github.com/{owner}/{repo}" if owner and repo else raw_url.split("#", 1)[0]
    normalized_url = f"{base}/tree/{tree_ref}/{tree_subpath}" if tree_ref and tree_subpath else base
    source_name = f"{owner}/{repo}" if owner and repo else raw_url
    slug = slugify(f"{raw_index:03d}-{owner}-{repo}-{tree_subpath or parsed.fragment}")
    return Candidate(
        raw_index=raw_index,
        raw_url=raw_url,
        normalized_url=normalized_url,
        source_name=source_name,
        owner=owner,
        repo=repo,
        fragment=parsed.fragment,
        tree_ref=tree_ref,
        tree_subpath=tree_subpath,
        slug=slug,
        malformed_reason=malformed_reason,
    )


def normalize() -> dict[str, Any]:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    candidates = [parse_candidate(i, url) for i, url in enumerate(read_raw_urls(), 1)]
    counts = Counter(candidate.normalized_url for candidate in candidates)
    duplicate_groups: dict[str, list[int]] = defaultdict(list)
    for candidate in candidates:
        if counts[candidate.normalized_url] > 1:
            duplicate_groups[candidate.normalized_url].append(candidate.raw_index)
    payload = {
        "version": 1,
        "generated_at": now(),
        "expected_raw_count": EXPECTED_RAW_COUNT,
        "expected_unique_count": EXPECTED_UNIQUE_COUNT,
        "raw_count": len(candidates),
        "unique_count": len(counts),
        "entries": [
            {
                "raw_index": c.raw_index,
                "raw_url": c.raw_url,
                "normalized_url": c.normalized_url,
                "source_name": c.source_name,
                "owner": c.owner,
                "repo": c.repo,
                "fragment": c.fragment,
                "tree_ref": c.tree_ref,
                "tree_subpath": c.tree_subpath,
                "slug": c.slug,
                "malformed": c.malformed,
                "malformed_reason": c.malformed_reason,
                "duplicate_group": duplicate_groups.get(c.normalized_url, []),
                "is_duplicate_raw": counts[c.normalized_url] > 1
                and c.raw_index != duplicate_groups[c.normalized_url][0],
            }
            for c in candidates
        ],
        "unique_targets": sorted(counts),
        "duplicate_groups": dict(sorted(duplicate_groups.items())),
    }
    NORMALIZED.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace").lower() if path.exists() else ""


def catalog_texts() -> dict[str, str]:
    if not CATALOG_DIR.exists():
        return {}
    return {path.name: load_text(path) for path in sorted(CATALOG_DIR.glob("*.mdx"))}


def catalog_authoring_rows() -> list[dict[str, Any]]:
    rows = []
    if not CATALOG_DIR.exists():
        return rows
    for path in sorted(CATALOG_DIR.glob("*.mdx")):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            continue
        if CATALOG_ENTRY_MARKER in text:
            continue
        if not text.startswith("---\n"):
            continue
        frontmatter = text.split("---", 2)[1]
        row: dict[str, Any] = {"path": str(path.relative_to(ROOT))}
        for line in frontmatter.splitlines():
            if ":" not in line or line.startswith(" "):
                continue
            key, value = line.split(":", 1)
            row[key.strip()] = unquote_frontmatter_value(value)
        rows.append(row)
    return rows


def git_head(entry: dict[str, Any]) -> dict[str, str]:
    if entry["malformed"]:
        return {"status": "malformed", "head_sha": "", "default_branch": "", "error": entry["malformed_reason"]}
    repo_url = f"https://github.com/{entry['owner']}/{entry['repo']}.git"
    try:
        proc = subprocess.run(
            ["git", "ls-remote", "--symref", repo_url, "HEAD"],
            cwd=ROOT,
            env={"GIT_TERMINAL_PROMPT": "0"},
            text=True,
            capture_output=True,
            timeout=18,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"status": "unreachable", "head_sha": "", "default_branch": "", "error": str(exc)}
    if proc.returncode != 0:
        return {"status": "unreachable", "head_sha": "", "default_branch": "", "error": proc.stderr.strip()[:500]}
    branch = ""
    sha = ""
    for line in proc.stdout.splitlines():
        if line.startswith("ref:") and line.endswith("\tHEAD"):
            branch = line.split()[1].removeprefix("refs/heads/")
        elif line.endswith("\tHEAD"):
            sha = line.split()[0]
    return {"status": "ok", "head_sha": sha, "default_branch": branch or "HEAD", "error": ""}


def candidate_cache_key(entry: dict[str, Any]) -> str:
    if entry["owner"] and entry["repo"]:
        return f"{entry['owner'].lower()}/{entry['repo'].lower()}"
    return f"raw:{entry['raw_index']}"


def github_metadata(entry: dict[str, Any]) -> dict[str, Any]:
    if entry["malformed"]:
        return {
            "status": "skipped-malformed",
            "error": entry["malformed_reason"],
            "full_name": entry["source_name"],
            "default_branch": "",
            "pushed_at": "",
            "updated_at": "",
            "license_spdx_id": "",
            "license_name": "",
            "language": "",
            "topics": [],
            "archived": False,
            "fork": False,
            "private": False,
            "visibility": "",
        }
    try:
        proc = subprocess.run(
            ["gh", "api", f"repos/{entry['owner']}/{entry['repo']}"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "status": "unavailable",
            "error": str(exc),
            "full_name": entry["source_name"],
            "default_branch": "",
            "pushed_at": "",
            "updated_at": "",
            "license_spdx_id": "",
            "license_name": "",
            "language": "",
            "topics": [],
            "archived": False,
            "fork": False,
            "private": False,
            "visibility": "",
        }
    if proc.returncode != 0:
        return {
            "status": "unavailable",
            "error": proc.stderr.strip()[:500],
            "full_name": entry["source_name"],
            "default_branch": "",
            "pushed_at": "",
            "updated_at": "",
            "license_spdx_id": "",
            "license_name": "",
            "language": "",
            "topics": [],
            "archived": False,
            "fork": False,
            "private": False,
            "visibility": "",
        }
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        return {
            "status": "parse-error",
            "error": str(exc),
            "full_name": entry["source_name"],
            "default_branch": "",
            "pushed_at": "",
            "updated_at": "",
            "license_spdx_id": "",
            "license_name": "",
            "language": "",
            "topics": [],
            "archived": False,
            "fork": False,
            "private": False,
            "visibility": "",
        }
    license_payload = payload.get("license") or {}
    return {
        "status": "ok",
        "error": "",
        "full_name": payload.get("full_name") or entry["source_name"],
        "html_url": payload.get("html_url") or entry["normalized_url"],
        "default_branch": payload.get("default_branch") or "",
        "pushed_at": payload.get("pushed_at") or "",
        "updated_at": payload.get("updated_at") or "",
        "license_spdx_id": license_payload.get("spdx_id") or "",
        "license_name": license_payload.get("name") or "",
        "language": payload.get("language") or "",
        "topics": payload.get("topics") or [],
        "archived": bool(payload.get("archived")),
        "fork": bool(payload.get("fork")),
        "private": bool(payload.get("private")),
        "visibility": payload.get("visibility") or "",
    }


def github_license_label(metadata: dict[str, Any]) -> str:
    if metadata["status"] != "ok":
        return f"github-api-{metadata['status']}"
    spdx = str(metadata.get("license_spdx_id") or "").strip()
    name = str(metadata.get("license_name") or "").strip()
    if spdx and spdx != "NOASSERTION":
        return spdx
    if name:
        return f"NOASSERTION ({name})"
    return "NOASSERTION (license not detected by GitHub API)"


def github_latest_label(metadata: dict[str, Any]) -> str:
    if metadata["status"] != "ok":
        return f"github-api-{metadata['status']}"
    pushed_at = str(metadata.get("pushed_at") or "").strip()
    if pushed_at:
        return f"github-pushed-at:{pushed_at}"
    updated_at = str(metadata.get("updated_at") or "").strip()
    if updated_at:
        return f"github-updated-at:{updated_at}"
    return "github-api-ok-date-unavailable"


def classify(entry: dict[str, Any]) -> list[str]:
    text = f"{entry['raw_url']} {entry['source_name']} {entry['tree_subpath']}".lower()
    found: set[str] = set()
    if "mcp" in text or "modelcontextprotocol" in text:
        found.add("MCP server")
    if "plugin" in text:
        found.add("plugin")
    if "skill" in text or "skills" in text:
        found.add("skill")
    if "agent" in text:
        found.add("agent")
    if any(word in text for word in ("cli", "tool", "library", "sdk")):
        found.add("CLI/tool")
    if "awesome" in text:
        found.add("awesome list")
    if not found:
        found.add("docs/reference")
    return sorted(found)


def risk(entry: dict[str, Any], categories: list[str]) -> tuple[str, list[str], str]:
    text = f"{entry['raw_url']} {entry['source_name']} {entry['tree_subpath']}".lower()
    hits = sorted(word for word in HIGH_RISK if risk_keyword_present(word, text))
    if any(risk_keyword_present(word, text) for word in QUARANTINE):
        return "quarantine", hits, "Quarantine trigger; requires explicit threat model and approval before promotion."
    if hits:
        return "review-required", hits, "Requires safety, compliance, credential, ToS, and anti-abuse boundaries."
    if any(category in categories for category in ("MCP server", "plugin", "CLI/tool")):
        return (
            "executable-surface-review-required",
            hits,
            "Executable/tool surface requires script and dependency review.",
        )
    return "standard-review", hits, "No elevated keyword risk detected."


def entry_match_keys(entry: dict[str, Any]) -> set[str]:
    keys = {entry["source_name"].lower(), entry["normalized_url"].lower()}
    if not entry["tree_subpath"] and entry["owner"] and entry["repo"]:
        canonical = f"https://github.com/{entry['owner']}/{entry['repo']}".lower()
        keys.add(canonical)
        keys.add(canonical.removeprefix("https://github.com/"))
    return keys


def registry_has_exact_source_match(match_keys: set[str], registry_text: str) -> bool:
    return any(key and key in registry_text for key in match_keys)


def overlap(
    catalog_rows: list[dict[str, Any]],
    entry: dict[str, Any],
    mcp_text: str,
    plugin_text: str,
) -> dict[str, Any]:
    match_keys = entry_match_keys(entry)
    catalog_matches = sorted(row["path"] for row in catalog_rows if match_keys & row_match_values(row))
    return {
        "catalog_matches": catalog_matches,
        "mcp_registry_match": registry_has_exact_source_match(match_keys, mcp_text),
        "plugin_registry_match": registry_has_exact_source_match(match_keys, plugin_text),
    }


def decision(
    entry: dict[str, Any], meta: dict[str, str], categories: list[str], tier: str, ov: dict[str, Any]
) -> tuple[str, str]:
    if entry["is_duplicate_raw"]:
        return "skip_duplicate", "Exact duplicate raw entry; covered by first normalized target decision."
    if meta["status"] != "ok":
        return "skip_inaccessible", "Source could not be resolved through public Git metadata."
    if tier == "quarantine":
        return "quarantine", "Quarantine trigger detected; keep reference-only pending explicit approval."
    if ov["catalog_matches"] or ov["mcp_registry_match"] or ov["plugin_registry_match"]:
        return "merge_into_existing", "Existing repo catalog or registry surface already covers this source/domain."
    if "MCP server" in categories:
        return "reference_only", "MCP candidate requires registry design and smoke tests before enablement."
    if "plugin" in categories or "CLI/tool" in categories:
        return "reference_only", "Executable candidate requires deeper package/script review before promotion."
    if "awesome list" in categories:
        return "reference_only", "Collection source should not be vendored wholesale."
    return "reference_only", "Discovery-only pending source-list, license, security, and docs-steward promotion gates."


def docs_surfaces(categories: list[str], dec: str, tier: str) -> list[str]:
    surfaces = {"reports", "decision-log", "auth-matrix", "changelog", "openspec", "generated-drift"}
    if dec in {
        "catalog_add",
        "catalog_update",
        "merge_into_existing",
        "quarantine",
        "reference_only",
        "skip_inaccessible",
    }:
        surfaces.update({"README", "catalog-authoring", "catalog-generated", "skill-research", "install-docs"})
    if any(category in categories for category in ("MCP server", "plugin", "CLI/tool")):
        surfaces.add("mcp-tools")
    if tier != "standard-review":
        surfaces.add("runbooks")
    return sorted(surfaces)


def risk_keyword_present(keyword: str, text: str) -> bool:
    """Match risk keywords as delimited URL/path tokens, not arbitrary substrings."""

    return re.search(rf"(?<![a-z0-9]){re.escape(keyword.lower())}(?![a-z0-9])", text) is not None


def build_record(
    entry: dict[str, Any],
    catalog_rows: list[dict[str, Any]],
    mcp_text: str,
    plugin_text: str,
    meta: dict[str, str],
    repo_metadata: dict[str, Any],
) -> dict[str, Any]:
    categories = classify(entry)
    tier, risk_hits, safety = risk(entry, categories)
    ov = overlap(catalog_rows, entry, mcp_text, plugin_text)
    dec, reason = decision(entry, meta, categories, tier, ov)
    auth_required = tier in {"quarantine", "review-required", "executable-surface-review-required"}
    env_vars = ["PLACEHOLDER_ONLY_REVIEW_REQUIRED"] if auth_required else []
    source_support = [
        {
            "claim": "Candidate source was inspected without executing candidate code.",
            "support_status": "supports" if meta["status"] == "ok" else "partial",
            "confidence": 0.9 if meta["status"] == "ok" else 0.45,
            "sources": [entry["normalized_url"]],
        },
        {
            "claim": "Promotion remains blocked pending source-list, license, security, and docs-steward gates.",
            "support_status": "supports",
            "confidence": 0.95,
            "sources": ["AGENTS.md §2.7", "config/skill-registry-policy.json"],
        },
        {
            "claim": "GitHub repository metadata was queried without executing candidate code.",
            "support_status": "supports" if repo_metadata["status"] == "ok" else "partial",
            "confidence": 0.9 if repo_metadata["status"] == "ok" else 0.45,
            "sources": [f"gh api repos/{entry['owner']}/{entry['repo']}"] if entry["owner"] else [],
        },
    ]
    checks_run = ["git ls-remote --symref"]
    if entry["owner"] and entry["repo"]:
        checks_run.append("gh api repos/{owner}/{repo}")
    return {
        "raw_url": entry["raw_url"],
        "normalized_url": entry["normalized_url"],
        "source_name": entry["source_name"],
        "category": ", ".join(categories),
        "inspected_commit_sha": meta["head_sha"],
        "license": github_license_label(repo_metadata),
        "latest_release_or_commit_date": github_latest_label(repo_metadata),
        "artifact_types_found": categories,
        "install_or_integration_decision": dec,
        "reason": reason,
        "auth_required": auth_required,
        "env_vars_or_credentials": env_vars,
        "safety_notes": safety,
        "attribution_notes": f"Preserve attribution to {entry['source_name']}; verify license before adapting content.",
        "files_added": [],
        "files_modified": [],
        "tests_or_checks_run": checks_run,
        "skipped_reason": reason if dec.startswith("skip") or dec == "quarantine" else "",
        "reviewer_notes": "Automated public-metadata packet; human review required before promotion.",
        "raw_index": entry["raw_index"],
        "normalized_index": entry["normalized_url"],
        "duplicate_group": entry["duplicate_group"],
        "fragment": entry["fragment"],
        "tree_subpath": entry["tree_subpath"],
        "canonical_source": f"https://github.com/{entry['owner']}/{entry['repo']}"
        if entry["owner"] and entry["repo"]
        else "",
        "risk_tier": tier,
        "risk_keywords": risk_hits,
        "support_tier": "discovery-only",
        "phase_status": {
            "source_capture": "completed" if meta["status"] == "ok" else "completed-with-warning",
            "deep_research": "completed-public-metadata",
            "overlap": "completed",
            "security": "completed-static",
            "license": "completed-static",
            "compliance": "completed-static",
            "docs_impact": "completed",
            "decision": "completed",
        },
        "source_capture_packet": {
            "git_status": meta["status"],
            "git_error": meta["error"],
            "default_branch": meta["default_branch"],
            "github_api_status": repo_metadata["status"],
            "github_api_error": repo_metadata["error"],
            "candidate_code_executed": False,
        },
        "github_metadata_packet": repo_metadata,
        "deep_research_claims": source_support,
        "source_support_matrix": source_support,
        "overlap_packet": ov,
        "security_packet": {
            "candidate_code_executed": False,
            "network_probe_scope": "public Git metadata only",
            "executable_surface_review_required": any(
                category in categories for category in ("MCP server", "plugin", "CLI/tool")
            ),
        },
        "license_packet": {
            "license_status": (
                "spdx-from-github-api"
                if repo_metadata["status"] == "ok" and repo_metadata.get("license_spdx_id")
                else "verify-before-use"
            ),
            "license_spdx_id": repo_metadata.get("license_spdx_id", ""),
            "license_name": repo_metadata.get("license_name", ""),
        },
        "compliance_packet": {"auth_required": auth_required, "env_vars_or_credentials": env_vars},
        "docs_steward_surfaces": docs_surfaces(categories, dec, tier),
        "docs_steward_status": "packet-generated",
        "decision_packet": {"decision": dec, "reason": reason},
        "integration_packet": {"mutation_allowed": False, "required_before_promotion": "human trust-gate review"},
    }


def build_records(data: dict[str, Any]) -> list[dict[str, Any]]:
    catalog_rows = catalog_authoring_rows()
    mcp_text = load_text(MCP_REGISTRY)
    plugin_text = load_text(PLUGIN_REGISTRY)
    entries_by_key: dict[str, dict[str, Any]] = {}
    for entry in data["entries"]:
        entries_by_key.setdefault(candidate_cache_key(entry), entry)
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        git_futures = {key: pool.submit(git_head, entry) for key, entry in entries_by_key.items()}
        github_futures = {key: pool.submit(github_metadata, entry) for key, entry in entries_by_key.items()}
        git_meta_by_key = {key: future.result() for key, future in git_futures.items()}
        github_meta_by_key = {key: future.result() for key, future in github_futures.items()}
        futures = [
            pool.submit(
                build_record,
                entry,
                catalog_rows,
                mcp_text,
                plugin_text,
                git_meta_by_key[candidate_cache_key(entry)],
                github_meta_by_key[candidate_cache_key(entry)],
            )
            for entry in data["entries"]
        ]
        return sorted(
            (future.result() for future in concurrent.futures.as_completed(futures)), key=lambda r: r["raw_index"]
        )


def unique_record_groups(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_target: dict[str, dict[str, Any]] = {}
    for record in records:
        target = record["normalized_url"]
        if target not in by_target or record["raw_index"] < by_target[target]["primary"]["raw_index"]:
            by_target[target] = {"primary": record, "raw_indexes": []}
        by_target[target]["raw_indexes"].append(record["raw_index"])
    for group in by_target.values():
        group["raw_indexes"] = sorted(group["raw_indexes"])
    return sorted(by_target.values(), key=lambda group: group["primary"]["raw_index"])


def catalog_entry_name(record: dict[str, Any]) -> str:
    leaf = record["tree_subpath"].split("/")[-1] if record["tree_subpath"] else record["source_name"].split("/")[-1]
    prefix = f"{CATALOG_ENTRY_PREFIX}-{record['raw_index']:03d}-"
    max_leaf_len = 64 - len(prefix)
    leaf_slug = slugify(leaf)[:max_leaf_len].strip("-") or "source"
    return f"{prefix}{leaf_slug}"


def catalog_description(record: dict[str, Any]) -> str:
    target_label = record["source_name"]
    if record["tree_subpath"]:
        target_label = f"{target_label}/{record['tree_subpath']}"
    return (
        f"Trust-gated July 2026 candidate corpus entry for {target_label}. "
        "Catalog metadata only; do not install, vendor, adapt, or promote until source-list, "
        "license, security, and docs-steward review pass."
    )


def write_catalog_authoring(records: list[dict[str, Any]]) -> dict[str, Any]:
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    stale_removed = 0
    for path in sorted(CATALOG_DIR.glob(f"{CATALOG_ENTRY_PREFIX}-*.mdx")):
        if CATALOG_ENTRY_MARKER in path.read_text(encoding="utf-8", errors="replace"):
            path.unlink()
            stale_removed += 1

    rows = []
    for group in unique_record_groups(records):
        record = group["primary"]
        name = catalog_entry_name(record)
        path = CATALOG_DIR / f"{name}.mdx"
        raw_indexes = group["raw_indexes"]
        source = record["source_name"]
        install_source = record["normalized_url"]
        audited_head = record["inspected_commit_sha"]
        source_list_status = "not-run"
        risk_category = record["risk_tier"]
        description = catalog_description(record)
        executable_surface = (
            "review-required"
            if record["security_packet"]["executable_surface_review_required"]
            else "not-detected-in-static-intake"
        )
        target_label = record["source_name"]
        if record["tree_subpath"]:
            target_label = f"{target_label}/{record['tree_subpath']}"
        frontmatter = [
            "---",
            f"name: {yaml_string(name)}",
            f"description: {yaml_string(description)}",
            f"title: {yaml_string(name.replace('-', ' ').title())}",
            'source_kind: "curated-external"',
            f"source: {yaml_string(source)}",
            f"install_source: {yaml_string(install_source)}",
            'status: "global-only-or-avoid"',
            'trust_tier: "global-only-or-avoid"',
            'provenance_status: "explicit-unresolved"',
            'sync_kind: "none"',
            "target_agents: []",
            f"source_url: {yaml_string(record['normalized_url'])}",
            'selector_mode: "unresolved"',
            (
                "unresolved_reason: "
                + yaml_string(
                    "July 2026 candidate corpus intake only; source-list evidence, license review, "
                    "security review, and docs-steward promotion gates are still required."
                )
            ),
            'audit_date: "2026-07-06"',
            f"audited_head: {yaml_string(audited_head)}",
            'pin_policy: "pin-before-install"',
            (
                "no_pin_rationale: "
                + yaml_string("No install command is published until the candidate passes promotion review.")
            ),
            f"source_list_evidence: {yaml_string(source_list_status)}",
            f"executable_surface: {yaml_string(executable_surface)}",
            'credential_behavior: "placeholder-only; credentials must remain user-owned and uncommitted"',
            'network_access: "public Git metadata only during corpus intake"',
            'file_access: "no candidate files installed or executed during corpus intake"',
            f"live_action_risk: {yaml_string(record['safety_notes'])}",
            f"risk_category: {yaml_string(risk_category)}",
            f"dedupe_notes: {yaml_string('Raw indexes covered: ' + ', '.join(str(index) for index in raw_indexes))}",
            f"notes: {yaml_string(description)}",
            f"risk_notes: {yaml_string(record['safety_notes'])}",
            (
                "promotion_policy: "
                + yaml_string(
                    "Keep non-installable until source-list, license, security, attribution, auth, "
                    "and docs-steward gates pass."
                )
            ),
            (
                "provenance_evidence: "
                + yaml_string(
                    "Generated from planning/manifests/candidate-corpus-jul2026 records; "
                    "no npx skills add --list evidence captured yet."
                )
            ),
            "---",
        ]
        body = [
            "",
            f"{{/* {CATALOG_ENTRY_MARKER}: source=planning/manifests/candidate-corpus-jul2026 */}}",
            "",
            f"# {name.replace('-', ' ').title()}",
            "",
            f"This row adds `{target_label}` to the curated external catalog as a trust-gated July 2026 candidate.",
            "",
            "It is intentionally non-installable. Do not publish an install command, run candidate code, "
            "copy source content, or promote this candidate until the source-list, license, security, "
            "attribution, auth, and docs-steward gates pass.",
            "",
            "## Intake",
            "",
            f"- Raw indexes covered: {', '.join(str(index) for index in raw_indexes)}",
            f"- Normalized URL: [{record['normalized_url']}]({record['normalized_url']})",
            f"- Artifact types found: `{record['category']}`",
            f"- Intake decision: `{record['install_or_integration_decision']}`",
            f"- Risk tier: `{record['risk_tier']}`",
            f"- Inspected commit SHA: `{audited_head or 'unresolved'}`",
            f"- License status: `{record['license']}`",
            "",
            "## Promotion Gates",
            "",
            "- Run read-only source-list discovery, for example `npx skills add <source> --list`, when applicable.",
            "- Verify license compatibility and attribution before adapting any content.",
            "- Review hooks, scripts, commands, allowed tools, dependencies, network calls, and credential handling.",
            "- Route MCP servers, plugins, CLIs, libraries, and broad collections through their native repo surfaces.",
            "- Update docs-steward surfaces from source after any promotion decision.",
            "",
            "## Safety Notes",
            "",
            f"- {record['safety_notes']}",
            f"- Auth required: `{str(record['auth_required']).lower()}`",
            (
                "- Secrets, tokens, private keys, connection strings, cookies, OAuth grants, and account IDs "
                "must not be committed."
            ),
        ]
        path.write_text("\n".join(frontmatter + body) + "\n", encoding="utf-8")
        rows.append({
            "name": name,
            "path": str(path.relative_to(ROOT)),
            "normalized_url": record["normalized_url"],
            "source_name": record["source_name"],
            "raw_indexes": raw_indexes,
            "status": "global-only-or-avoid",
            "sync_kind": "none",
            "risk_tier": record["risk_tier"],
            "intake_decision": record["install_or_integration_decision"],
        })

    summary_payload = {
        "version": 1,
        "generated_at": now(),
        "marker": CATALOG_ENTRY_MARKER,
        "rows_written": len(rows),
        "unique_targets": len(unique_record_groups(records)),
        "stale_generated_rows_removed": stale_removed,
        "status": "global-only-or-avoid",
        "sync_kind": "none",
        "install_commands_published": 0,
        "rows": rows,
    }
    (MANIFEST_DIR / "catalog-authoring-summary.json").write_text(
        json.dumps(summary_payload, indent=2) + "\n", encoding="utf-8"
    )
    return summary_payload


def write_shards(data: dict[str, Any]) -> None:
    shards = []
    for start in range(0, len(data["entries"]), MICRO_WAVE_SIZE):
        chunk = data["entries"][start : start + MICRO_WAVE_SIZE]
        shards.append({
            "shard_id": f"MW-{start // MICRO_WAVE_SIZE + 1:02d}",
            "start_index": start + 1,
            "count": len(chunk),
            "raw_indexes": [entry["raw_index"] for entry in chunk],
            "node_families": {
                family: [f"{family}{entry['raw_index']:03d}" for entry in chunk]
                for family in ["SC", "DR", "OC", "SA", "LA", "CA", "DI", "DA", "PD"]
            },
        })
    payload = {"version": 1, "generated_at": now(), "micro_wave_size": MICRO_WAVE_SIZE, "shards": shards}
    (MANIFEST_DIR / "shard-map-293.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    clusters = [{"id": cid, "name": name, "match": match} for cid, name, match in CLUSTERS]
    (MANIFEST_DIR / "cluster-map-40.json").write_text(json.dumps(clusters, indent=2) + "\n", encoding="utf-8")


def summary(data: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    decisions = Counter(record["install_or_integration_decision"] for record in records)
    terminal_decisions = Counter(
        group["primary"]["install_or_integration_decision"] for group in unique_record_groups(records)
    )
    risks = Counter(record["risk_tier"] for record in records)
    return {
        "generated_at": now(),
        "raw_count": len(records),
        "unique_count": len(data["unique_targets"]),
        "duplicates_deduped": len(records) - len(data["unique_targets"]),
        "decisions": dict(sorted(decisions.items())),
        "risk_tiers": dict(sorted(risks.items())),
        "added_count": len(data["unique_targets"]),
        "catalog_authoring_added_count": len(data["unique_targets"]),
        "live_install_added_count": decisions["catalog_add"]
        + decisions["mcp_registry_add"]
        + decisions["plugin_registry_add"],
        "adapted_count": decisions["repo_skill_adapt"] + decisions["catalog_update"],
        "reference_only_count": terminal_decisions["reference_only"],
        "skipped_count": decisions["skip_duplicate"]
        + decisions["skip_inaccessible"]
        + decisions["skip_risky"]
        + decisions["quarantine"],
        "auth_required_count": sum(1 for record in records if record["auth_required"]),
    }


def unique_decisions(data: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["normalized_url"]].append(record)
    decisions = []
    for target in data["unique_targets"]:
        group = sorted(grouped[target], key=lambda record: record["raw_index"])
        primary = next(
            (record for record in group if record["install_or_integration_decision"] != "skip_duplicate"), group[0]
        )
        decisions.append({
            "normalized_url": target,
            "raw_indexes": [record["raw_index"] for record in group],
            "source_name": primary["source_name"],
            "decision": primary["install_or_integration_decision"],
            "reason": primary["reason"],
            "risk_tier": primary["risk_tier"],
            "docs_steward_surfaces": primary["docs_steward_surfaces"],
        })
    return decisions


def write_json(name: str, payload: Any) -> None:
    (MANIFEST_DIR / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def source_match_keys(record: dict[str, Any]) -> set[str]:
    keys = {record["source_name"].lower(), record["normalized_url"].lower()}
    if not record["tree_subpath"]:
        canonical = record.get("canonical_source", "")
        if canonical:
            keys.add(canonical.lower())
            keys.add(canonical.lower().removeprefix("https://github.com/"))
    return keys


def row_match_values(row: dict[str, Any]) -> set[str]:
    values = set()
    for key in ["source", "install_source", "source_url"]:
        value = str(row.get(key, "")).strip().lower()
        if value:
            values.add(value)
            values.add(value.removeprefix("https://github.com/"))
    return values


def build_existing_integration_coverage(records: list[dict[str, Any]]) -> dict[str, Any]:
    rows = catalog_authoring_rows()
    groups = unique_record_groups(records)
    items = []
    counts: Counter[str] = Counter()
    for group in groups:
        primary = group["primary"]
        match_keys = source_match_keys(primary)
        matches = []
        for row in rows:
            if not (match_keys & row_match_values(row)):
                continue
            install_command = str(row.get("install_command", "")).strip()
            sync_kind = str(row.get("sync_kind", "")).strip()
            matches.append({
                "name": row.get("name", ""),
                "path": row["path"],
                "source": row.get("source", ""),
                "install_source": row.get("install_source", ""),
                "source_url": row.get("source_url", ""),
                "status": row.get("status", ""),
                "trust_tier": row.get("trust_tier", ""),
                "sync_kind": sync_kind,
                "has_install_command": bool(install_command),
            })
        installable = [
            match for match in matches if match["has_install_command"] and match["sync_kind"] not in {"", "none"}
        ]
        if installable:
            coverage_status = "covered-by-existing-installable-catalog"
        elif matches:
            coverage_status = "covered-by-existing-reference"
        else:
            coverage_status = "needs-promotion-review"
        counts[coverage_status] += 1
        items.append({
            "normalized_url": primary["normalized_url"],
            "source_name": primary["source_name"],
            "raw_indexes": group["raw_indexes"],
            "intake_decision": primary["install_or_integration_decision"],
            "coverage_status": coverage_status,
            "existing_rows": matches,
            "recommended_next_action": (
                "Treat as already integrated through existing curated catalog row; do not duplicate."
                if installable
                else "Research and route through the promotion task graph before installing or adapting."
            ),
        })
    return {
        "version": 1,
        "generated_at": now(),
        "summary": dict(sorted(counts.items())),
        "items": items,
    }


COVERAGE_PROMOTION_WAVES = [
    ("W00", "existing-catalog-coverage", "Already covered by existing curated/installable catalog entries."),
    ("W01", "official-vendor-platform-data", "Official vendor, platform, data, and database skills."),
    ("W02", "apple-ios-macos-swift", "Apple, iOS, macOS, Swift, simulator, and App Store candidates."),
    ("W03", "frontend-web-auth-design-quality", "Frontend, web quality, auth, TypeScript, React, Solid, and design."),
    ("W04", "charts-diagrams-media-cad-webgpu", "Charts, diagrams, slides, visual media, CAD, and WebGPU."),
    ("W05", "cloud-iac-devops-security-mcp-plugins", "Cloud, IaC, DevOps, security, MCP, plugins, and CLIs."),
    ("W06", "research-legal-finance-economics", "Research, academic, legal, finance, and economics."),
    (
        "W07",
        "seo-aso-gtm-sales-marketing-product-content",
        "SEO, ASO, GEO, GTM, sales, marketing, product, and content.",
    ),
    (
        "W08",
        "openspec-workflow-docs-obsidian-composio-pedronauck",
        "OpenSpec, workflow, docs, Obsidian, Composio, and Pedronauck.",
    ),
    ("W99", "quarantine-or-blocked", "Quarantined, inaccessible, malformed, or blocked sources."),
]


def promotion_wave_for(record: dict[str, Any], coverage_status: str) -> tuple[str, str]:
    if coverage_status == "covered-by-existing-installable-catalog":
        return "W00", "Existing installable catalog row owns integration; no duplicate install command."
    decision = record["install_or_integration_decision"]
    if decision in {"quarantine", "skip_inaccessible", "skip_risky"}:
        return "W99", record["reason"]
    text = f"{record['source_name']} {record['normalized_url']} {record['tree_subpath']} {record['category']}".lower()
    if any(
        token in text
        for token in [
            "apple",
            "app-intents",
            "app-store",
            "background-execution",
            "core-data",
            "focusengine",
            "ios",
            "macos",
            "swift",
            "widget",
            "xcode",
        ]
    ):
        return "W02", "Apple platform assumptions, signing, simulator, and App Store boundaries are required."
    if any(
        token in text
        for token in [
            "cloudflare",
            "wordpress",
            "timescale",
            "tanstack",
            "solana",
            "ast-grep",
            "langchain",
            "duckdb",
            "dbt",
            "elastic",
            "apify",
            "supabase",
            "huggingface",
            "google",
            "vercel",
            "planetscale",
            "postgres",
            "database",
        ]
    ):
        return "W01", "Official/vendor/data source; prefer existing official curated rows or precise selectors."
    if any(
        token in text
        for token in [
            "react",
            "typescript",
            "solid",
            "auth",
            "frontend",
            "web-quality",
            "css",
            "html",
            "design",
            "figma",
            "ui",
            "ux",
        ]
    ):
        return "W03", "Frontend/web/design source; dedupe triggers and avoid broad activation."
    if any(
        token in text
        for token in [
            "chart",
            "diagram",
            "ppt",
            "slide",
            "cad",
            "webgpu",
            "mermaid",
            "motion",
            "image",
            "logo",
            "visual",
            "video",
        ]
    ):
        return "W04", "Visual/media source; document copyright, brand, likeness, and asset provenance."
    if any(
        token in text
        for token in [
            "aws",
            "terraform",
            "cloud",
            "security",
            "devops",
            "mcp",
            "plugin",
            "cli",
            "guard",
            "secret",
            "rg-guard",
            "langfuse",
        ]
    ):
        return "W05", "Executable or operational source; require dry-run, least privilege, and smoke tests."
    if any(
        token in text
        for token in [
            "research",
            "academic",
            "paper",
            "zotero",
            "notebooklm",
            "legal",
            "finance",
            "econ",
            "buffett",
            "yahoo",
            "scientific",
        ]
    ):
        return "W06", "Research/domain source; document citation, evidence, non-advice, and reproducibility."
    if any(
        token in text
        for token in [
            "seo",
            "aso",
            "geo",
            "gtm",
            "sales",
            "marketing",
            "outbound",
            "affiliate",
            "ads",
            "product",
            "content",
            "copywriting",
            "pm-",
            "pm_",
            "pm/",
        ]
    ):
        return "W07", "Growth/product source; document anti-abuse, ToS, and non-deceptive boundaries."
    if any(
        token in text
        for token in [
            "openspec",
            "workflow",
            "docs",
            "readme",
            "obsidian",
            "composiohq",
            "pedronauck",
            "find-rules",
            "find-skills",
        ]
    ):
        return "W08", "Workflow/docs source; dedupe against repo skills and docs-steward surfaces."
    return "W08", "General workflow/content source; route after source research."


def build_coverage_promotion_wave_plan(records: list[dict[str, Any]], coverage: dict[str, Any]) -> dict[str, Any]:
    coverage_by_target = {item["normalized_url"]: item for item in coverage["items"]}
    groups = unique_record_groups(records)
    wave_meta: dict[str, dict[str, Any]] = {
        wave_id: {"wave_id": wave_id, "name": name, "description": description, "targets": []}
        for wave_id, name, description in COVERAGE_PROMOTION_WAVES
    }
    for group in groups:
        primary = group["primary"]
        target_coverage = coverage_by_target[primary["normalized_url"]]
        wave_id, reason = promotion_wave_for(primary, target_coverage["coverage_status"])
        wave_meta[wave_id]["targets"].append({
            "normalized_url": primary["normalized_url"],
            "source_name": primary["source_name"],
            "raw_indexes": group["raw_indexes"],
            "coverage_status": target_coverage["coverage_status"],
            "intake_decision": primary["install_or_integration_decision"],
            "risk_tier": primary["risk_tier"],
            "auth_required": primary["auth_required"],
            "docs_steward_surfaces": primary["docs_steward_surfaces"],
            "next_gate": reason,
        })
    waves = []
    for wave_id, _, _ in COVERAGE_PROMOTION_WAVES:
        wave = wave_meta[wave_id]
        wave["target_count"] = len(wave["targets"])
        wave["raw_indexes"] = sorted({index for target in wave["targets"] for index in target["raw_indexes"]})
        wave["mutation_policy"] = (
            "no mutation; use existing catalog rows"
            if wave_id == "W00"
            else "single integrator only after read-only research packets pass"
        )
        waves.append(wave)
    return {
        "version": 1,
        "generated_at": now(),
        "total_targets": sum(wave["target_count"] for wave in waves),
        "waves": waves,
    }


def raw_leaf_status(suffix: str, record: dict[str, Any]) -> str:
    if suffix == "URL":
        return "complete-static"
    if suffix in {"LIVE", "HEAD"}:
        if record["source_capture_packet"]["git_status"] == "ok":
            return "complete-public-git-metadata"
        return "complete-with-warning"
    if suffix in {"SKILL", "MCP", "PLUGIN", "AGENT", "CLI", "AUTH", "SEC", "TOS", "DEDUPE", "ROUTE"}:
        return "provisional-static-intake"
    if suffix in {"PROMOTE", "VAL"}:
        return "blocked-until-trust-gates"
    return "pending-deep-source-research"


def raw_leaf_notes(suffix: str, record: dict[str, Any]) -> str:
    if suffix == "URL":
        return "Raw URL, normalized URL, fragment, tree path, owner, and repo are captured."
    if suffix == "LIVE":
        status = record["source_capture_packet"]["git_status"]
        return f"Public git metadata probe status: {status}."
    if suffix == "HEAD":
        sha = record["inspected_commit_sha"] or "unresolved"
        branch = record["source_capture_packet"]["default_branch"] or "unresolved"
        return f"Default branch `{branch}` with HEAD `{sha}` from git ls-remote."
    if suffix == "AUTH":
        if record["auth_required"]:
            return "Placeholder-only auth boundary recorded; user-owned credentials required before live use."
        return "No auth requirement detected in static URL/category intake."
    if suffix == "SEC":
        return "Static risk tier recorded; no candidate code was executed."
    if suffix == "TOS":
        return "Compliance boundary is provisional and must be rechecked from source docs before promotion."
    if suffix == "DEDUPE":
        return "Exact duplicate group and existing repo overlap packet recorded."
    if suffix == "ROUTE":
        return f"Provisional intake decision: {record['install_or_integration_decision']}."
    if suffix == "PROMOTE":
        return "Mutation is blocked until source-list, license, security, attribution, auth, and docs gates pass."
    if suffix == "VAL":
        return "Target-specific validation waits for a promotion decision."
    return "Deep source research required before this check can be marked complete."


def build_raw_leaf_checks(record: dict[str, Any]) -> list[dict[str, Any]]:
    lane_id = f"U{record['raw_index']:03d}"
    return [
        {
            "leaf_id": f"{lane_id}.{suffix}",
            "suffix": suffix,
            "mode": mode,
            "required_check": required_check,
            "required_evidence": required_evidence,
            "status": raw_leaf_status(suffix, record),
            "notes": raw_leaf_notes(suffix, record),
        }
        for suffix, mode, required_check, required_evidence in RAW_RESEARCH_LEAF_CHECKS
    ]


def unique_leaf_status(suffix: str, primary: dict[str, Any], coverage_status: str) -> str:
    if coverage_status == "covered-by-existing-installable-catalog" and suffix in {
        "RAW-MAP",
        "SURFACE",
        "AUTH",
        "INSTALL",
        "DOCS",
        "VAL",
    }:
        return "covered-by-existing-catalog"
    if suffix == "RAW-MAP":
        return "complete-static"
    if suffix in {"SURFACE", "AUTH", "DOCS"}:
        return "provisional-static-intake"
    if suffix in {"INSTALL", "VAL"}:
        return "blocked-until-trust-gates"
    if suffix == "ATTRIB":
        return "pending-license-review"
    return "pending-deep-source-research"


def unique_leaf_notes(
    suffix: str,
    primary: dict[str, Any],
    raw_indexes: list[int],
    coverage_status: str,
) -> str:
    if coverage_status == "covered-by-existing-installable-catalog":
        if suffix == "INSTALL":
            return "Existing curated catalog row already owns install command; no duplicate command is published."
        if suffix == "SURFACE":
            return "Existing curated catalog row is the integration surface."
        if suffix == "VAL":
            return "Covered by existing catalog validation and skills sync dry-run."
    if suffix == "RAW-MAP":
        return "Raw indexes covered: " + ", ".join(str(index) for index in raw_indexes)
    if suffix == "SURFACE":
        return f"Provisional terminal surface decision: {primary['install_or_integration_decision']}."
    if suffix == "AUTH":
        if primary["auth_required"]:
            return "Auth remains placeholder-only until source review and user-owned setup."
        return "No auth requirement detected in the static intake packet."
    if suffix == "INSTALL":
        return "No live install command is eligible until all trust gates pass."
    if suffix == "DOCS":
        return "Docs-steward surfaces are mapped, but generated docs must be rerun after any promotion."
    if suffix == "VAL":
        return "Validation waits for concrete repo or live-harness mutation."
    if suffix == "ATTRIB":
        return primary["attribution_notes"]
    return "Deep source research required before synthesis can be finalized."


def build_unique_leaf_checks(group: dict[str, Any]) -> list[dict[str, Any]]:
    primary = group["primary"]
    raw_indexes = group["raw_indexes"]
    lane_id = group["lane_id"]
    coverage_status = group["coverage_status"]
    return [
        {
            "leaf_id": f"{lane_id}.{suffix}",
            "suffix": suffix,
            "mode": mode,
            "required_check": required_check,
            "required_evidence": required_evidence,
            "status": unique_leaf_status(suffix, primary, coverage_status),
            "notes": unique_leaf_notes(suffix, primary, raw_indexes, coverage_status),
        }
        for suffix, mode, required_check, required_evidence in UNIQUE_SYNTHESIS_LEAF_CHECKS
    ]


def build_research_task_graph(
    data: dict[str, Any],
    records: list[dict[str, Any]],
    coverage: dict[str, Any],
) -> dict[str, Any]:
    record_by_raw_index = {record["raw_index"]: record for record in records}
    unique_groups = unique_record_groups(records)
    coverage_by_target = {item["normalized_url"]: item for item in coverage["items"]}
    for unique_index, group in enumerate(unique_groups, 1):
        group["lane_id"] = f"N{unique_index:03d}"
        target_coverage = coverage_by_target[group["primary"]["normalized_url"]]
        group["coverage_status"] = target_coverage["coverage_status"]
        group["existing_rows"] = target_coverage["existing_rows"]
    unique_lane_by_target = {group["primary"]["normalized_url"]: group["lane_id"] for group in unique_groups}

    raw_lanes = []
    for entry in data["entries"]:
        record = record_by_raw_index[entry["raw_index"]]
        raw_lanes.append({
            "lane_id": f"U{entry['raw_index']:03d}",
            "raw_index": entry["raw_index"],
            "raw_url": entry["raw_url"],
            "normalized_url": entry["normalized_url"],
            "normalized_lane_id": unique_lane_by_target[entry["normalized_url"]],
            "source_name": entry["source_name"],
            "fragment": entry["fragment"],
            "tree_ref": entry["tree_ref"],
            "tree_subpath": entry["tree_subpath"],
            "duplicate_group": entry["duplicate_group"],
            "is_duplicate_raw": entry["is_duplicate_raw"],
            "current_intake_decision": record["install_or_integration_decision"],
            "risk_tier": record["risk_tier"],
            "live_install_eligible": False,
            "promotion_blocked_by": [
                "source-list evidence",
                "license review",
                "security review",
                "attribution review",
                "auth review",
                "docs-steward promotion",
            ],
            "leaf_checks": build_raw_leaf_checks(record),
        })

    unique_lanes = []
    for group in unique_groups:
        primary = group["primary"]
        covered = group["coverage_status"] == "covered-by-existing-installable-catalog"
        unique_lanes.append({
            "lane_id": group["lane_id"],
            "normalized_url": primary["normalized_url"],
            "source_name": primary["source_name"],
            "raw_indexes": group["raw_indexes"],
            "raw_lane_ids": [f"U{index:03d}" for index in group["raw_indexes"]],
            "current_intake_decision": primary["install_or_integration_decision"],
            "terminal_decision_status": "covered-by-existing-catalog" if covered else "provisional-intake-only",
            "existing_integration_status": group["coverage_status"],
            "existing_rows": group["existing_rows"],
            "risk_tier": primary["risk_tier"],
            "auth_required": primary["auth_required"],
            "docs_steward_surfaces": primary["docs_steward_surfaces"],
            "live_install_eligible": False,
            "leaf_checks": build_unique_leaf_checks(group),
        })

    raw_leaf_count = len(raw_lanes) * len(RAW_RESEARCH_LEAF_CHECKS)
    unique_leaf_count = len(unique_lanes) * len(UNIQUE_SYNTHESIS_LEAF_CHECKS)
    return {
        "version": 1,
        "generated_at": now(),
        "status": "research-graph-generated",
        "raw_lane_count": len(raw_lanes),
        "unique_target_lane_count": len(unique_lanes),
        "raw_leaf_check_count": raw_leaf_count,
        "unique_leaf_check_count": unique_leaf_count,
        "total_leaf_check_count": raw_leaf_count + unique_leaf_count,
        "live_install_eligible_count": 0,
        "existing_integration_summary": coverage["summary"],
        "raw_leaf_check_template": [
            {
                "suffix": suffix,
                "mode": mode,
                "required_check": required_check,
                "required_evidence": required_evidence,
            }
            for suffix, mode, required_check, required_evidence in RAW_RESEARCH_LEAF_CHECKS
        ],
        "unique_leaf_check_template": [
            {
                "suffix": suffix,
                "mode": mode,
                "required_check": required_check,
                "required_evidence": required_evidence,
            }
            for suffix, mode, required_check, required_evidence in UNIQUE_SYNTHESIS_LEAF_CHECKS
        ],
        "raw_lanes": raw_lanes,
        "unique_target_lanes": unique_lanes,
    }


def build_research_packet_schema() -> dict[str, Any]:
    return {
        "version": 1,
        "generated_at": now(),
        "raw_lane_id_format": "U###",
        "unique_target_lane_id_format": "N###",
        "required_packet_fields": RESEARCH_PACKET_FIELDS,
        "raw_leaf_check_suffixes": [suffix for suffix, *_ in RAW_RESEARCH_LEAF_CHECKS],
        "unique_synthesis_leaf_check_suffixes": [suffix for suffix, *_ in UNIQUE_SYNTHESIS_LEAF_CHECKS],
        "terminal_surface_decisions": [
            "curated-external",
            "repo-native-skill",
            "mcp",
            "plugin",
            "agent",
            "instruction",
            "docs-reference",
            "merged",
            "blocked",
        ],
        "live_install_rule": (
            "Live installs remain disabled until source-list, license, security, attribution, auth, "
            "and docs-steward gates pass and the exact command is recorded."
        ),
    }


def cluster_for_record(record: dict[str, Any]) -> tuple[str, str]:
    text = f"{record['raw_url']} {record['source_name']} {record['tree_subpath']}".lower()
    for cluster_id, cluster_name, needles in CLUSTERS:
        if any(needle.lower() in text for needle in needles):
            return cluster_id, cluster_name
    return "CJ99", "other-candidate-sources"


def build_subagent_wave_queue(records: list[dict[str, Any]]) -> dict[str, Any]:
    domain_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    ordered_records = sorted(records, key=lambda item: item["raw_index"])
    for record in ordered_records:
        domain_groups[cluster_for_record(record)].append(record)

    domain_waves: list[dict[str, Any]] = []
    for (cluster_id, cluster_name), items in sorted(domain_groups.items()):
        domain_waves.append({
            "wave_id": cluster_id,
            "name": cluster_name,
            "mode": "parallel-read-only",
            "mutation_policy": "research packets only; root integrator serializes repo edits",
            "raw_count": len(items),
            "raw_indexes": [item["raw_index"] for item in items],
            "source_names": sorted({item["source_name"] for item in items}),
            "required_roles": [
                "source-research",
                "security-review",
                "license-attribution-review",
                "surface-routing",
                "docs-steward-impact",
            ],
        })

    micro_waves: list[dict[str, Any]] = []
    for start in range(0, len(ordered_records), MICRO_WAVE_SIZE):
        chunk = ordered_records[start : start + MICRO_WAVE_SIZE]
        micro_waves.append({
            "wave_id": f"MW-{start // MICRO_WAVE_SIZE + 1:02d}",
            "mode": "parallel-read-only",
            "raw_count": len(chunk),
            "raw_indexes": [item["raw_index"] for item in chunk],
            "handoff_packet": "research-packet-schema.json",
        })

    covered = sorted({index for wave in domain_waves for index in wave["raw_indexes"]})
    return {
        "version": 1,
        "generated_at": now(),
        "status": "ready-for-read-only-subagent-dispatch",
        "covered_raw_count": len(covered),
        "covered_raw_indexes": covered,
        "domain_wave_count": len(domain_waves),
        "micro_wave_count": len(micro_waves),
        "domain_waves": domain_waves,
        "micro_waves": micro_waves,
    }


def build_promotion_readiness_queue(decisions: list[dict[str, Any]], graph: dict[str, Any]) -> dict[str, Any]:
    lanes_by_target = {lane["normalized_url"]: lane for lane in graph["unique_target_lanes"]}
    blocked = []
    for decision_item in decisions:
        lane = lanes_by_target[decision_item["normalized_url"]]
        blocked.append({
            "lane_id": lane["lane_id"],
            "normalized_url": decision_item["normalized_url"],
            "source_name": decision_item["source_name"],
            "raw_indexes": decision_item["raw_indexes"],
            "current_intake_decision": decision_item["decision"],
            "existing_integration_status": lane["existing_integration_status"],
            "risk_tier": lane["risk_tier"],
            "auth_required": lane["auth_required"],
            "blocking_gates": [
                "source-list evidence",
                "license review",
                "security review",
                "attribution review",
                "auth review",
                "docs-steward promotion",
                "target-specific validation",
            ],
            "live_install_eligible": False,
            "install_command": "",
            "repo_mutation_eligible": False,
        })

    return {
        "version": 1,
        "generated_at": now(),
        "status": "all-targets-blocked-until-trust-gates",
        "summary": {
            "unique_targets": len(decisions),
            "ready_for_repo_promotion": 0,
            "ready_for_live_install": 0,
            "blocked_until_trust_gates": len(blocked),
        },
        "ready_for_repo_promotion": [],
        "ready_for_live_install": [],
        "blocked_until_trust_gates": blocked,
    }


def build_full_integration_progress(
    data: dict[str, Any],
    records: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    graph: dict[str, Any],
    coverage: dict[str, Any],
    readiness: dict[str, Any],
    wave_plan: dict[str, Any],
) -> dict[str, Any]:
    status_counts = Counter(leaf["status"] for lane in graph["raw_lanes"] for leaf in lane["leaf_checks"])
    status_counts.update(leaf["status"] for lane in graph["unique_target_lanes"] for leaf in lane["leaf_checks"])
    return {
        "version": 1,
        "generated_at": now(),
        "phase": "research-graph-ready",
        "complete": False,
        "raw_candidates": len(records),
        "unique_normalized_targets": len(data["unique_targets"]),
        "unique_terminal_decisions": len(decisions),
        "research_graph": {
            "raw_lanes": graph["raw_lane_count"],
            "unique_target_lanes": graph["unique_target_lane_count"],
            "total_leaf_checks": graph["total_leaf_check_count"],
            "leaf_status_counts": dict(sorted(status_counts.items())),
        },
        "existing_integration_coverage": coverage["summary"],
        "promotion_readiness": readiness["summary"],
        "promotion_waves": {
            wave["wave_id"]: wave["target_count"] for wave in wave_plan["waves"] if wave["target_count"]
        },
        "live_install": {
            "eligible_count": 0,
            "status": "blocked-until-trust-gates",
            "reason": "No candidate has complete source-list, license, security, attribution, auth, and docs review.",
        },
        "next_actions": [
            "Dispatch read-only source research packets for each U### lane.",
            "Promote only the N### targets whose raw lanes pass trust gates.",
            "Regenerate docs-steward surfaces after each promotion wave.",
            "Run focused validation and commit each validated wave if still authorized.",
        ],
    }


def build_promotion_wave_plan(
    records: list[dict[str, Any]],
    graph: dict[str, Any],
) -> dict[str, Any]:
    record_by_raw_index = {record["raw_index"]: record for record in records}
    waves_by_id: dict[str, dict[str, Any]] = {
        wave_id: {
            "wave_id": wave_id,
            "name": name,
            "description": description,
            "objective": description,
            "promotion_policy": (
                "Read-only source research first; mutate only after license, security, "
                "attribution, auth, dedupe, docs-steward, and validation gates pass."
            ),
            "stop_rules": [
                "Stop promotion if upstream is inaccessible or malformed without a replacement canonical source.",
                "Stop promotion if license is missing, unclear, incompatible, or attribution cannot be preserved.",
                (
                    "Stop promotion if candidate scripts, hooks, plugins, MCP servers, or CLIs require "
                    "unreviewed execution."
                ),
                "Stop promotion if credentials, OAuth scopes, account IDs, or live services are required.",
                (
                    "Stop promotion if the surface duplicates an existing installable catalog row without "
                    "a merge decision."
                ),
            ],
            "validation_commands": [
                "uv run python scripts/generate_candidate_corpus_shards.py --check-coverage",
                "uv run pytest tests/test_candidate_corpus.py -q",
                "uv run ruff check scripts/generate_candidate_corpus_shards.py tests/test_candidate_corpus.py",
                "uv run wagents validate",
                "uv run wagents skills sync --dry-run",
                "uv run wagents docs generate --no-installed",
            ],
            "unique_target_count": 0,
            "raw_entry_count": 0,
            "coverage_status_counts": {},
            "risk_tier_counts": {},
            "lanes": [],
            "targets": [],
        }
        for wave_id, name, description in COVERAGE_PROMOTION_WAVES
    }

    for lane in graph["unique_target_lanes"]:
        primary = record_by_raw_index[lane["raw_indexes"][0]]
        wave_id, reason = promotion_wave_for(primary, lane["existing_integration_status"])
        item = {
            "lane_id": lane["lane_id"],
            "normalized_url": lane["normalized_url"],
            "source_name": lane["source_name"],
            "raw_indexes": lane["raw_indexes"],
            "raw_lane_ids": lane["raw_lane_ids"],
            "current_intake_decision": lane["current_intake_decision"],
            "existing_integration_status": lane["existing_integration_status"],
            "risk_tier": lane["risk_tier"],
            "auth_required": lane["auth_required"],
            "live_install_eligible": False,
            "next_packet_required": "complete all U### and N### trust-gate leaf checks before promotion",
            "next_gate": reason,
        }
        waves_by_id[wave_id]["lanes"].append(item)
        waves_by_id[wave_id]["targets"].append({
            "normalized_url": lane["normalized_url"],
            "source_name": lane["source_name"],
            "raw_indexes": lane["raw_indexes"],
            "coverage_status": lane["existing_integration_status"],
            "intake_decision": lane["current_intake_decision"],
            "risk_tier": lane["risk_tier"],
            "auth_required": lane["auth_required"],
            "docs_steward_surfaces": lane["docs_steward_surfaces"],
            "next_gate": reason,
        })

    assigned_targets: set[str] = set()
    covered_raw_indexes: set[int] = set()
    waves = []
    for wave_id, _, _ in COVERAGE_PROMOTION_WAVES:
        wave = waves_by_id[wave_id]
        wave["lanes"].sort(key=lambda item: item["lane_id"])
        wave["targets"].sort(key=lambda item: item["normalized_url"])
        wave["unique_target_count"] = len(wave["lanes"])
        wave["target_count"] = wave["unique_target_count"]
        raw_indexes = sorted({index for item in wave["lanes"] for index in item["raw_indexes"]})
        wave["raw_entry_count"] = len(raw_indexes)
        wave["raw_indexes"] = raw_indexes
        wave["mutation_policy"] = (
            "no mutation; use existing catalog rows"
            if wave_id == "W00"
            else "single integrator only after read-only research packets pass"
        )
        coverage_counts = Counter(item["existing_integration_status"] for item in wave["lanes"])
        risk_counts = Counter(item["risk_tier"] for item in wave["lanes"])
        wave["coverage_status_counts"] = dict(sorted(coverage_counts.items()))
        wave["risk_tier_counts"] = dict(sorted(risk_counts.items()))
        assigned_targets.update(item["normalized_url"] for item in wave["lanes"])
        covered_raw_indexes.update(raw_indexes)
        waves.append(wave)

    return {
        "version": 1,
        "generated_at": now(),
        "status": "trust-gated-promotion-wave-plan-generated",
        "wave_count": len(COVERAGE_PROMOTION_WAVES),
        "total_targets": len(assigned_targets),
        "unique_targets_assigned": len(assigned_targets),
        "raw_entries_covered": len(covered_raw_indexes),
        "live_install_eligible_count": 0,
        "assignment_rule": (
            "Each normalized target is assigned to exactly one promotion wave by source URL, "
            "category, artifact type, and subresource text; Composio, Pedronauck, OpenSpec, "
            "and Obsidian sources are reserved for final reconciliation."
        ),
        "waves": waves,
    }


def write_promotion_wave_report(plan: dict[str, Any]) -> None:
    status = plan.get("status", "trust-gated-promotion-wave-plan-generated")
    wave_count = plan.get("wave_count", len(plan["waves"]))
    assigned_count = plan.get("unique_targets_assigned", plan["total_targets"])
    raw_count = plan.get(
        "raw_entries_covered",
        len({index for wave in plan["waves"] for index in wave.get("raw_indexes", [])}),
    )
    live_install_eligible = plan.get("live_install_eligible_count", 0)
    lines = [
        "# Candidate Corpus Promotion Wave Plan",
        "",
        f"- Status: `{status}`",
        f"- Waves: {wave_count}",
        f"- Unique targets assigned: {assigned_count}",
        f"- Raw entries covered: {raw_count}",
        f"- Live install eligible: {live_install_eligible}",
        "",
        "## Waves",
        "",
    ]
    for wave in plan["waves"]:
        coverage_counts = wave.get("coverage_status_counts")
        if coverage_counts is None:
            coverage_counts = Counter(target["coverage_status"] for target in wave.get("targets", []))
        risk_counts = wave.get("risk_tier_counts")
        if risk_counts is None:
            risk_counts = Counter(target["risk_tier"] for target in wave.get("targets", []))
        coverage = ", ".join(f"{key}={value}" for key, value in coverage_counts.items()) or "none"
        risks = ", ".join(f"{key}={value}" for key, value in risk_counts.items()) or "none"
        lines.extend([
            f"### {wave['wave_id']} {wave['name']}",
            "",
            f"- Objective: {wave.get('objective', wave.get('description', 'Promotion wave'))}",
            f"- Unique targets: {wave.get('unique_target_count', wave['target_count'])}",
            f"- Raw entries: {wave.get('raw_entry_count', len(wave.get('raw_indexes', [])))}",
            f"- Coverage: {coverage}",
            f"- Risk tiers: {risks}",
            "- Promotion policy: read-only source research first; mutation only after all trust gates pass.",
            "",
        ])
    (MANIFEST_DIR / "promotion-wave-plan.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_research_state_report(progress: dict[str, Any], graph: dict[str, Any]) -> None:
    lines = [
        "# Candidate Corpus Full Integration State",
        "",
        f"- Phase: `{progress['phase']}`",
        f"- Complete: `{str(progress['complete']).lower()}`",
        f"- Raw research lanes: {graph['raw_lane_count']}",
        f"- Unique target synthesis lanes: {graph['unique_target_lane_count']}",
        f"- Raw leaf checks: {graph['raw_leaf_check_count']}",
        f"- Unique synthesis leaf checks: {graph['unique_leaf_check_count']}",
        f"- Total leaf checks: {graph['total_leaf_check_count']}",
        f"- Live install eligible: {graph['live_install_eligible_count']}",
        "- Existing integration coverage: "
        + ", ".join(f"{key}={value}" for key, value in progress["existing_integration_coverage"].items()),
        f"- Ready for repo promotion: {progress['promotion_readiness']['ready_for_repo_promotion']}",
        f"- Blocked until trust gates: {progress['promotion_readiness']['blocked_until_trust_gates']}",
        "",
        "## Promotion Waves",
        "",
        *[f"- `{wave_id}`: {count} targets" for wave_id, count in progress["promotion_waves"].items()],
        "",
        "## Current Gate",
        "",
        (
            "Every candidate is represented, but live install and repo-native promotion remain blocked until "
            "source-list, license, security, attribution, auth, and docs-steward gates pass."
        ),
        "",
        "## Next Actions",
        "",
    ]
    lines.extend(f"- {action}" for action in progress["next_actions"])
    (MANIFEST_DIR / "full-integration-state.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def record_github_metadata(record: dict[str, Any]) -> dict[str, Any]:
    metadata = record.get("github_metadata_packet")
    if isinstance(metadata, dict):
        return metadata
    capture = record.get("source_capture_packet", {})
    return {
        "status": capture.get("github_api_status") or capture.get("git_status") or "unavailable",
        "error": capture.get("github_api_error") or capture.get("git_error") or "missing github metadata packet",
        "default_branch": capture.get("default_branch", ""),
        "pushed_at": "",
        "updated_at": "",
        "license_spdx_id": "",
        "license_name": "",
        "language": "",
        "topics": [],
        "archived": False,
        "fork": False,
        "private": False,
        "visibility": "",
    }


def docs_surface_counts(records: list[dict[str, Any]]) -> dict[str, int]:
    return {
        surface: sum(surface in record["docs_steward_surfaces"] for record in records)
        for surface in DOCS_SURFACES
    }


def covered_docs_surfaces(records: list[dict[str, Any]]) -> list[str]:
    counts = docs_surface_counts(records)
    return [surface for surface in DOCS_SURFACES if counts[surface] > 0]


def write_matrices(data: dict[str, Any], records: list[dict[str, Any]]) -> dict[str, Any]:
    stats = summary(data, records)
    decisions = unique_decisions(data, records)
    coverage = build_existing_integration_coverage(records)
    wave_plan = build_coverage_promotion_wave_plan(records, coverage)
    graph = build_research_task_graph(data, records, coverage)
    readiness = build_promotion_readiness_queue(decisions, graph)
    wave_queue = build_subagent_wave_queue(records)
    progress = build_full_integration_progress(data, records, decisions, graph, coverage, readiness, wave_plan)
    surface_counts = docs_surface_counts(records)
    covered_surfaces = [surface for surface in DOCS_SURFACES if surface_counts[surface] > 0]
    omitted_surfaces = [surface for surface in DOCS_SURFACES if surface_counts[surface] == 0]
    write_json("all-records.json", {"version": 1, "generated_at": now(), "records": records})
    write_json(
        "integration-decisions.json", {"version": 1, "generated_at": now(), "summary": stats, "decisions": decisions}
    )
    write_json("existing-integration-coverage.json", coverage)
    write_json("promotion-wave-plan.json", wave_plan)
    write_json("research-task-graph.json", graph)
    write_json("research-packet-schema.json", build_research_packet_schema())
    write_json("promotion-readiness-queue.json", readiness)
    write_json("subagent-wave-queue.json", wave_queue)
    write_json("full-integration-progress.json", progress)
    write_promotion_wave_report(wave_plan)
    write_research_state_report(progress, graph)
    write_json(
        "source-research-matrix.json",
        {
            "version": 1,
            "items": [
                {
                    "raw_index": r["raw_index"],
                    "source_name": r["source_name"],
                    "claims": r["deep_research_claims"],
                    "capture": r["source_capture_packet"],
                }
                for r in records
            ],
        },
    )
    github_items_by_source: dict[str, dict[str, Any]] = {}
    for record in records:
        metadata = record_github_metadata(record)
        key = record["canonical_source"] or record["source_name"]
        github_items_by_source.setdefault(
            key,
            {
                "source": key,
                "source_name": record["source_name"],
                "normalized_url": record["normalized_url"],
                "status": metadata["status"],
                "error": metadata["error"],
                "default_branch": metadata.get("default_branch", ""),
                "pushed_at": metadata.get("pushed_at", ""),
                "updated_at": metadata.get("updated_at", ""),
                "license": record["license"],
                "license_spdx_id": metadata.get("license_spdx_id", ""),
                "license_name": metadata.get("license_name", ""),
                "language": metadata.get("language", ""),
                "topics": metadata.get("topics", []),
                "archived": metadata.get("archived", False),
                "fork": metadata.get("fork", False),
                "private": metadata.get("private", False),
                "visibility": metadata.get("visibility", ""),
                "raw_indexes": [],
            },
        )
        github_items_by_source[key]["raw_indexes"].append(record["raw_index"])
    write_json(
        "github-metadata-audit.json",
        {
            "version": 1,
            "generated_at": now(),
            "source_count": len(github_items_by_source),
            "status_counts": dict(sorted(Counter(item["status"] for item in github_items_by_source.values()).items())),
            "license_counts": dict(
                sorted(Counter(item["license"] for item in github_items_by_source.values()).items())
            ),
            "items": sorted(github_items_by_source.values(), key=lambda item: item["source"].lower()),
        },
    )
    write_json(
        "source-support-audit.json",
        {
            "version": 1,
            "items": [
                {
                    "raw_index": r["raw_index"],
                    "source_name": r["source_name"],
                    "source_support_matrix": r["source_support_matrix"],
                }
                for r in records
            ],
        },
    )
    write_json(
        "security-audit-matrix.json",
        {
            "version": 1,
            "items": [
                {
                    "raw_index": r["raw_index"],
                    "source_name": r["source_name"],
                    "risk_tier": r["risk_tier"],
                    "security_packet": r["security_packet"],
                }
                for r in records
            ],
        },
    )
    write_json(
        "license-attribution-matrix.json",
        {
            "version": 1,
            "items": [
                {
                    "raw_index": r["raw_index"],
                    "source_name": r["source_name"],
                    "license": r["license"],
                    "attribution_notes": r["attribution_notes"],
                }
                for r in records
            ],
        },
    )
    write_json(
        "compliance-auth-matrix.json",
        {
            "version": 1,
            "items": [
                {
                    "raw_index": r["raw_index"],
                    "source_name": r["source_name"],
                    "auth_required": r["auth_required"],
                    "env_vars_or_credentials": r["env_vars_or_credentials"],
                }
                for r in records
            ],
        },
    )
    write_json(
        "docs-impact-matrix.json",
        {
            "version": 1,
            "surfaces": covered_surfaces,
            "omitted_zero_count_surfaces": omitted_surfaces,
            "items": [
                {
                    "raw_index": r["raw_index"],
                    "source_name": r["source_name"],
                    "decision": r["install_or_integration_decision"],
                    "docs_steward_surfaces": r["docs_steward_surfaces"],
                }
                for r in records
            ],
        },
    )
    write_json(
        "auth-matrix.json",
        {
            "version": 1,
            "items": [
                {
                    "raw_index": r["raw_index"],
                    "source_name": r["source_name"],
                    "env_vars_or_credentials": r["env_vars_or_credentials"],
                    "safety_notes": r["safety_notes"],
                }
                for r in records
                if r["auth_required"]
            ],
        },
    )
    write_json(
        "dedupe-clusters.json",
        {
            "version": 1,
            "exact_duplicates": data["duplicate_groups"],
            "clusters": [{"id": cid, "name": name, "match": match} for cid, name, match in CLUSTERS],
        },
    )
    write_json(
        "docs-steward-surface-map.json",
        {
            "version": 1,
            "surfaces": [
                {
                    "surface": surface,
                    "candidate_count": sum(surface in r["docs_steward_surfaces"] for r in records),
                    "status": "packet-generated",
                }
                for surface in covered_surfaces
            ],
            "omitted_zero_count_surfaces": omitted_surfaces,
        },
    )
    write_reports(stats, decisions, records, graph, progress)
    return stats


def write_reports(
    stats: dict[str, Any],
    decisions: list[dict[str, Any]],
    records: list[dict[str, Any]],
    graph: dict[str, Any],
    progress: dict[str, Any],
) -> None:
    github_status_counts = Counter(r["github_metadata_packet"]["status"] for r in records)
    github_license_counts = Counter(r["license"] for r in records)
    surface_counts = docs_surface_counts(records)
    covered_surfaces = [surface for surface in DOCS_SURFACES if surface_counts[surface] > 0]
    omitted_surfaces = [surface for surface in DOCS_SURFACES if surface_counts[surface] == 0]
    risky = [r for r in records if r["risk_tier"] in {"quarantine", "review-required"}]
    skipped = [
        r
        for r in records
        if r["install_or_integration_decision"].startswith("skip")
        or r["install_or_integration_decision"] == "quarantine"
    ]
    source_list_evidence_path = MANIFEST_DIR / "safe-wave-source-list-evidence.json"
    if source_list_evidence_path.exists():
        source_list_evidence_raw = json.loads(source_list_evidence_path.read_text(encoding="utf-8"))
    else:
        source_list_evidence_raw = {"items": [], "install_command_count": 0, "summary": {}}
    source_list_evidence: dict[str, Any] = (
        source_list_evidence_raw if isinstance(source_list_evidence_raw, dict) else {}
    )
    source_list_items_raw = source_list_evidence.get("items", [])
    source_list_items = source_list_items_raw if isinstance(source_list_items_raw, list) else []
    source_list_summary_raw = source_list_evidence.get("summary", {})
    source_list_summary: dict[str, Any] = (
        source_list_summary_raw if isinstance(source_list_summary_raw, dict) else {}
    )
    source_list_status_counts_raw = source_list_summary.get("status_counts", {})
    source_list_status_counts: dict[str, Any] = (
        source_list_status_counts_raw if isinstance(source_list_status_counts_raw, dict) else {}
    )
    source_list_count_raw = source_list_summary.get("recorded_target_count")
    source_list_count = source_list_count_raw if isinstance(source_list_count_raw, int) else len(source_list_items)
    source_list_found = source_list_status_counts.get("source-list-found", 0)
    source_list_other = source_list_count - source_list_found
    source_list_line = (
        f"- Source-list evidence: {source_list_count} list-only probes recorded "
        f"({source_list_found} found, {source_list_other} blocked/error/no-skills), "
        f"{source_list_evidence.get('install_command_count', 0)} installs"
    )
    decision_log = [
        "# Candidate Corpus July 2026 Decision Log",
        "",
        f"- Raw candidates: {stats['raw_count']}",
        f"- Unique normalized targets: {stats['unique_count']}",
        f"- Duplicates deduped: {stats['duplicates_deduped']}",
        "",
        "## Risky Or Quarantined",
        "",
        *[f"- `{r['raw_index']:03d}` `{r['source_name']}`: {r['risk_tier']} - {r['reason']}" for r in risky],
        "",
        "## Skipped",
        "",
        *[
            (
                f"- `{r['raw_index']:03d}` `{r['source_name']}`: "
                f"{r['install_or_integration_decision']} - {r['skipped_reason']}"
            )
            for r in skipped
        ],
    ]
    (MANIFEST_DIR / "risky-skipped-deduped-decision-log.md").write_text(
        "\n".join(decision_log) + "\n", encoding="utf-8"
    )
    validation_report = [
        "# Candidate Corpus July 2026 Validation Report",
        "",
        f"- Raw candidates processed: {stats['raw_count']}",
        f"- Unique normalized targets: {stats['unique_count']}",
        f"- Added count: {stats['added_count']}",
        f"- Catalog authoring rows added: {stats['catalog_authoring_added_count']}",
        f"- Live install additions: {stats['live_install_added_count']}",
        f"- Adapted count: {stats['adapted_count']}",
        f"- Reference-only count: {stats['reference_only_count']}",
        f"- Skipped count: {stats['skipped_count']}",
        f"- Duplicates deduped: {stats['duplicates_deduped']}",
        f"- Raw research lanes: {graph['raw_lane_count']}",
        f"- Unique target synthesis lanes: {graph['unique_target_lane_count']}",
        f"- Research leaf checks tracked: {graph['total_leaf_check_count']}",
        f"- Raw promotion research packets: {stats['raw_count']}",
        f"- Unique promotion research packets: {stats['unique_count']}",
        "- Live install command preview: 0 commands emitted",
        source_list_line,
        "- GitHub metadata status: "
        + ", ".join(f"{key}={value}" for key, value in sorted(github_status_counts.items())),
        f"- GitHub license labels detected: {len(github_license_counts)}",
        "- Existing integration coverage: "
        + ", ".join(f"{key}={value}" for key, value in progress["existing_integration_coverage"].items()),
        "- Promotion waves: " + ", ".join(f"{key}={value}" for key, value in progress["promotion_waves"].items()),
        f"- Full integration phase: `{progress['phase']}`",
        f"- Live install status: `{progress['live_install']['status']}`",
        "",
        "## Observed Generated Evidence",
        "",
        "- Generator emitted manifest, matrix, packet, report, and catalog-authoring artifacts from local inputs.",
        "- Candidate code was not installed, executed, vendored, adapted, or enabled.",
        "- Live install command preview emitted 0 commands.",
        (
            "- Trust gates remain open for source-list evidence, license, security, attribution, auth, "
            "docs-steward, and target-specific validation."
        ),
        "",
        "## Command Checklist",
        "",
        "- `uv run python scripts/generate_candidate_corpus_shards.py --check-coverage`",
        "- `uv run python scripts/promote_candidate_corpus.py --write --check-coverage`",
        "- `uv run pytest tests/test_candidate_corpus.py -q`",
        (
            "- `uv run ruff check scripts/generate_candidate_corpus_shards.py "
            "scripts/promote_candidate_corpus.py tests/test_candidate_corpus.py`"
        ),
        "- `uv run wagents validate`",
        "- `uv run wagents docs generate --no-installed`",
        "- `uv run wagents readme`",
        "- `uv run wagents readme --check`",
        "- `uv run wagents skills sync --dry-run`",
        "- `uv run wagents docs lint`",
        "- `uv run wagents docs build`",
        (
            "- `OPENSPEC_TELEMETRY=0 npx -y @fission-ai/openspec@latest "
            "validate integrate-candidate-corpus-jul2026 --strict --json`"
        ),
        "- `uv run wagents openspec validate`",
    ]
    (MANIFEST_DIR / "validation-report.md").write_text("\n".join(validation_report) + "\n", encoding="utf-8")
    final_report = [
        "# Candidate Corpus July 2026 Final Review Report",
        "",
        f"- Total raw candidates processed: {stats['raw_count']}",
        f"- Total unique normalized targets: {stats['unique_count']}",
        f"- Added count: {stats['added_count']}",
        f"- Catalog authoring rows added: {stats['catalog_authoring_added_count']}",
        f"- Live install additions: {stats['live_install_added_count']}",
        f"- Adapted count: {stats['adapted_count']}",
        f"- Reference-only count: {stats['reference_only_count']}",
        f"- Skipped count: {stats['skipped_count']}",
        f"- Duplicates deduped: {stats['duplicates_deduped']}",
        f"- Auth requirements: {stats['auth_required_count']} candidates require auth or credential-boundary review.",
        f"- Research task graph: {graph['raw_lane_count']} raw lanes, "
        f"{graph['unique_target_lane_count']} synthesis lanes, "
        f"{graph['total_leaf_check_count']} leaf checks.",
        "- GitHub metadata audit: "
        + ", ".join(f"{key}={value}" for key, value in sorted(github_status_counts.items()))
        + f"; license labels={len(github_license_counts)}.",
        "- Existing integration coverage: "
        + ", ".join(f"{key}={value}" for key, value in progress["existing_integration_coverage"].items()),
        "- Promotion waves: " + ", ".join(f"{key}={value}" for key, value in progress["promotion_waves"].items()),
        f"- Full integration phase: `{progress['phase']}`; live install remains "
        f"`{progress['live_install']['status']}`.",
        "- Promotion packet outputs: 293 raw packets, 289 unique packets, 289 gate rows, 0 install commands.",
        source_list_line,
        (
            "- Generator-owned docs-steward packets emitted: manifest surface map, auth matrix, decision log, "
            "catalog authoring summary, existing integration coverage, promotion wave plan, research task "
            "graph, research packet schema, raw/unique research packets, promotion gate matrix, live install "
            "command preview, GitHub metadata audit, subagent wave queue, promotion readiness queue, "
            "integration progress, changelog entry, validation report, and final review report."
        ),
        (
            "- Covered docs-steward surfaces: "
            + ", ".join(f"`{surface}`={surface_counts[surface]}" for surface in covered_surfaces)
            + "."
        ),
        (
            "- Zero-count docs-steward surfaces omitted from covered lists: "
            + (", ".join(f"`{surface}`" for surface in omitted_surfaces) if omitted_surfaces else "none")
            + "."
        ),
        "- Validation command checklist: see `validation-report.md`; execution results must be recorded by the runner.",
        (
            "- Review findings addressed in generator-owned outputs: coverage/schema gates are automated, "
            "catalog-only rows publish no install/use commands, and generated reports no longer imply "
            "unobserved validation passes."
        ),
        (
            "- Unresolved risks: source-list, license, security, attribution, auth, and docs-steward "
            "trust gates remain required before live install, adaptation, or repo promotion."
        ),
        "- Final commit hash: no commit made by this script.",
        "",
        "## Suggested PR Title",
        "",
        "chore: add candidate corpus July 2026 intake manifests",
        "",
        "## Suggested PR Body",
        "",
        (
            "- Adds deterministic candidate corpus normalization, sharding, coverage, generated catalog "
            "authoring rows, GitHub metadata audit, and manifest generation."
        ),
        (
            "- Records public Git/GitHub metadata, source-support, security, license, compliance/auth, "
            "docs impact, dedupe, and decision outputs."
        ),
        (
            "- Keeps third-party sources discovery-only pending source-list evidence, "
            "license review, security review, and docs-steward gates."
        ),
    ]
    (MANIFEST_DIR / "final-review-report.md").write_text("\n".join(final_report) + "\n", encoding="utf-8")
    changelog = [
        "# Changelog Entry: Candidate Corpus July 2026 Intake",
        "",
        "- Added tracked candidate-corpus raw URL manifest and deterministic processing pipeline.",
        "- Added one non-installable curated-external catalog authoring row for every unique normalized target.",
        "- Added GitHub repository metadata audit with license labels, default branches, and pushed dates.",
        (
            "- Added generated source research, source support, security, license, "
            "compliance/auth, docs impact, dedupe, decisions, validation, and review outputs."
        ),
        (
            "- Added full-integration research graph, packet schema, progress JSON, and state report "
            "for every raw candidate and normalized target."
        ),
        (
            "- Added raw and unique promotion research packets, promotion gate matrix, and live install "
            "command preview with zero emitted commands."
        ),
        (
            f"- Added source-list evidence for {source_list_count} candidates "
            f"with {source_list_evidence.get('install_command_count', 0)} installs."
        ),
        "- Added trust-gated promotion readiness and parallel subagent wave queue artifacts.",
        (
            "- Added exact existing-catalog coverage so already integrated curated sources are not "
            "duplicated by candidate-corpus rows."
        ),
        "- Added target-level promotion wave plan for serialized integration waves.",
        (
            "- Kept all third-party candidates discovery-only; no live install, execution, "
            "vendoring, or default enablement was performed."
        ),
    ]
    (MANIFEST_DIR / "changelog-entry.md").write_text("\n".join(changelog) + "\n", encoding="utf-8")
    docs_summary = ["# Docs-Steward Surface Summary", "", "Generated docs-steward packets cover:", ""]
    docs_summary.extend(f"- `{surface}`: {surface_counts[surface]} candidates" for surface in covered_surfaces)
    docs_summary.append("")
    docs_summary.append("Zero-count docs-steward surfaces omitted from covered lists:")
    if omitted_surfaces:
        docs_summary.extend(f"- `{surface}`: 0 candidates" for surface in omitted_surfaces)
    else:
        docs_summary.append("- none")
    docs_summary.append("")
    docs_summary.append(
        "Generated docs and catalog pages must still be regenerated from source during any future promotion wave."
    )
    docs_summary.append("")
    docs_summary.append(
        "Full integration tracking lives in `existing-integration-coverage.json`, `promotion-wave-plan.json`, "
        "`research-task-graph.json`, `research-packet-schema.json`, `raw-research-packets.json`, "
        "`unique-target-research-packets.json`, `promotion-gate-matrix.json`, "
        "`live-install-command-preview.json`, `github-metadata-audit.json`, `promotion-readiness-queue.json`, "
        "`subagent-wave-queue.json`, `safe-wave-source-list-evidence.json`, "
        "`full-integration-progress.json`, and `full-integration-state.md`."
    )
    (MANIFEST_DIR / "docs-steward-surface-summary.md").write_text("\n".join(docs_summary) + "\n", encoding="utf-8")
    lines = [
        "# Unique Target Decisions",
        "",
        "| Source | Raw indexes | Decision | Reason |",
        "| --- | ---: | --- | --- |",
    ]
    for item in decisions:
        raw_indexes = ", ".join(str(index) for index in item["raw_indexes"])
        lines.append(
            f"| `{item['source_name']}` | {raw_indexes} | `{item['decision']}` | {item['reason'].replace('|', '\\|')} |"
        )
    (MANIFEST_DIR / "unique-target-decisions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_record_files(records: list[dict[str, Any]]) -> None:
    for path in RECORDS_DIR.glob("*.json"):
        path.unlink()
    for record in records:
        path = RECORDS_DIR / f"{record['raw_index']:03d}-{slugify(record['source_name'])}.json"
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def rebuild_records_from_cache(data: dict[str, Any], cached_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    catalog_rows = catalog_authoring_rows()
    mcp_text = load_text(MCP_REGISTRY)
    plugin_text = load_text(PLUGIN_REGISTRY)
    cached_by_raw_index = {record["raw_index"]: record for record in cached_records}
    rebuilt = []
    for entry in data["entries"]:
        cached = cached_by_raw_index[entry["raw_index"]]
        capture = cached.get("source_capture_packet", {})
        meta = {
            "status": str(capture.get("git_status") or "ok"),
            "head_sha": str(cached.get("inspected_commit_sha") or ""),
            "default_branch": str(capture.get("default_branch") or ""),
            "error": str(capture.get("git_error") or ""),
        }
        rebuilt.append(
            build_record(
                entry,
                catalog_rows,
                mcp_text,
                plugin_text,
                meta,
                record_github_metadata(cached),
            )
        )
    return sorted(rebuilt, key=lambda record: record["raw_index"])


def emit_all(*, no_network: bool = False) -> dict[str, Any]:
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    RECORDS_DIR.mkdir(parents=True, exist_ok=True)
    data = normalize()
    if no_network and (MANIFEST_DIR / "all-records.json").exists():
        cached_records = json.loads((MANIFEST_DIR / "all-records.json").read_text(encoding="utf-8"))["records"]
        records = rebuild_records_from_cache(data, cached_records)
    else:
        records = build_records(data)
    write_record_files(records)
    write_shards(data)
    write_catalog_authoring(records)
    stats = write_matrices(data, records)
    return {"normalized": data, "records": records, "summary": stats}


def check_coverage() -> int:
    if not RAW_URLS.exists() or not NORMALIZED.exists() or not (MANIFEST_DIR / "integration-decisions.json").exists():
        print("Missing raw, normalized, or decision artifacts", file=sys.stderr)
        return 1
    raw_count = len(read_raw_urls())
    normalized = json.loads(NORMALIZED.read_text(encoding="utf-8"))
    decisions = json.loads((MANIFEST_DIR / "integration-decisions.json").read_text(encoding="utf-8"))
    record_count = len(list(RECORDS_DIR.glob("*.json"))) if RECORDS_DIR.exists() else 0
    unique_count = len(normalized.get("unique_targets", []))
    decision_count = len(decisions.get("decisions", []))
    ok = (
        raw_count == EXPECTED_RAW_COUNT
        and unique_count == EXPECTED_UNIQUE_COUNT
        and record_count == EXPECTED_RAW_COUNT
        and decision_count == EXPECTED_UNIQUE_COUNT
    )
    payload = {
        "raw": raw_count,
        "unique": unique_count,
        "records": record_count,
        "decisions": decision_count,
        "ok": ok,
    }
    print(json.dumps(payload, indent=2))
    return 0 if ok else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit-all", action="store_true")
    parser.add_argument("--normalize", action="store_true")
    parser.add_argument("--check-coverage", action="store_true")
    parser.add_argument("--no-network", action="store_true", help="Reuse existing records when available.")
    args = parser.parse_args()
    if args.normalize:
        payload = normalize()
        print(json.dumps({"raw": payload["raw_count"], "unique": payload["unique_count"]}, indent=2))
        return 0
    if args.emit_all:
        payload = emit_all(no_network=args.no_network)
        print(json.dumps(payload["summary"], indent=2))
        return 0
    if args.check_coverage:
        return check_coverage()
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
