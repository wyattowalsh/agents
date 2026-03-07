#!/usr/bin/env python3
"""Estimate CI/CD minutes from workflow analysis.

Output: JSON with estimated minutes, parallelizable steps, and caching savings.
Stdlib only (reads workflow-analyzer.py output from stdin or file).
"""

import argparse
import json
import sys


# Base duration estimates per step type (minutes)
STEP_WEIGHTS = {
    "checkout": 0.5,
    "setup": 1.0,
    "cache_restore": 0.5,
    "install": 2.0,
    "build": 3.0,
    "test": 5.0,
    "lint": 1.0,
    "docker_build": 5.0,
    "deploy": 2.0,
    "upload_artifact": 0.5,
    "download_artifact": 0.5,
    "generic": 1.0,
}

# Runner cost multipliers (relative to ubuntu-latest)
RUNNER_MULTIPLIERS = {
    "ubuntu-latest": 1.0,
    "ubuntu-22.04": 1.0,
    "ubuntu-24.04": 1.0,
    "macos-latest": 10.0,
    "macos-14": 10.0,
    "macos-15": 10.0,
    "windows-latest": 2.0,
    "windows-2022": 2.0,
    "self-hosted": 0.0,  # No GitHub billing
}


def classify_step(step: dict) -> str:
    """Classify a step by type for cost estimation."""
    uses = step.get("uses", "").lower()
    run = step.get("run", "").lower()

    if "checkout" in uses:
        return "checkout"
    if "setup-" in uses or "setup_" in uses:
        return "setup"
    if "cache" in uses:
        return "cache_restore"
    if "docker" in uses or "build-push" in uses:
        return "docker_build"
    if "upload-artifact" in uses:
        return "upload_artifact"
    if "download-artifact" in uses:
        return "download_artifact"
    if any(kw in run for kw in ["npm install", "pip install", "yarn install", "pnpm install", "uv sync", "bundle install"]):
        return "install"
    if any(kw in run for kw in ["build", "compile", "make", "cargo build", "go build"]):
        return "build"
    if any(kw in run for kw in ["test", "pytest", "jest", "vitest", "cargo test", "go test"]):
        return "test"
    if any(kw in run for kw in ["lint", "eslint", "ruff", "clippy", "golangci"]):
        return "lint"
    if any(kw in run for kw in ["deploy", "kubectl", "terraform apply", "aws ", "gcloud"]):
        return "deploy"
    return "generic"


def estimate_job(job: dict) -> dict:
    """Estimate cost for a single job."""
    steps = job.get("steps", [])
    runner = str(job.get("runs-on", "ubuntu-latest"))

    # Find the best matching runner multiplier
    multiplier = 1.0
    for runner_key, mult in RUNNER_MULTIPLIERS.items():
        if runner_key in runner.lower():
            multiplier = mult
            break

    step_estimates = []
    total_minutes = 0.0
    parallelizable = []

    for step in steps:
        step_type = classify_step(step)
        base_minutes = STEP_WEIGHTS[step_type]
        adjusted = base_minutes * multiplier
        total_minutes += adjusted

        step_info = {
            "name": step.get("name", step.get("uses", step.get("run", "unnamed")[:50])),
            "type": step_type,
            "estimated_minutes": round(adjusted, 1),
        }
        step_estimates.append(step_info)

        # Steps that don't depend on previous output could run in parallel
        if step_type in ("lint", "test"):
            parallelizable.append(step_info["name"])

    # Matrix multiplier
    matrix = job.get("strategy", {}).get("matrix", {})
    matrix_combinations = 1
    for key, values in matrix.items():
        if isinstance(values, list):
            matrix_combinations *= len(values)

    return {
        "name": job.get("name", "unnamed"),
        "runner": runner,
        "runner_multiplier": multiplier,
        "steps": step_estimates,
        "estimated_minutes_per_run": round(total_minutes, 1),
        "matrix_combinations": matrix_combinations,
        "total_with_matrix": round(total_minutes * matrix_combinations, 1),
        "parallelizable_steps": parallelizable,
    }


