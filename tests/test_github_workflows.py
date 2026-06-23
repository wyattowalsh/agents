"""Regression guards for hardened GitHub Actions workflow structure."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
WORKFLOW_FILES = ("ci.yml", "release-skills.yml")
SHA_PIN_RE = re.compile(r"^[0-9a-f]{40}$")


def _load_workflow(name: str) -> dict:
    data = yaml.safe_load((WORKFLOWS_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{name} root must be a mapping"
    return data


def _action_ref(uses: str) -> str:
    return uses.split("@", 1)[1].split("#", 1)[0].strip()


def test_workflows_declare_top_level_permissions() -> None:
    for name in WORKFLOW_FILES:
        workflow = _load_workflow(name)
        assert "permissions" in workflow, f"{name} missing top-level permissions block"


def test_workflow_jobs_have_timeouts() -> None:
    for name in WORKFLOW_FILES:
        jobs = _load_workflow(name).get("jobs", {})
        for job_name, job in jobs.items():
            assert "timeout-minutes" in job, f"{name} job '{job_name}' missing timeout-minutes"


def test_third_party_actions_are_sha_pinned() -> None:
    for name in WORKFLOW_FILES:
        jobs = _load_workflow(name).get("jobs", {})
        for job_name, job in jobs.items():
            for step in job.get("steps", []):
                uses = step.get("uses", "")
                if not uses or uses.startswith("./"):
                    continue
                ref = _action_ref(uses)
                assert SHA_PIN_RE.match(ref), f"{name} job '{job_name}' uses unpinned action ref '{ref}' in '{uses}'"
