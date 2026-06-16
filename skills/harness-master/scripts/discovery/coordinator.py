#!/usr/bin/env python3
"""Plan and verify scout wave manifests from GapReport."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from schemas import load_json, validate_scout_artifact, validate_wave_manifest, write_json

MAX_REGISTRY_SCOUTS = 20
MAX_WEB_SCOUTS = 6
MAX_WAVE2_TASKS = 24
DEFAULT_TIMEOUTS = {
    "registry-scout": 45,
    "web-researcher": 90,
    "mcp-scout": 30,
    "harness-scout": 30,
    "plugin-scout": 30,
    "hook-scout": 30,
    "policy-scout": 60,
    "repo-auditor": 120,
    "ideator": 180,
}


def _scout_task(
    *,
    task_id: str,
    role: str,
    partition_primary: str,
    artifacts_root: Path,
    wave_dir: str,
    inputs: dict[str, Any],
    timeout_sec: int,
) -> dict[str, Any]:
    return {
        "id": task_id,
        "role": role,
        "partition_primary": partition_primary,
        "inputs": inputs,
        "outputs": {
            "artifact": str(artifacts_root / wave_dir / f"{task_id}.json"),
            "schema": "scout-artifact",
        },
        "timeout_sec": timeout_sec,
        "retries": 1,
        "readonly": True,
    }


def plan_wave(
    *,
    gap_report: dict[str, Any],
    session_id: str,
    wave: int,
    artifacts_root: Path,
) -> dict[str, Any]:
    tasks: list[dict[str, Any]] = []

    if wave == 1:
        domains = gap_report.get("domains", [])
        for idx, domain in enumerate(domains[:12]):
            if not isinstance(domain, dict):
                continue
            task_id = f"W1-RA-{idx:02d}"
            tasks.append(
                _scout_task(
                    task_id=task_id,
                    role="repo-auditor",
                    partition_primary=f"domain:{domain.get('id', idx)}",
                    artifacts_root=artifacts_root,
                    wave_dir="wave1",
                    inputs={
                        "gap_report": str(artifacts_root / "wave0" / "gap-report.json"),
                        "domain_id": domain.get("id"),
                    },
                    timeout_sec=DEFAULT_TIMEOUTS["repo-auditor"],
                )
            )

    if wave == 2:
        # Fixed asset scouts (mcp/plugin/hook/harness/policy) appended first so they survive MAX trim
        gap_input = {"gap_report": str(artifacts_root / "wave0" / "gap-report.json")}
        for role, suffix in (
            ("mcp-scout", "MS-00"),
            ("plugin-scout", "PS-00"),
            ("hook-scout", "HK-00"),
            ("policy-scout", "POL-00"),
        ):
            tasks.append(
                _scout_task(
                    task_id=f"W2-{suffix}",
                    role=role,
                    partition_primary=role,
                    artifacts_root=artifacts_root,
                    wave_dir="wave2",
                    inputs=gap_input,
                    timeout_sec=DEFAULT_TIMEOUTS[role],
                )
            )

        tasks.append(
            _scout_task(
                task_id="W2-HS-00",
                role="harness-scout",
                partition_primary="harness:all",
                artifacts_root=artifacts_root,
                wave_dir="wave2",
                inputs={},
                timeout_sec=DEFAULT_TIMEOUTS["harness-scout"],
            )
        )

        queries: list[str] = []
        for domain in gap_report.get("domains", []):
            if not isinstance(domain, dict):
                continue
            if domain.get("classification") in {"high", "medium"}:
                for q in domain.get("scout_queries", []):
                    if q and q not in queries:
                        queries.append(str(q))
        queries = queries[:MAX_REGISTRY_SCOUTS]

        for idx, query in enumerate(queries):
            task_id = f"W2-RS-{idx:02d}"
            tasks.append(
                _scout_task(
                    task_id=task_id,
                    role="registry-scout",
                    partition_primary=f"query:{query}",
                    artifacts_root=artifacts_root,
                    wave_dir="wave2",
                    inputs={"query": query},
                    timeout_sec=DEFAULT_TIMEOUTS["registry-scout"],
                )
            )

        high_domains = [
            d for d in gap_report.get("domains", []) if isinstance(d, dict) and d.get("classification") == "high"
        ][:MAX_WEB_SCOUTS]
        for idx, domain in enumerate(high_domains):
            task_id = f"W2-WR-{idx:02d}"
            tasks.append(
                _scout_task(
                    task_id=task_id,
                    role="web-researcher",
                    partition_primary=f"web:{domain.get('id', idx)}",
                    artifacts_root=artifacts_root,
                    wave_dir="wave2",
                    inputs={"domain_id": domain.get("id"), "domain_name": domain.get("name")},
                    timeout_sec=DEFAULT_TIMEOUTS["web-researcher"],
                )
            )

        if len(tasks) > MAX_WAVE2_TASKS:
            tasks = tasks[:MAX_WAVE2_TASKS]

    manifest = {
        "session_id": session_id,
        "wave": wave,
        "expected_count": len(tasks),
        "resolved_count": 0,
        "max_wall_sec": 600,
        "tasks": tasks,
    }
    errors = validate_wave_manifest(manifest)
    if errors:
        manifest["validation_errors"] = errors
    return manifest


def _resolve_artifact_path(
    *,
    task_id: str,
    outputs: dict[str, Any] | None,
    artifacts_dir: Path | None,
) -> Path:
    if isinstance(outputs, dict) and outputs.get("artifact"):
        path = Path(str(outputs["artifact"]))
        if path.is_file():
            return path
    if artifacts_dir is not None and task_id:
        fallback = artifacts_dir / f"{task_id}.json"
        if fallback.is_file():
            return fallback
    if isinstance(outputs, dict) and outputs.get("artifact"):
        return Path(str(outputs["artifact"]))
    return Path()


def verify_manifest(
    *,
    manifest: dict[str, Any],
    artifacts_dir: Path | None = None,
) -> dict[str, Any]:
    tasks = manifest.get("tasks", [])
    resolved = 0
    missing: list[str] = []
    invalid: list[str] = []

    for task in tasks:
        if not isinstance(task, dict):
            continue
        task_id = str(task.get("id", ""))
        outputs = task.get("outputs", {})
        artifact_path = _resolve_artifact_path(
            task_id=task_id,
            outputs=outputs if isinstance(outputs, dict) else None,
            artifacts_dir=artifacts_dir,
        )
        if not artifact_path.is_file():
            missing.append(task_id)
            continue
        try:
            data = json.loads(artifact_path.read_text(encoding="utf-8"))
            errs = validate_scout_artifact(data)
            if errs:
                invalid.append(f"{task_id}:{'|'.join(errs)}")
                continue
            if data.get("status") in {"success", "skipped"}:
                resolved += 1
            else:
                missing.append(task_id)
        except json.JSONDecodeError:
            invalid.append(f"{task_id}:invalid-json")

    expected = int(manifest.get("expected_count", len(tasks)))
    ok = resolved == expected and not invalid
    return {
        "ok": ok,
        "expected_count": expected,
        "resolved_count": resolved,
        "missing": missing,
        "invalid": invalid,
    }


def write_checkpoint(artifacts_root: Path, payload: dict[str, Any]) -> None:
    write_json(artifacts_root / "checkpoint.json", payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discovery coordinator")
    sub = parser.add_subparsers(dest="command", required=True)

    plan_p = sub.add_parser("plan")
    plan_p.add_argument("--gap", type=Path, required=True)
    plan_p.add_argument("--session-id", required=True)
    plan_p.add_argument("--wave", type=int, required=True)
    plan_p.add_argument("--artifacts-root", type=Path, required=True)
    plan_p.add_argument("-o", "--output", type=Path, required=True)

    verify_p = sub.add_parser("verify")
    verify_p.add_argument("--manifest", type=Path, required=True)
    verify_p.add_argument("--artifacts", type=Path, required=True)

    args = parser.parse_args(argv)

    if args.command == "plan":
        gap = load_json(args.gap)
        manifest = plan_wave(
            gap_report=gap,
            session_id=args.session_id,
            wave=args.wave,
            artifacts_root=args.artifacts_root,
        )
        write_json(args.output, manifest)
        write_checkpoint(
            args.artifacts_root,
            {
                "session_id": args.session_id,
                "session_version": 2,
                "artifact_root": str(args.artifacts_root),
                "wave": args.wave,
                "manifest": str(args.output),
            },
        )
        return 0 if "validation_errors" not in manifest else 1

    if args.command == "verify":
        manifest = load_json(args.manifest)
        result = verify_manifest(manifest=manifest, artifacts_dir=args.artifacts)
        print(json.dumps(result, indent=2))
        manifest["resolved_count"] = result["resolved_count"]
        write_json(args.manifest, manifest)
        return 0 if result["ok"] else 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())