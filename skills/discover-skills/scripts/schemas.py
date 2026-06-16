#!/usr/bin/env python3
"""Discovery JSON contracts and validation (stdlib only)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from _paths import data_dir

COVERAGE_VALUES = frozenset({"none", "low", "medium", "good", "full"})
SCOUT_ROLES = frozenset(
    {
        "repo-auditor",
        "registry-scout",
        "web-researcher",
        "mcp-scout",
        "harness-scout",
        "plugin-scout",
        "policy-scout",
        "ideator",
    }
)


@dataclass
class DomainGap:
    id: str
    name: str
    coverage: str
    priority: int
    existing_skills: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    scout_queries: list[str] = field(default_factory=list)
    classification: str = "low"

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GapReport:
    version: int
    generated_at: str
    repo_skill_count: int
    installed_skill_count: int
    domains: list[DomainGap]
    mcp: dict[str, Any] = field(default_factory=dict)
    plugins: dict[str, Any] = field(default_factory=dict)
    harness: dict[str, Any] = field(default_factory=dict)
    dedup_exclusions: list[str] = field(default_factory=list)

    def public_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "generated_at": self.generated_at,
            "repo_skill_count": self.repo_skill_count,
            "installed_skill_count": self.installed_skill_count,
            "domains": [d.public_dict() for d in self.domains],
            "mcp": self.mcp,
            "plugins": self.plugins,
            "harness": self.harness,
            "dedup_exclusions": self.dedup_exclusions,
        }


def load_agent_targets(path: Path | None = None) -> list[str]:
    target_path = path or data_dir() / "agent-targets.json"
    payload = json.loads(target_path.read_text(encoding="utf-8"))
    agents = payload.get("agents")
    if not isinstance(agents, list) or not agents:
        msg = f"Invalid agent targets: {target_path}"
        raise ValueError(msg)
    return [str(a) for a in agents]


def build_install_command(source: str, skill_name: str, *, agents: list[str] | None = None) -> str:
    targets = agents or load_agent_targets()
    agent_flags = " ".join(f"-a {agent}" for agent in targets)
    return f"npx skills add {source} --skill {skill_name} -y -g {agent_flags}"


def dedup_key(name: str, source: str) -> str:
    return f"{name.strip().lower()}@{source.strip().lower()}"


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def validate_gap_report(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("version", "generated_at", "domains"):
        if key not in data:
            errors.append(f"missing key: {key}")
    domains = data.get("domains")
    if not isinstance(domains, list):
        errors.append("domains must be a list")
        return errors
    for idx, domain in enumerate(domains):
        if not isinstance(domain, dict):
            errors.append(f"domains[{idx}] must be object")
            continue
        for req in ("id", "coverage", "priority"):
            if req not in domain:
                errors.append(f"domains[{idx}] missing {req}")
        cov = domain.get("coverage")
        if cov not in COVERAGE_VALUES:
            errors.append(f"domains[{idx}] invalid coverage: {cov}")
    return errors


def validate_wave_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("session_id", "wave", "expected_count", "tasks"):
        if key not in data:
            errors.append(f"missing key: {key}")
    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        errors.append("tasks must be a list")
        return errors
    if isinstance(data.get("expected_count"), int) and len(tasks) != data["expected_count"]:
        errors.append("expected_count must match len(tasks)")
    for idx, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"tasks[{idx}] must be object")
            continue
        for req in ("id", "role", "outputs"):
            if req not in task:
                errors.append(f"tasks[{idx}] missing {req}")
        role = task.get("role")
        if role not in SCOUT_ROLES:
            errors.append(f"tasks[{idx}] invalid role: {role}")
    return errors


def validate_scout_artifact(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ("task_id", "role", "status"):
        if key not in data:
            errors.append(f"missing key: {key}")
    if data.get("status") not in {"success", "skipped", "failed"}:
        errors.append("invalid status")
    if "candidates" in data and not isinstance(data["candidates"], list):
        errors.append("candidates must be a list")
    return errors


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")