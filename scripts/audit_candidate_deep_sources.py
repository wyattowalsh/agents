#!/usr/bin/env python3
"""Collect non-executing deep source evidence for the July 2026 corpus.

The audit uses GitHub API reads only. It does not clone repositories, run
package scripts, start MCP servers, import candidate code, or install anything.
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

from wagents.candidate_auth import extract_auth_env_names

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
OUTPUT = MANIFEST_DIR / "deep-source-audit.json"
SUMMARY = MANIFEST_DIR / "deep-source-audit-summary.md"
EXPECTED_RAW_COUNT = 293
EXPECTED_UNIQUE_COUNT = 289

MAX_WORKERS = 8
API_TIMEOUT_SECONDS = 35
MAX_FETCHED_FILES_PER_TARGET = 30
MAX_DECODE_BYTES = 250_000

PACKAGE_BASENAMES = {
    "package.json",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "requirements.txt",
    "requirements-dev.txt",
    "cargo.toml",
    "go.mod",
    "deno.json",
    "deno.jsonc",
    "bunfig.toml",
    "uv.lock",
    "poetry.lock",
    "pnpm-lock.yaml",
    "yarn.lock",
    "justfile",
    "makefile",
    "dockerfile",
    "compose.yaml",
    "compose.yml",
}

SCRIPT_EXTENSIONS = {".sh", ".bash", ".zsh", ".ps1", ".cmd", ".bat"}

SECURITY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("package-install-hook", re.compile(r"\b(preinstall|install|postinstall|prepare)\b", re.I)),
    ("network-download", re.compile(r"\b(curl|wget|invoke-webrequest|fetch\(|requests\.|http://|https://)", re.I)),
    ("dynamic-execution", re.compile(r"\b(eval|exec|os\.system|subprocess|child_process|spawn\(|popen)\b", re.I)),
    ("destructive-filesystem", re.compile(r"\b(rm\s+-rf|del\s+/[fsq]|chmod\s+777|sudo\s+rm|mkfs|diskutil)\b", re.I)),
    (
        "credential-keyword",
        re.compile(r"\b(api[_-]?key|token|secret|password|oauth|client_secret|private[_-]?key)\b", re.I),
    ),
    ("telemetry", re.compile(r"\b(telemetry|analytics|tracking|sentry|posthog|segment)\b", re.I)),
]

AUTH_PATTERNS = re.compile(
    r"\b(api[_-]?key|token|oauth|client_secret|service_account|database_url|connection_string|"
    r"aws_|gcp_|google_|slack_|notion_|datadog_|langsmith_|langfuse_|zotero_|app_store|"
    r"asc_|stripe_|openai_|anthropic_|xai_)\b",
    re.I,
)

AUTH_SOURCE_OVERRIDES: dict[str, tuple[str, ...]] = {
    "papersflow-ai/papersflow-codex-plugin": ("PAPERSFLOW_OAUTH_ACCOUNT",),
}


def now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def run_gh_json(endpoint: str) -> tuple[dict[str, Any] | list[Any] | None, dict[str, Any]]:
    cmd = ["gh", "api", endpoint]
    try:
        result = subprocess.run(
            cmd,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=API_TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return None, {"ok": False, "status": "timeout", "endpoint": endpoint}
    stderr = result.stderr.strip()
    if result.returncode != 0:
        return None, {
            "ok": False,
            "status": "error",
            "endpoint": endpoint,
            "exit_code": result.returncode,
            "stderr_excerpt": stderr[:300],
        }
    try:
        return json.loads(result.stdout), {"ok": True, "status": "ok", "endpoint": endpoint}
    except json.JSONDecodeError as exc:
        return None, {"ok": False, "status": "json-error", "endpoint": endpoint, "error": str(exc)}


def decode_contents_payload(payload: Any) -> str:
    if not isinstance(payload, dict):
        return ""
    if payload.get("type") != "file":
        return ""
    size = payload.get("size")
    if isinstance(size, int) and size > MAX_DECODE_BYTES:
        return ""
    encoded = payload.get("content")
    if not isinstance(encoded, str):
        return ""
    try:
        return base64.b64decode(encoded, validate=False).decode("utf-8", errors="replace")
    except (ValueError, OSError):
        return ""


def contents_endpoint(owner: str, repo: str, path: str, ref: str) -> str:
    encoded_path = quote(path, safe="/")
    encoded_ref = quote(ref, safe="")
    return f"repos/{owner}/{repo}/contents/{encoded_path}?ref={encoded_ref}"


def tree_endpoint(owner: str, repo: str, ref: str) -> str:
    encoded_ref = quote(ref, safe="")
    return f"repos/{owner}/{repo}/git/trees/{encoded_ref}?recursive=1"


def latest_release_endpoint(owner: str, repo: str) -> str:
    return f"repos/{owner}/{repo}/releases/latest"


def license_endpoint(owner: str, repo: str, ref: str) -> str:
    encoded_ref = quote(ref, safe="")
    return f"repos/{owner}/{repo}/license?ref={encoded_ref}"


def is_relevant_path(path: str, subpath: str) -> bool:
    if not subpath:
        return True
    prefix = subpath.rstrip("/") + "/"
    return path == subpath or path.startswith(prefix)


def relative_to_subpath(path: str, subpath: str) -> str:
    if not subpath:
        return path
    prefix = subpath.rstrip("/") + "/"
    return path[len(prefix) :] if path.startswith(prefix) else path


def choose_readme(paths: list[str], subpath: str) -> str:
    readmes = [path for path in paths if Path(path).name.lower().startswith("readme")]
    scoped = [path for path in readmes if is_relevant_path(path, subpath)]
    for path in sorted(scoped, key=lambda p: (relative_to_subpath(p, subpath).count("/"), p.lower())):
        return path
    for path in sorted(readmes, key=lambda p: (p.count("/"), p.lower())):
        return path
    return ""


def package_candidate_paths(paths: list[str], subpath: str) -> list[str]:
    candidates: list[str] = []
    for path in paths:
        if not is_relevant_path(path, subpath):
            continue
        basename = Path(path).name.lower()
        suffix = Path(path).suffix.lower()
        if (
            basename in PACKAGE_BASENAMES
            or suffix in SCRIPT_EXTENSIONS
            or "/scripts/" in f"/{path.lower()}"
            or basename in {"skill.md", "skill.json", "agent.md", "mcp.json", "plugin.json"}
        ):
            candidates.append(path)
    return sorted(candidates, key=lambda p: (relative_to_subpath(p, subpath).count("/"), p.lower()))[
        :MAX_FETCHED_FILES_PER_TARGET
    ]


def classify_artifacts(paths: list[str], topics: list[str], language: str) -> list[str]:
    text = "\n".join(path.lower() for path in paths) + "\n" + " ".join(topic.lower() for topic in topics)
    artifacts: set[str] = set()
    if "skill.md" in text or "/skills/" in text or "agent-skills" in text or "claude-skill" in text:
        artifacts.add("skill")
    if "mcp" in text or "fastmcp" in text or "modelcontextprotocol" in text:
        artifacts.add("mcp-server")
    if "plugin" in text or ".codex-plugin" in text or ".claude-plugin" in text or "opencode" in text:
        artifacts.add("plugin")
    if "/agents/" in text or "agent.md" in text or "agent" in text:
        artifacts.add("agent")
    if any(marker in text for marker in ("cli", "bin/", "console_scripts", "commander", "click", "typer")):
        artifacts.add("cli-tool")
    if language:
        artifacts.add("library")
    if "awesome" in text:
        artifacts.add("docs-reference")
    if not artifacts:
        artifacts.add("docs-reference")
    return sorted(artifacts)


def scan_security(fetched_files: list[dict[str, Any]], paths: list[str]) -> dict[str, Any]:
    matches: dict[str, list[str]] = defaultdict(list)
    for path in paths:
        lower_path = path.lower()
        for label, pattern in SECURITY_PATTERNS:
            if pattern.search(lower_path):
                matches[label].append(path)
    for fetched in fetched_files:
        path = str(fetched.get("path", ""))
        text = str(fetched.get("text", ""))
        for label, pattern in SECURITY_PATTERNS:
            if pattern.search(text):
                matches[label].append(path)
    deduped = {label: sorted(set(values))[:20] for label, values in sorted(matches.items())}
    return {
        "candidate_code_executed": False,
        "scan_scope": "GitHub metadata, tree paths, README/license/package/script text fetched through gh api",
        "matched_indicators": deduped,
        "indicator_count": sum(len(values) for values in deduped.values()),
        "requires_manual_review": bool(deduped),
    }


def detect_auth(fetched_files: list[dict[str, Any]], paths: list[str], source_name: str) -> dict[str, Any]:
    haystack = "\n".join(paths + [str(file.get("text", "")) for file in fetched_files])
    env_vars = sorted(set(extract_auth_env_names(haystack)) | set(AUTH_SOURCE_OVERRIDES.get(source_name.lower(), ())))
    auth_required = bool(AUTH_PATTERNS.search(haystack)) or bool(env_vars)
    risk_sources = [source_name.lower(), haystack.lower()]
    if any(
        marker in " ".join(risk_sources)
        for marker in (
            "aws",
            "app-store",
            "googleworkspace",
            "datadog",
            "langsmith",
            "langfuse",
            "zotero",
            "slack",
            "notion",
            "supabase",
            "database",
            "finance",
            "ads",
            "sales",
            "outbound",
        )
    ):
        auth_required = True
    if auth_required and not env_vars:
        env_vars = ["PLACEHOLDER_ONLY_REVIEW_REQUIRED"]
    return {
        "auth_required": auth_required,
        "env_vars_or_credentials": env_vars if auth_required else [],
        "credential_policy": "Tracked docs use placeholders only; real credentials stay user-owned and local.",
    }


def summarize_package_files(fetched_files: list[dict[str, Any]]) -> dict[str, Any]:
    package_json_scripts: dict[str, list[str]] = {}
    for fetched in fetched_files:
        path = str(fetched.get("path", ""))
        text = str(fetched.get("text", ""))
        if Path(path).name.lower() == "package.json" and text:
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue
            scripts = payload.get("scripts", {})
            if isinstance(scripts, dict):
                package_json_scripts[path] = sorted(str(key) for key in scripts)
    return {
        "files_reviewed": [str(file.get("path", "")) for file in fetched_files],
        "package_json_scripts": package_json_scripts,
    }


def fetch_file(owner: str, repo: str, path: str, ref: str) -> dict[str, Any]:
    payload, status = run_gh_json(contents_endpoint(owner, repo, path, ref))
    text = decode_contents_payload(payload)
    return {
        "path": path,
        "status": status["status"],
        "api_ok": status["ok"],
        "text": text,
        "byte_count": len(text.encode("utf-8")),
    }


def audit_target(target: dict[str, Any]) -> dict[str, Any]:
    owner = target.get("owner", "")
    repo = target.get("repo", "")
    normalized_url = target["normalized_url"]
    raw_indexes = target["raw_indexes"]
    source_name = target["source_name"]
    subpath = target.get("tree_subpath", "")
    ref = target.get("tree_ref") or target.get("default_branch") or "HEAD"
    default_branch = target.get("default_branch") or ref

    if not owner or not repo:
        return {
            "normalized_url": normalized_url,
            "source_name": source_name,
            "raw_indexes": raw_indexes,
            "status": "terminal-blocker",
            "blockers": ["not a GitHub owner/repo target"],
            "audit_complete": True,
        }

    tree_payload, tree_status = run_gh_json(tree_endpoint(owner, repo, ref))
    if not tree_status["ok"] and ref != default_branch:
        tree_payload, tree_status = run_gh_json(tree_endpoint(owner, repo, default_branch))
        ref = default_branch
    if not tree_status["ok"] or not isinstance(tree_payload, dict):
        return {
            "normalized_url": normalized_url,
            "source_name": source_name,
            "raw_indexes": raw_indexes,
            "status": "terminal-blocker",
            "blockers": [f"tree API unavailable: {tree_status['status']}"],
            "tree_status": tree_status,
            "audit_complete": True,
        }

    tree_items = tree_payload.get("tree", [])
    paths = [
        item.get("path", "")
        for item in tree_items
        if isinstance(item, dict) and item.get("type") == "blob" and isinstance(item.get("path"), str)
    ]
    relevant_paths = [path for path in paths if is_relevant_path(path, subpath)]
    readme_path = choose_readme(paths, subpath)
    package_paths = package_candidate_paths(paths, subpath)
    fetched_files = [fetch_file(owner, repo, path, ref) for path in ([readme_path] if readme_path else [])]
    fetched_files.extend(fetch_file(owner, repo, path, ref) for path in package_paths if path != readme_path)

    license_payload, license_status = run_gh_json(license_endpoint(owner, repo, ref))
    release_payload, release_status = run_gh_json(latest_release_endpoint(owner, repo))
    topics = target.get("topics", [])
    language = str(target.get("language") or "")
    artifacts = classify_artifacts(relevant_paths or paths, topics if isinstance(topics, list) else [], language)
    security = scan_security(fetched_files, relevant_paths or paths)
    auth = detect_auth(fetched_files, relevant_paths or paths, source_name)
    package_summary = summarize_package_files(fetched_files)
    readme_file = next((file for file in fetched_files if file.get("path") == readme_path), None)
    license_spdx = ""
    if isinstance(license_payload, dict):
        license_info = license_payload.get("license")
        if isinstance(license_info, dict):
            license_spdx = str(license_info.get("spdx_id") or "")
    latest_release = ""
    if isinstance(release_payload, dict):
        latest_release = str(release_payload.get("tag_name") or release_payload.get("published_at") or "")

    return {
        "normalized_url": normalized_url,
        "source_name": source_name,
        "raw_indexes": raw_indexes,
        "status": "audited",
        "audit_complete": True,
        "ref": ref,
        "subpath": subpath,
        "tree_status": tree_status,
        "tree_truncated": bool(tree_payload.get("truncated")),
        "file_count": len(paths),
        "scoped_file_count": len(relevant_paths),
        "readme": {
            "path": readme_path,
            "status": readme_file.get("status") if readme_file else "not-found",
            "byte_count": readme_file.get("byte_count", 0) if readme_file else 0,
        },
        "license": {
            "status": license_status["status"],
            "spdx_id": license_spdx,
        },
        "latest_release": {
            "status": release_status["status"],
            "value": latest_release,
        },
        "package_metadata": package_summary,
        "artifact_types_found": artifacts,
        "security_review": security,
        "auth_review": auth,
        "idiosyncrasies": [
            note
            for note in [
                f"tree subpath: {subpath}" if subpath else "",
                "GitHub tree response was truncated" if tree_payload.get("truncated") else "",
                "README not found in scoped tree" if not readme_path else "",
                "package/script files absent in scoped tree" if not package_paths else "",
            ]
            if note
        ],
        "candidate_code_executed": False,
        "reviewer_notes": "Deep source audit used GitHub API reads only; no candidate code was executed.",
    }


def target_rows() -> list[dict[str, Any]]:
    normalized = load_json(MANIFEST_DIR / "normalized-urls.json")
    records = load_json(MANIFEST_DIR / "all-records.json")["records"]
    records_by_url: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        records_by_url[record["normalized_url"].lower()].append(record)

    rows = []
    for normalized_url in normalized["unique_targets"]:
        group = sorted(records_by_url[normalized_url.lower()], key=lambda item: item["raw_index"])
        primary = group[0]
        metadata = primary.get("github_metadata_packet", {})
        source_name = str(primary["source_name"])
        owner = str(primary.get("owner") or "")
        repo = str(primary.get("repo") or "")
        if (not owner or not repo) and "/" in source_name:
            owner, repo = source_name.split("/", 1)
        if not owner or not repo:
            parsed = urlparse(normalized_url)
            parts = [part for part in parsed.path.split("/") if part]
            if len(parts) >= 2:
                owner, repo = parts[0], parts[1]
        rows.append({
            "normalized_url": normalized_url,
            "source_name": source_name,
            "raw_indexes": [item["raw_index"] for item in group],
            "owner": owner,
            "repo": repo,
            "tree_ref": primary.get("tree_ref", ""),
            "tree_subpath": primary.get("tree_subpath", ""),
            "default_branch": metadata.get("default_branch") or primary.get("default_branch", ""),
            "topics": metadata.get("topics", []),
            "language": metadata.get("language", ""),
        })
    return rows


def build_audit(limit: int | None = None) -> dict[str, Any]:
    rows = target_rows()
    if limit is not None:
        rows = rows[:limit]
    items: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(audit_target, row): row for row in rows}
        for future in concurrent.futures.as_completed(future_map):
            row = future_map[future]
            try:
                items.append(future.result())
            except Exception as exc:
                items.append({
                    "normalized_url": row["normalized_url"],
                    "source_name": row["source_name"],
                    "raw_indexes": row["raw_indexes"],
                    "status": "audit-error",
                    "audit_complete": False,
                    "error": str(exc),
                })
    items.sort(key=lambda item: (item.get("raw_indexes") or [9999])[0])
    status_counts = Counter(str(item.get("status", "")) for item in items)
    auth_required = sum(1 for item in items if item.get("auth_review", {}).get("auth_required"))
    security_indicators = sum(1 for item in items if item.get("security_review", {}).get("matched_indicators"))
    return {
        "version": 1,
        "generated_at": now(),
        "audit_method": (
            "GitHub API metadata, recursive tree, README, license, release, and package/script file reads only"
        ),
        "candidate_code_executed": False,
        "expected_raw_count": EXPECTED_RAW_COUNT,
        "expected_unique_count": EXPECTED_UNIQUE_COUNT,
        "unique_target_count": len(items),
        "status_counts": dict(sorted(status_counts.items())),
        "auth_required_count": auth_required,
        "security_indicator_target_count": security_indicators,
        "items": items,
    }


def validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if payload.get("candidate_code_executed") is not False:
        errors.append("candidate_code_executed must be false")
    if payload.get("unique_target_count") != EXPECTED_UNIQUE_COUNT:
        errors.append(f"expected {EXPECTED_UNIQUE_COUNT} unique targets")
    items = payload.get("items", [])
    if not isinstance(items, list):
        return ["items must be a list"]
    if len(items) != EXPECTED_UNIQUE_COUNT:
        errors.append(f"expected {EXPECTED_UNIQUE_COUNT} audit items")
    urls = [item.get("normalized_url") for item in items if isinstance(item, dict)]
    if len(urls) != len(set(urls)):
        errors.append("duplicate normalized_url values in audit")
    incomplete = [
        item.get("normalized_url")
        for item in items
        if not item.get("audit_complete") and item.get("status") not in {"terminal-blocker"}
    ]
    if incomplete:
        errors.append(f"incomplete audit items: {len(incomplete)}")
    return errors


def render_summary(payload: dict[str, Any], errors: list[str]) -> str:
    lines = [
        "# Candidate Corpus Deep Source Audit",
        "",
        f"- Generated at: `{payload.get('generated_at')}`",
        f"- Unique targets audited: {payload.get('unique_target_count')}",
        f"- Candidate code executed: `{str(payload.get('candidate_code_executed')).lower()}`",
        f"- Status counts: `{json.dumps(payload.get('status_counts', {}), sort_keys=True)}`",
        f"- Auth-boundary targets: {payload.get('auth_required_count')}",
        f"- Targets with security indicators: {payload.get('security_indicator_target_count')}",
        f"- Validation errors: {len(errors)}",
        "",
        (
            "This audit uses GitHub API reads for metadata, tree paths, README, license, releases, and selected "
            "package/script files."
        ),
        "It does not clone, install, import, execute, start, or enable candidate code.",
    ]
    if errors:
        lines.extend(["", "## Errors", "", *[f"- {error}" for error in errors]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="Write deep-source audit manifests.")
    parser.add_argument("--check", action="store_true", help="Validate the existing deep-source audit manifest.")
    parser.add_argument("--limit", type=int, default=None, help="Audit only the first N targets for development.")
    args = parser.parse_args()

    if args.check:
        if not OUTPUT.exists():
            print(f"Missing {OUTPUT.relative_to(ROOT)}", file=sys.stderr)
            return 1
        payload = load_json(OUTPUT)
        errors = validate(payload)
        print(
            json.dumps({
                "ok": not errors,
                "errors": errors,
                "unique_target_count": payload.get("unique_target_count"),
            })
        )
        return 0 if not errors else 1

    payload = build_audit(limit=args.limit)
    errors = validate(payload)
    if args.write:
        write_json(OUTPUT, payload)
        SUMMARY.write_text(render_summary(payload, errors), encoding="utf-8")
    print(json.dumps({"ok": not errors, "errors": errors, "unique_target_count": payload.get("unique_target_count")}))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