def estimate_caching_savings(jobs: list[dict]) -> dict:
    """Estimate potential savings from caching."""
    total_install_time = 0.0
    total_build_time = 0.0
    jobs_without_cache = []

    for job in jobs:
        has_cache = any(s["type"] == "cache_restore" for s in job["steps"])
        if not has_cache:
            jobs_without_cache.append(job["name"])
            for s in job["steps"]:
                if s["type"] == "install":
                    total_install_time += s["estimated_minutes"]
                elif s["type"] == "build":
                    total_build_time += s["estimated_minutes"]

    # Cache typically saves 50-80% of install time, 30-50% of build time
    install_savings = total_install_time * 0.65
    build_savings = total_build_time * 0.40
    total_savings = install_savings + build_savings
    total_time = sum(j["estimated_minutes_per_run"] for j in jobs)

    return {
        "jobs_without_cache": jobs_without_cache,
        "potential_install_savings_minutes": round(install_savings, 1),
        "potential_build_savings_minutes": round(build_savings, 1),
        "total_potential_savings_minutes": round(total_savings, 1),
        "caching_savings_pct": round((total_savings / total_time * 100) if total_time > 0 else 0, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="Estimate CI/CD pipeline cost")
    parser.add_argument("file", nargs="?", help="Path to workflow YAML (requires pyyaml) or workflow-analyzer JSON output")
    parser.add_argument("--from-analysis", action="store_true", help="Input is workflow-analyzer.py JSON output")
    args = parser.parse_args()

    if args.file:
        with open(args.file) as f:
            data = f.read()
    else:
        data = sys.stdin.read()

    if args.from_analysis or not args.file:
        # Parse workflow-analyzer output
        try:
            analysis = json.loads(data)
        except json.JSONDecodeError as e:
            print(json.dumps({"error": f"Invalid JSON: {e}"}))
            sys.exit(1)

        # Reconstruct minimal job dicts from analysis
        jobs = analysis.get("jobs", [])
        print(json.dumps({
            "estimated_minutes_per_run": sum(j.get("estimated_duration_weight", 1) for j in jobs),
            "parallelizable_steps": sum(1 for j in jobs if not j.get("needs")),
            "total_jobs": len(jobs),
            "note": "Use --from-analysis with workflow-analyzer.py output for detailed estimates. Pass raw YAML for full analysis.",
        }, indent=2))
        return

    # Direct YAML analysis
    try:
        import yaml
    except ImportError:
        print(json.dumps({"error": "pyyaml required for direct YAML analysis. Use --from-analysis with workflow-analyzer output instead."}))
        sys.exit(1)

    try:
        workflow = yaml.safe_load(data)
    except yaml.YAMLError as e:
        print(json.dumps({"error": f"YAML parse error: {e}"}))
        sys.exit(1)

    jobs_raw = workflow.get("jobs", {})
    job_estimates = [estimate_job({"name": name, **job}) for name, job in jobs_raw.items()]
    caching = estimate_caching_savings(job_estimates)

    total_per_run = sum(j["total_with_matrix"] for j in job_estimates)
    # Find critical path (longest chain)
    critical_path_minutes = max(j["total_with_matrix"] for j in job_estimates) if job_estimates else 0

    result = {
        "estimated_minutes_per_run": round(total_per_run, 1),
        "critical_path_minutes": round(critical_path_minutes, 1),
        "parallelizable_steps": sum(len(j["parallelizable_steps"]) for j in job_estimates),
        "caching_savings_pct": caching["caching_savings_pct"],
        "jobs": job_estimates,
        "caching_analysis": caching,
        "monthly_estimate": {
            "runs_per_day_5": round(total_per_run * 5 * 30, 1),
            "runs_per_day_20": round(total_per_run * 20 * 30, 1),
            "runs_per_day_50": round(total_per_run * 50 * 30, 1),
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
