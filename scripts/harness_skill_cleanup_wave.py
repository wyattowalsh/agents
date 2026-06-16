#!/usr/bin/env python3
"""Orchestrate harness-skill cleanup waves 2-4 from wave0 artifacts."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

REPO = Path(__file__).resolve().parents[1]
TARGET_HARNESSES = ("claude-code", "codex", "grok", "opencode")

KNOWN_DEDUP_SLUGS = {
    "shadcn": ["shadcn/ui", "shadcn-ui/ui"],
    "find-skills": ["vercel-labs/skills", "discover-skills"],
}

DEDUP_PRECEDENCE = (
    "repo-owned",
    "verified-curated-external",
    "installed-external",
    "curated-unresolved",
    "read-only-discovered",
)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _provenance_rank(status: str) -> int:
    try:
        return DEDUP_PRECEDENCE.index(status)
    except ValueError:
        return len(DEDUP_PRECEDENCE)


def classify_row(row: dict, *, repo_skill_names: set[str], desired_by_name: dict[str, dict]) -> str:
    name = row["name"]
    status = row.get("provenance_status", "")
    agents = set(row.get("installed_agents") or [])
    desired = desired_by_name.get(name)

    if name in repo_skill_names and status != "repo-owned":
        return "dedupe_source"

    if desired:
        target_agents = desired.get("target_agents") or TARGET_HARNESSES
        if any(h not in agents for h in TARGET_HARNESSES if h in target_agents):
            missing = [h for h in TARGET_HARNESSES if h in target_agents and h not in agents]
            if missing:
                return "parity_install"

    if status == "installed-external" and row.get("install_command"):
        return "review_external"

    return "keep"


def build_parity_gaps(inventory_rows: list[dict], desired_rows: list[dict]) -> dict[str, list[dict]]:
    by_name = {r["name"]: r for r in inventory_rows}
    gaps: dict[str, list[dict]] = {h: [] for h in TARGET_HARNESSES}
    for desired in desired_rows:
        if desired.get("provenance_status") not in {"repo-owned", "verified-curated-external"}:
            continue
        name = desired["name"]
        installed = by_name.get(name, {})
        installed_agents = set(installed.get("installed_agents") or [])
        targets = set(desired.get("target_agents") or TARGET_HARNESSES)
        for harness in TARGET_HARNESSES:
            if harness in targets and harness not in installed_agents:
                gaps[harness].append(
                    {
                        "name": name,
                        "provenance_status": desired.get("provenance_status"),
                        "install_command": desired.get("install_command", ""),
                    }
                )
    return gaps


def build_dedup_candidates(inventory_rows: list[dict], external_policy: list[dict]) -> list[dict]:
    by_name: dict[str, list[dict]] = defaultdict(list)
    for row in inventory_rows:
        by_name[row["name"]].append(row)

    candidates: list[dict] = []
    for name, rows in sorted(by_name.items()):
        if len(rows) < 2:
            continue
        sources = sorted({r.get("source") or r.get("install_source") or r.get("path") for r in rows})
        canonical = sorted(rows, key=lambda r: _provenance_rank(str(r.get("provenance_status", ""))))[0]
        candidates.append(
            {
                "name": name,
                "count": len(rows),
                "sources": sources,
                "canonical_provenance": canonical.get("provenance_status"),
                "canonical_path": canonical.get("path"),
                "action": "dedupe_source",
            }
        )

    for slug, _sources in KNOWN_DEDUP_SLUGS.items():
        matching = [e for e in external_policy if e.get("name") == slug or slug in (e.get("source") or "")]
        if len(matching) > 1:
            candidates.append(
                {
                    "name": slug,
                    "count": len(matching),
                    "sources": [m.get("source") for m in matching],
                    "canonical_provenance": "verified-curated-external",
                    "note": "policy collision — pick one source in external-skills.md",
                    "action": "dedupe_source",
                }
            )
    return candidates


def merge_ledger(
    inventory_rows: list[dict],
    desired_rows: list[dict],
    symlink_audit: dict,
    multiroot: dict,
) -> list[dict]:
    repo_skill_names = {
        r["name"] for r in desired_rows if r.get("provenance_status") == "repo-owned"
    } | {
        r["name"] for r in inventory_rows if r.get("provenance_status") == "repo-owned"
    }
    desired_by_name = {r["name"]: r for r in desired_rows}

    mismatch_names = {e["name"] for e in symlink_audit.get("mismatch", [])}
    broken_names = {e["name"] for e in symlink_audit.get("broken", [])}
    multiroot_names = set((multiroot.get("collisions") or {}).keys())

    ledger = []
    for row in sorted(inventory_rows, key=lambda r: r["name"].lower()):
        action = classify_row(row, repo_skill_names=repo_skill_names, desired_by_name=desired_by_name)
        name = row["name"]
        notes: list[str] = []

        if name in broken_names:
            action = "refresh_mirror"
            notes.append("broken grok symlink")
        elif name in mismatch_names:
            action = "refresh_mirror"
            notes.append("grok symlink target mismatch")
        if name in multiroot_names:
            notes.append("opencode multi-root collision")

        ledger.append(
            {
                "name": name,
                "action": action,
                "provenance_status": row.get("provenance_status"),
                "installed_agents": row.get("installed_agents"),
                "target_agents": row.get("target_agents"),
                "path": row.get("path"),
                "install_command": row.get("install_command", ""),
                "notes": notes,
            }
        )
    return ledger


def emit_sync_dryruns(session: Path) -> None:
    import io
    from contextlib import redirect_stdout

    sys.path.insert(0, str(REPO))
    from wagents.cli import _build_sync_report, _emit_sync_report

    for harness in TARGET_HARNESSES:
        report = _build_sync_report((harness,), include_installed=False)
        buf = io.StringIO()
        with redirect_stdout(buf):
            _emit_sync_report(report, dry_run=True)
        (session / "wave0" / f"sync-dryrun-{harness}.txt").write_text(buf.getvalue(), encoding="utf-8")


def write_batch_packets(session: Path, ledger: list[dict], parity_gaps: dict[str, list[dict]]) -> None:
    wave4 = session / "wave4"
    wave4.mkdir(parents=True, exist_ok=True)

    dedupe = [r for r in ledger if r["action"] == "dedupe_source"]
    mirror = [r for r in ledger if r["action"] == "refresh_mirror"]

    if dedupe:
        lines = [
            "## Batch 1 — Claude/source dedupe",
            f"**Rows:** {len(dedupe)} | **Risk:** medium",
            "",
            "### Commands",
        ]
        for r in dedupe[:40]:
            if r.get("path") and "skills/" in r["path"] and not r["path"].startswith(str(REPO / "skills")):
                lines.append(f"# {r['name']}: review duplicate at {r['path']}")
        if len(dedupe) > 40:
            lines.append(f"# ... and {len(dedupe) - 40} more — see ledger.json")
        lines.extend(["", "### Rollback", "Use install_command per row in ledger.json"])
        (wave4 / "batch-1-dedup.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    for harness in TARGET_HARNESSES:
        gaps = parity_gaps.get(harness, [])
        if not gaps:
            continue
        lines = [
            f"## Batch 2 — {harness} parity install",
            f"**Rows:** {len(gaps)} | **Risk:** low (additive)",
            "",
            "### Commands",
            f"uv run wagents skills sync --apply -a {harness}",
            "",
            "### Missing skills (top 30)",
        ]
        for g in gaps[:30]:
            lines.append(f"- {g['name']} [{g['provenance_status']}]")
        (wave4 / f"batch-2-{harness}-parity.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    if mirror:
        lines = [
            "## Batch 3 — Grok mirror refresh",
            f"**Rows:** {len(mirror)} | **Risk:** low",
            "",
            "### Commands",
        ]
        for r in mirror:
            lines.append(f"rm ~/.grok/skills/{r['name']}  # then re-mirror")
        lines.append(
            'uv run python -c "from wagents.installed_inventory import '
            'mirror_grok_skills_from_claude; print(mirror_grok_skills_from_claude())"'
        )
        (wave4 / "batch-3-grok-mirror.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_kpi(session: Path, parity_gaps: dict, dedup_candidates: list, symlink_audit: dict, multiroot: dict) -> str:
    missing_total = sum(len(v) for v in parity_gaps.values())
    lines = [
        "# KPI Report",
        f"Generated: {datetime.now(UTC).isoformat()}",
        "",
        "| Metric | Value | Target |",
        "|--------|-------|--------|",
        f"| Parity gaps (curated+repo missing) | {missing_total} | 0 |",
        f"| Dedup candidate groups | {len(dedup_candidates)} | review |",
        f"| Broken Grok symlinks | {symlink_audit.get('broken_count', 0)} | 0 |",
        f"| Grok symlink mismatches | {symlink_audit.get('mismatch_count', 0)} | 0 |",
        f"| OpenCode multi-root collisions | {multiroot.get('collision_count', 0)} | document |",
        "",
        "## Per-harness parity gaps",
    ]
    for h in TARGET_HARNESSES:
        lines.append(f"- **{h}**: {len(parity_gaps.get(h, []))}")
    return "\n".join(lines) + "\n"


def run_apply_parity(session: Path, parity_gaps: dict[str, list[dict]]) -> list[dict]:
    log: list[dict] = []
    for harness in TARGET_HARNESSES:
        if not parity_gaps.get(harness):
            continue
        cmd = ["uv", "run", "wagents", "skills", "sync", "--apply", "-a", harness]
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True, check=False)
        entry = {
            "ts": datetime.now(UTC).isoformat(),
            "harness": harness,
            "cmd": " ".join(cmd),
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-2000:],
            "stderr_tail": proc.stderr[-1000:],
        }
        log.append(entry)
    log_path = session / "wave6" / "execution-log.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for entry in log:
            f.write(json.dumps(entry) + "\n")
    return log


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", default="harness-skill-cleanup-20260615")
    parser.add_argument("--apply-parity", action="store_true")
    args = parser.parse_args()

    session = REPO / "artifacts" / args.session
    wave0 = session / "wave0"
    wave2 = session / "wave2" / "merged"
    wave2.mkdir(parents=True, exist_ok=True)

    inventory_payload = _load_json(wave0 / "inventory-full.json")
    if isinstance(inventory_payload, dict):
        inventory_rows = cast(list[dict], inventory_payload["rows"])
    else:
        inventory_rows = cast(list[dict], inventory_payload)
    desired_rows = cast(list[dict], _load_json(wave0 / "desired-rows.json"))
    external_policy = cast(list[dict], _load_json(wave0 / "external-policy.json"))
    symlink_audit = cast(dict, _load_json(wave0 / "symlink-audit-grok.json"))
    multiroot = cast(dict, _load_json(wave0 / "multiroot-opencode.json"))

    emit_sync_dryruns(session)

    parity_gaps = build_parity_gaps(inventory_rows, desired_rows)
    dedup_candidates = build_dedup_candidates(inventory_rows, external_policy)
    ledger = merge_ledger(inventory_rows, desired_rows, symlink_audit, multiroot)

    (wave2 / "parity-gaps.json").write_text(json.dumps(parity_gaps, indent=2), encoding="utf-8")
    (wave2 / "dedup-candidates.json").write_text(json.dumps(dedup_candidates, indent=2), encoding="utf-8")
    (wave2 / "ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")

    action_counts: dict[str, int] = defaultdict(int)
    for row in ledger:
        action_counts[row["action"]] += 1
    summary = {"action_counts": dict(action_counts), "ledger_rows": len(ledger)}
    (wave2 / "ledger-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    write_batch_packets(session, ledger, parity_gaps)
    kpi = write_kpi(session, parity_gaps, dedup_candidates, symlink_audit, multiroot)
    (session / "wave7" / "kpi-report.md").write_text(kpi, encoding="utf-8")

    if args.apply_parity:
        run_apply_parity(session, parity_gaps)

    print(json.dumps(summary, indent=2))
    print(f"parity_gaps={{{', '.join(f'{k}: {len(v)}' for k, v in parity_gaps.items())}}}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())