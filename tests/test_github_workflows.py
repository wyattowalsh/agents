"""Regression guards for hardened GitHub Actions workflow structure."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = ROOT / ".github" / "workflows"
WORKFLOW_FILES = (
    "ci.yml",
    "dependency-review.yml",
    "frontier-radar-deterministic.yml",
    "ideas-quality-gates.yml",
    "install-smoke-phase3.yml",
    "maintenance-freshness.yml",
    "release-skills.yml",
    "reusable-validate.yml",
)
SETUP_UV_ACTION = ROOT / ".github" / "actions" / "setup-uv" / "action.yml"
SHA_PIN_RE = re.compile(r"^[0-9a-f]{40}$")
CHECKOUT_REF = "de0fac2e4500dabe0009e67214ff5f5447ce83dd"
SETUP_UV_REF = "08807647e7069bb48b6ef5acd8ec9567f424441b"


def _load_workflow(name: str) -> dict:
    data = yaml.safe_load((WORKFLOWS_DIR / name).read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{name} root must be a mapping"
    return data


def _action_ref(uses: str) -> str:
    return uses.split("@", 1)[1].split("#", 1)[0].strip()


def _is_checkout_step(step: dict) -> bool:
    uses = step.get("uses", "")
    return isinstance(uses, str) and uses.startswith("actions/checkout@")


def _is_local_action_step(step: dict) -> bool:
    uses = step.get("uses", "")
    return isinstance(uses, str) and uses.startswith("./")


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


def test_local_actions_run_after_checkout() -> None:
    for name in WORKFLOW_FILES:
        jobs = _load_workflow(name).get("jobs", {})
        for job_name, job in jobs.items():
            seen_checkout = False
            for step in job.get("steps", []):
                if _is_checkout_step(step):
                    seen_checkout = True
                if _is_local_action_step(step):
                    uses = step.get("uses")
                    assert seen_checkout, f"{name} job '{job_name}' uses local action '{uses}' before checkout"


def test_checkout_actions_use_canonical_ref() -> None:
    for name in WORKFLOW_FILES:
        jobs = _load_workflow(name).get("jobs", {})
        for job_name, job in jobs.items():
            for step in job.get("steps", []):
                if not _is_checkout_step(step):
                    continue
                uses = step.get("uses", "")
                ref = _action_ref(uses)
                assert ref == CHECKOUT_REF, f"{name} job '{job_name}' uses non-canonical checkout ref '{ref}'"


def test_setup_uv_action_uses_canonical_ref() -> None:
    action = yaml.safe_load(SETUP_UV_ACTION.read_text(encoding="utf-8"))
    assert isinstance(action, dict), "setup-uv action root must be a mapping"
    steps = action.get("runs", {}).get("steps", [])
    setup_steps = [step for step in steps if str(step.get("uses", "")).startswith("astral-sh/setup-uv@")]
    assert len(setup_steps) == 1, "setup-uv composite must contain exactly one astral-sh/setup-uv step"
    ref = _action_ref(setup_steps[0]["uses"])
    assert SHA_PIN_RE.match(ref), f"setup-uv composite uses unpinned action ref '{ref}'"
    assert ref == SETUP_UV_REF, f"setup-uv composite uses non-canonical ref '{ref}'"
