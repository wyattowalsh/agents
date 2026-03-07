#!/usr/bin/env python3
"""Parse GitHub Actions YAML and analyze workflow structure.

Output: JSON with jobs, issues, and optimization opportunities.
Requires: pyyaml
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(json.dumps({"error": "pyyaml not installed. Run: uv add pyyaml"}), file=sys.stderr)
    sys.exit(1)


def analyze_job(name: str, job: dict) -> dict:
    """Analyze a single job for structure and issues."""
    steps = job.get("steps", [])
    uses_cache = any(
        s.get("uses", "").startswith("actions/cache") for s in steps
    )
    uses_matrix = "matrix" in job.get("strategy", {})
    has_timeout = "timeout-minutes" in job

    step_count = len(steps)
    # Weight: base 1 per step, +2 for build/compile steps, +1 for test steps
    weight = 0
    for s in steps:
        run_cmd = s.get("run", "")
        uses_action = s.get("uses", "")
        if any(kw in run_cmd.lower() for kw in ["build", "compile", "make", "cargo build", "go build"]):
            weight += 3
        elif any(kw in run_cmd.lower() for kw in ["test", "pytest", "jest", "vitest"]):
            weight += 2
        elif any(kw in uses_action.lower() for kw in ["docker", "build-push"]):
            weight += 3
        else:
            weight += 1

    return {
        "name": name,
        "steps_count": step_count,
        "uses_cache": uses_cache,
        "uses_matrix": uses_matrix,
        "has_timeout": has_timeout,
        "needs": job.get("needs", []),
        "runs_on": job.get("runs-on", "unknown"),
        "estimated_duration_weight": weight,
    }


def find_issues(workflow: dict, jobs_analysis: list[dict]) -> list[dict]:
    """Find common workflow issues."""
    issues = []

    # Check for missing permissions block
    if "permissions" not in workflow:
        issues.append({
            "severity": "critical",
            "category": "security",
            "message": "Missing top-level 'permissions' block. Workflow runs with default (broad) permissions.",
            "fix": "Add 'permissions: {}' at top level, then grant only what each job needs.",
        })

    # Check for missing concurrency
    if "concurrency" not in workflow:
        triggers = workflow.get("on", workflow.get(True, {}))
        if isinstance(triggers, dict) and ("push" in triggers or "pull_request" in triggers):
            issues.append({
                "severity": "warning",
                "category": "reliability",
                "message": "No concurrency group defined. Parallel runs of this workflow may conflict.",
                "fix": "Add 'concurrency: { group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true }'",
            })

    # Check each job for timeouts and unpinned actions in a single pass
    jobs = workflow.get("jobs", {})
    for job_info in jobs_analysis:
        job_name = job_info["name"]
        if not job_info["has_timeout"]:
            issues.append({
                "severity": "warning",
                "category": "cost",
                "message": f"Job '{job_name}' has no timeout-minutes. Runaway jobs consume quota.",
                "fix": f"Add 'timeout-minutes: <N>' to job '{job_name}'.",
            })

        # Check for unpinned actions in the same job
        job = jobs.get(job_name, {})
        for step in job.get("steps", []):
            uses = step.get("uses", "")
            if uses and "@" in uses:
                ref = uses.split("@")[1]
                # SHA pins are 40 hex chars
                if len(ref) < 40 and not ref.startswith("v"):
                    issues.append({
                        "severity": "warning",
                        "category": "security",
                        "message": f"Action '{uses}' in job '{job_name}' uses branch ref. Prefer SHA pin.",
                        "fix": f"Pin to full SHA: {uses.split('@')[0]}@<commit-sha>",
                    })
                elif ref.startswith("v") and len(ref) < 40:
                    issues.append({
                        "severity": "info",
                        "category": "security",
                        "message": f"Action '{uses}' in job '{job_name}' uses version tag. SHA pin is more secure.",
                        "fix": f"Pin to full SHA: {uses.split('@')[0]}@<commit-sha>",
                    })

    return issues


def find_optimizations(jobs_analysis: list[dict]) -> list[dict]:
    """Find optimization opportunities."""
    optimizations = []

    # Jobs without caching
    uncached = [j for j in jobs_analysis if not j["uses_cache"]]
    if uncached:
        names = [j["name"] for j in uncached]
        optimizations.append({
            "type": "caching",
            "impact": "high",
            "message": f"Jobs without caching: {', '.join(names)}. Adding dependency caching can reduce build time 30-60%.",
            "jobs": names,
        })

    # Jobs that could use matrix
    no_matrix = [j for j in jobs_analysis if not j["uses_matrix"] and j["steps_count"] > 3]
    if no_matrix:
        names = [j["name"] for j in no_matrix]
        optimizations.append({
            "type": "matrix",
            "impact": "medium",
            "message": f"Jobs without matrix strategy: {', '.join(names)}. Consider matrix for multi-version/multi-OS testing.",
            "jobs": names,
        })

    # Sequential jobs that could parallelize
    all_needs = {}
    for j in jobs_analysis:
        needs = j["needs"]
        if isinstance(needs, str):
            needs = [needs]
        all_needs[j["name"]] = needs

    # Find chains longer than 2
    for name, deps in all_needs.items():
        for dep in deps:
            if dep in all_needs and all_needs[dep]:
                optimizations.append({
                    "type": "parallelization",
                    "impact": "medium",
                    "message": f"Job '{name}' depends on '{dep}' which itself has dependencies. Review if the chain can be shortened.",
                    "jobs": [name, dep],
                })

    # Heavy jobs on default runners
    heavy = [j for j in jobs_analysis if j["estimated_duration_weight"] > 10 and "ubuntu-latest" in str(j["runs_on"])]
    if heavy:
        names = [j["name"] for j in heavy]
        optimizations.append({
            "type": "runner",
            "impact": "low",
            "message": f"Heavy jobs on default runners: {', '.join(names)}. Consider larger runners for compute-intensive work.",
            "jobs": names,
        })

    return optimizations


def main():
    parser = argparse.ArgumentParser(description="Analyze GitHub Actions workflow YAML")
    parser.add_argument("file", help="Path to workflow YAML file")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(json.dumps({"error": f"File not found: {args.file}"}))
        sys.exit(1)

    try:
        with open(path) as f:
            workflow = yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(json.dumps({"error": f"YAML parse error: {e}"}))
        sys.exit(1)

    if not isinstance(workflow, dict):
        print(json.dumps({"error": "Invalid workflow: root must be a mapping"}))
        sys.exit(1)

    jobs = workflow.get("jobs", {})
    if not jobs:
        print(json.dumps({"error": "No jobs found in workflow"}))
        sys.exit(1)

    jobs_analysis = [analyze_job(name, job) for name, job in jobs.items()]
    issues = find_issues(workflow, jobs_analysis)
    optimizations = find_optimizations(jobs_analysis)

    result = {
        "file": str(path),
        "name": workflow.get("name", path.stem),
        "triggers": list(workflow.get("on", workflow.get(True, {})).keys()) if isinstance(workflow.get("on", workflow.get(True, {})), dict) else [str(workflow.get("on", "unknown"))],
        "jobs": jobs_analysis,
        "issues": issues,
        "optimization_opportunities": optimizations,
        "summary": {
            "total_jobs": len(jobs_analysis),
            "total_steps": sum(j["steps_count"] for j in jobs_analysis),
            "jobs_with_cache": sum(1 for j in jobs_analysis if j["uses_cache"]),
            "jobs_with_matrix": sum(1 for j in jobs_analysis if j["uses_matrix"]),
            "jobs_without_timeout": sum(1 for j in jobs_analysis if not j["has_timeout"]),
            "critical_issues": sum(1 for i in issues if i["severity"] == "critical"),
            "warnings": sum(1 for i in issues if i["severity"] == "warning"),
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
