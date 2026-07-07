#!/usr/bin/env python3
"""Collect read-only Skills CLI source-list evidence for the July 2026 corpus.

The runner invokes only `npx --yes skills add <source> --list`. It never passes
`--skill`, never calls `wagents skills sync --apply`, and never installs a
candidate into a harness.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import contextlib
import json
import os
import re
import shlex
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / "planning" / "manifests" / "candidate-corpus-jul2026"
EVIDENCE_FILE = "safe-wave-source-list-evidence.json"
EXPECTED_UNIQUE_COUNT = 289
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_CONCURRENCY = 4

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
BOX_NAME_RE = re.compile(r"^\s*[\u2502|]\s{4}([a-z0-9][a-z0-9-]{0,63})\s*$")
BULLET_NAME_RE = re.compile(r"^\s*(?:[-*]|\d+[.)])\s+([a-z0-9][a-z0-9-]{0,63})(?:\s|$)")
PLAIN_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
REPORTED_COUNT_RE = re.compile(r"Found\s+(\d+)\s+skills?", re.IGNORECASE)

VALID_EVIDENCE_STATUSES = {
    "source-list-error",
    "source-list-found",
    "source-list-no-skills-listed",
    "source-list-timeout",
}

EVIDENCE_ITEM_KEYS = [
    "rank",
    "raw_indexes",
    "wave_id",
    "normalized_url",
    "source_name",
    "coverage_status",
    "intake_decision",
    "risk_tier",
    "auth_required",
    "command",
    "exit_code",
    "timed_out",
    "duration_seconds",
    "reported_skill_count",
    "found_skill_count",
    "representative_skills",
    "evidence_status",
    "stderr_excerpt",
    "remaining_blockers",
]
DISALLOWED_EVIDENCE_ITEM_KEYS = {"listed_skills", "stdout_excerpt"}


@dataclass(frozen=True)
class SourceListTask:
    rank: int
    raw_indexes: list[int]
    wave_id: str
    normalized_url: str
    source_name: str
    coverage_status: str
    intake_decision: str
    risk_tier: str
    auth_required: bool


def now() -> str:
    return datetime.now(UTC).isoformat()


def load_json(name: str) -> Any:
    path = MANIFEST_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Missing {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(name: str, payload: Any) -> None:
    path = MANIFEST_DIR / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def clean_cli_output(text: str) -> str:
    text = ANSI_RE.sub("", text)
    text = text.replace("\r", "\n")
    return CONTROL_RE.sub("", text)


def parse_skill_list_output(stdout: str) -> dict[str, Any]:
    """Parse `npx skills add --list` output.

    The current CLI renders a boxed "Available Skills" section where skill names
    appear on lines like `|    workers-best-practices` before indented
    descriptions. The parser also accepts simpler bullet/plain list formats so
    evidence remains stable if the CLI renderer changes.
    """

    cleaned = clean_cli_output(stdout)
    reported_count: int | None = None
    names: list[str] = []
    seen: set[str] = set()
    in_available_section = False
    for raw_line in cleaned.splitlines():
        line = raw_line.rstrip()
        if reported_count is None:
            count_match = REPORTED_COUNT_RE.search(line)
            if count_match:
                reported_count = int(count_match.group(1))
        if "Available Skills" in line:
            in_available_section = True
            continue
        if in_available_section and "Use --skill" in line:
            break
        if not in_available_section:
            continue

        candidates: list[str] = []
        for pattern in (BOX_NAME_RE, BULLET_NAME_RE):
            match = pattern.match(line)
            if match:
                candidates.append(match.group(1))
        stripped = line.strip()
        if PLAIN_NAME_RE.fullmatch(stripped):
            candidates.append(stripped)

        for candidate in candidates:
            if candidate in seen:
                continue
            seen.add(candidate)
            names.append(candidate)
    return {
        "reported_skill_count": reported_count,
        "parsed_skill_count": len(names),
        "listed_skills": names,
    }


def extract_skill_names(stdout: str) -> list[str]:
    return parse_skill_list_output(stdout)["listed_skills"]


def command_for(task: SourceListTask) -> list[str]:
    return ["npx", "--yes", "skills", "add", task.normalized_url, "--list"]


def status_for(
    exit_code: int,
    timed_out: bool,
    found_skill_count: int,
    *,
    reported_skill_count: int | None = None,
) -> str:
    if timed_out:
        return "source-list-timeout"
    if exit_code != 0:
        return "source-list-error"
    if found_skill_count > 0:
        return "source-list-found"
    if reported_skill_count and reported_skill_count > 0:
        return "source-list-error"
    return "source-list-no-skills-listed"


def excerpt(text: str, max_chars: int = 800) -> str:
    cleaned = clean_cli_output(text).strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 3].rstrip() + "..."


def subprocess_text(value: str | bytes | None) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value or ""


def run_command_capture(command: list[str], timeout_seconds: int) -> tuple[int, bool, str, str]:
    """Run a probe command and kill its whole subprocess group on timeout."""

    popen_kwargs: dict[str, Any] = {
        "cwd": ROOT,
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
    }
    if hasattr(os, "setsid"):
        popen_kwargs["start_new_session"] = True

    process = subprocess.Popen(command, **popen_kwargs)
    timed_out = False
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        if hasattr(os, "killpg"):
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
        else:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            if hasattr(os, "killpg"):
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
            else:
                process.kill()
            stdout, stderr = process.communicate()
        stdout = subprocess_text(exc.stdout) + subprocess_text(stdout)
        stderr = subprocess_text(exc.stderr) + subprocess_text(stderr)
        return 124, timed_out, stdout, stderr

    return process.returncode, timed_out, subprocess_text(stdout), subprocess_text(stderr)


def build_tasks() -> list[SourceListTask]:
    wave_plan = load_json("promotion-wave-plan.json")
    tasks: list[SourceListTask] = []
    rank = 0
    for wave in wave_plan["waves"]:
        for target in wave["targets"]:
            rank += 1
            tasks.append(
                SourceListTask(
                    rank=rank,
                    raw_indexes=target["raw_indexes"],
                    wave_id=wave["wave_id"],
                    normalized_url=target["normalized_url"],
                    source_name=target["source_name"],
                    coverage_status=target["coverage_status"],
                    intake_decision=target["intake_decision"],
                    risk_tier=target["risk_tier"],
                    auth_required=target["auth_required"],
                )
            )
    return tasks


def existing_items_by_url() -> dict[str, dict[str, Any]]:
    existing = load_json(EVIDENCE_FILE) if (MANIFEST_DIR / EVIDENCE_FILE).exists() else {"items": []}
    return {item["normalized_url"].lower(): item for item in existing.get("items", [])}


def task_matches_filters(task: SourceListTask, waves: set[str], risk_tiers: set[str]) -> bool:
    return (not waves or task.wave_id in waves) and (not risk_tiers or task.risk_tier in risk_tiers)


def select_tasks(
    tasks: list[SourceListTask],
    *,
    waves: set[str],
    risk_tiers: set[str],
    limit: int | None,
    force: bool,
) -> list[SourceListTask]:
    existing = existing_items_by_url()
    selected = [
        task
        for task in tasks
        if task_matches_filters(task, waves, risk_tiers)
        and (force or task.normalized_url.lower() not in existing)
    ]
    return selected[:limit] if limit is not None else selected


def run_task(task: SourceListTask, timeout_seconds: int) -> dict[str, Any]:
    command = command_for(task)
    started = time.monotonic()
    exit_code, timed_out, stdout, stderr = run_command_capture(command, timeout_seconds)
    duration = round(time.monotonic() - started, 3)
    parsed = parse_skill_list_output(stdout)
    skills = parsed["listed_skills"]
    status = status_for(
        exit_code,
        timed_out,
        parsed["parsed_skill_count"],
        reported_skill_count=parsed["reported_skill_count"],
    )
    return {
        "rank": task.rank,
        "raw_indexes": task.raw_indexes,
        "wave_id": task.wave_id,
        "normalized_url": task.normalized_url,
        "source_name": task.source_name,
        "coverage_status": task.coverage_status,
        "intake_decision": task.intake_decision,
        "risk_tier": task.risk_tier,
        "auth_required": task.auth_required,
        "command": shlex.join(command),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "duration_seconds": duration,
        "reported_skill_count": parsed["reported_skill_count"],
        "found_skill_count": parsed["parsed_skill_count"],
        "representative_skills": skills[:10],
        "evidence_status": status,
        "stderr_excerpt": excerpt(stderr),
        "remaining_blockers": remaining_blockers(task, status),
    }


def remaining_blockers(task: SourceListTask, evidence_status: str) -> list[str]:
    blockers = [
        "license file review",
        "executable surface security review",
        "attribution review",
        "docs-steward promotion review",
        "target-specific validation",
    ]
    if task.coverage_status == "covered-by-existing-installable-catalog":
        blockers.insert(0, "do not duplicate existing installable catalog rows")
    if task.auth_required:
        blockers.insert(0, "auth and credential boundary review")
    if evidence_status != "source-list-found":
        blockers.insert(0, evidence_status)
    return blockers


def normalize_evidence_item(item: dict[str, Any], tasks_by_url: dict[str, SourceListTask]) -> dict[str, Any]:
    task = tasks_by_url.get(item["normalized_url"].lower())
    normalized = {key: item[key] for key in EVIDENCE_ITEM_KEYS if key in item}
    if task:
        normalized["rank"] = task.rank
        normalized["raw_indexes"] = task.raw_indexes
        normalized["wave_id"] = task.wave_id
        normalized["normalized_url"] = task.normalized_url
        normalized["source_name"] = task.source_name
        normalized["coverage_status"] = task.coverage_status
        normalized["intake_decision"] = task.intake_decision
        normalized["risk_tier"] = task.risk_tier
        normalized["auth_required"] = task.auth_required
        normalized["command"] = shlex.join(command_for(task))
    timed_out_raw = normalized.get("timed_out", False)
    normalized["timed_out"] = timed_out_raw if isinstance(timed_out_raw, bool) else False
    normalized.setdefault("duration_seconds", None)
    reported_skill_count_raw = normalized.get("reported_skill_count")
    normalized["reported_skill_count"] = (
        reported_skill_count_raw if isinstance(reported_skill_count_raw, int) else None
    )
    exit_code_raw = normalized.get("exit_code", 1)
    normalized["exit_code"] = exit_code_raw if isinstance(exit_code_raw, int) else 1
    found_skill_count_raw = normalized.get("found_skill_count", 0)
    normalized["found_skill_count"] = found_skill_count_raw if isinstance(found_skill_count_raw, int) else 0
    representative_skills = normalized.get("representative_skills") or item.get("listed_skills") or []
    if not isinstance(representative_skills, list):
        representative_skills = []
    normalized["representative_skills"] = [str(skill) for skill in representative_skills[:10]]
    if normalized.get("evidence_status") not in VALID_EVIDENCE_STATUSES:
        normalized["evidence_status"] = status_for(
            normalized["exit_code"],
            normalized["timed_out"],
            normalized["found_skill_count"],
            reported_skill_count=normalized["reported_skill_count"],
        )
    normalized.setdefault("stderr_excerpt", "")
    normalized.setdefault("remaining_blockers", remaining_blockers(task, normalized["evidence_status"]) if task else [])
    return normalized


def merge_items(
    existing_items: list[dict[str, Any]],
    new_items: list[dict[str, Any]],
    tasks_by_url: dict[str, SourceListTask],
) -> list[dict[str, Any]]:
    merged = {
        item["normalized_url"].lower(): normalize_evidence_item(item, tasks_by_url)
        for item in existing_items
    }
    for item in new_items:
        merged[item["normalized_url"].lower()] = normalize_evidence_item(item, tasks_by_url)
    return sorted(merged.values(), key=lambda item: (min(item["raw_indexes"]), item["normalized_url"].lower()))


def summarize_items(items: list[dict[str, Any]]) -> dict[str, Any]:
    by_status: dict[str, int] = {}
    by_wave: dict[str, int] = {}
    for item in items:
        by_status[item["evidence_status"]] = by_status.get(item["evidence_status"], 0) + 1
        by_wave[item["wave_id"]] = by_wave.get(item["wave_id"], 0) + 1
    return {
        "recorded_target_count": len(items),
        "remaining_target_count": max(EXPECTED_UNIQUE_COUNT - len(items), 0),
        "status_counts": dict(sorted(by_status.items())),
        "wave_counts": dict(sorted(by_wave.items())),
    }


def build_payload(items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "version": 2,
        "generated_at": now(),
        "status": "source-list-evidence-recorded",
        "scope": "read-only `npx --yes skills add <source> --list` probes for candidate corpus targets",
        "live_install_executed": False,
        "install_command_count": 0,
        "rule": "List-only probes are evidence gathering. They do not authorize live install or repo promotion.",
        "summary": summarize_items(items),
        "items": items,
    }


def validate_evidence(*, require_complete: bool) -> dict[str, Any]:
    errors: list[str] = []
    evidence = load_json(EVIDENCE_FILE)
    normalized = load_json("normalized-urls.json")
    unique_targets = {url.lower() for url in normalized["unique_targets"]}
    items = evidence.get("items", [])
    seen: set[str] = set()
    for item in items:
        url = item.get("normalized_url", "").lower()
        raw_keys = sorted(DISALLOWED_EVIDENCE_ITEM_KEYS.intersection(item))
        if raw_keys:
            errors.append(f"raw list-output fields present for {item.get('normalized_url')}: {', '.join(raw_keys)}")
        if url not in unique_targets:
            errors.append(f"unknown target in evidence: {item.get('normalized_url')}")
        if url in seen:
            errors.append(f"duplicate target in evidence: {item.get('normalized_url')}")
        seen.add(url)
        command = item.get("command", "")
        if " npx " in f" {command} " or command.startswith("npx "):
            pass
        else:
            errors.append(f"non-npx evidence command: {item.get('normalized_url')}")
        if "--list" not in command or "--skill" in command or "--apply" in command:
            errors.append(f"non-list-only evidence command: {item.get('normalized_url')}")
        if item.get("evidence_status") not in VALID_EVIDENCE_STATUSES:
            errors.append(f"invalid evidence status for {item.get('normalized_url')}: {item.get('evidence_status')}")
        if (
            item.get("evidence_status") == "source-list-found"
            and (item.get("exit_code") != 0 or item.get("found_skill_count", 0) <= 0)
        ):
            errors.append(f"inconsistent source-list-found item: {item.get('normalized_url')}")
    if evidence.get("live_install_executed") is not False or evidence.get("install_command_count") != 0:
        errors.append("source-list evidence unexpectedly records live install execution")
    if require_complete and len(items) != EXPECTED_UNIQUE_COUNT:
        errors.append(f"evidence item count {len(items)} != {EXPECTED_UNIQUE_COUNT}")
    return {
        "items": len(items),
        "unique_targets": len(unique_targets),
        "complete": len(items) == len(unique_targets),
        "summary": summarize_items(items),
        "ok": not errors,
        "errors": errors,
    }


def run_tasks(tasks: list[SourceListTask], *, concurrency: int, timeout_seconds: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        future_to_task = {executor.submit(run_task, task, timeout_seconds): task for task in tasks}
        total = len(future_to_task)
        for completed_count, future in enumerate(concurrent.futures.as_completed(future_to_task), 1):
            task = future_to_task[future]
            item = future.result()
            results.append(item)
            print(
                f"[{completed_count}/{total}] {item['evidence_status']} "
                f"{task.wave_id} {task.normalized_url}",
                file=sys.stderr,
                flush=True,
            )
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="run selected list-only probes and merge evidence")
    parser.add_argument("--plan-only", action="store_true", help="print selected probes without running them")
    parser.add_argument("--check", action="store_true", help="validate the current evidence file")
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="make --check fail unless all 289 targets have evidence",
    )
    parser.add_argument("--wave", action="append", default=[], help="limit to a promotion wave id, repeatable")
    parser.add_argument("--risk-tier", action="append", default=[], help="limit to a risk tier, repeatable")
    parser.add_argument("--limit", type=int, help="maximum selected probes")
    parser.add_argument("--force", action="store_true", help="rerun probes even when evidence already exists")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT_SECONDS, help="per-probe timeout in seconds")
    parser.add_argument("--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="parallel probe count")
    args = parser.parse_args()

    if args.check:
        result = validate_evidence(require_complete=args.require_complete)
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 1

    all_tasks = build_tasks()
    tasks = select_tasks(
        all_tasks,
        waves=set(args.wave),
        risk_tiers=set(args.risk_tier),
        limit=args.limit,
        force=args.force,
    )

    if args.plan_only:
        targets = [
            {
                "rank": task.rank,
                "raw_indexes": task.raw_indexes,
                "wave_id": task.wave_id,
                "normalized_url": task.normalized_url,
                "command": shlex.join(command_for(task)),
            }
            for task in tasks
        ]
        print(
            json.dumps(
                {
                    "selected_count": len(tasks),
                    "targets": targets,
                    "tasks": targets,
                },
                indent=2,
            )
        )
        return 0

    if args.write:
        if args.concurrency < 1:
            parser.error("--concurrency must be >= 1")
        if args.timeout < 1:
            parser.error("--timeout must be >= 1")
        existing = load_json(EVIDENCE_FILE) if (MANIFEST_DIR / EVIDENCE_FILE).exists() else {"items": []}
        new_items = run_tasks(tasks, concurrency=args.concurrency, timeout_seconds=args.timeout)
        tasks_by_url = {task.normalized_url.lower(): task for task in all_tasks}
        payload = build_payload(merge_items(existing.get("items", []), new_items, tasks_by_url))
        write_json(EVIDENCE_FILE, payload)
        print(json.dumps(payload["summary"], indent=2))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
