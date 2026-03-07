#!/usr/bin/env python3
"""Basic Kubernetes manifest validation.

Output JSON: {resources: [{kind, name, namespace}], issues: [{resource, rule, severity, message, fix}]}
"""

import argparse
import itertools
import json
import re
import sys
from pathlib import Path


def parse_yaml_documents(content: str) -> list[dict]:
    """Simple YAML parser for K8s manifests (stdlib only, no PyYAML dependency)."""
    documents = []
    current_doc = {}
    current_path = []
    indent_stack = [(-1, current_doc)]

    for raw_line in content.split("---"):
        doc_lines = raw_line.strip().splitlines()
        if not doc_lines:
            continue

        doc = {}
        for line in doc_lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            if ":" in stripped:
                key, _, value = stripped.partition(":")
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key == "kind":
                    doc["kind"] = value
                elif key == "name" and "metadata" not in doc or key == "name":
                    doc.setdefault("metadata", {})["name"] = value
                elif key == "namespace":
                    doc.setdefault("metadata", {})["namespace"] = value
                elif key == "image":
                    doc.setdefault("_images", []).append(value)
                elif key == "privileged":
                    doc["_privileged"] = value.lower() == "true"
                elif key == "runAsNonRoot":
                    doc["_runAsNonRoot"] = value.lower() == "true"
                elif key == "readOnlyRootFilesystem":
                    doc["_readOnlyRootFs"] = value.lower() == "true"
                elif key == "allowPrivilegeEscalation":
                    doc["_allowPrivEsc"] = value.lower() == "true"
                elif key == "hostNetwork":
                    doc["_hostNetwork"] = value.lower() == "true"
                elif key == "hostPID":
                    doc["_hostPID"] = value.lower() == "true"

        if doc.get("kind"):
            documents.append(doc)

    return documents


def check_resource_limits(content: str, resource_name: str) -> list[dict]:
    """Check if containers have resource limits."""
    issues = []
    has_limits = "limits:" in content and ("cpu:" in content or "memory:" in content)
    has_requests = "requests:" in content and ("cpu:" in content or "memory:" in content)

    if not has_limits:
        issues.append({
            "resource": resource_name,
            "rule": "K8S001",
            "severity": "high",
            "message": "Missing resource limits (cpu/memory)",
            "fix": "Add resources.limits with cpu and memory values",
        })

    if not has_requests:
        issues.append({
            "resource": resource_name,
            "rule": "K8S002",
            "severity": "medium",
            "message": "Missing resource requests (cpu/memory)",
            "fix": "Add resources.requests with cpu and memory values",
        })

    return issues


def check_health_checks(content: str, resource_name: str) -> list[dict]:
    """Check for health probes."""
    issues = []
    workload_kinds = {"Deployment", "StatefulSet", "DaemonSet"}

    # Only check workloads
    kind_match = re.search(r"kind:\s*(\w+)", content)
    if not kind_match or kind_match.group(1) not in workload_kinds:
        return issues

    if "livenessProbe:" not in content:
        issues.append({
            "resource": resource_name,
            "rule": "K8S003",
            "severity": "high",
            "message": "Missing livenessProbe",
            "fix": "Add livenessProbe with httpGet, tcpSocket, or exec check",
        })

    if "readinessProbe:" not in content:
        issues.append({
            "resource": resource_name,
            "rule": "K8S004",
            "severity": "high",
            "message": "Missing readinessProbe",
            "fix": "Add readinessProbe to prevent traffic to unready pods",
        })

    return issues


def check_security(doc: dict, content: str, resource_name: str) -> list[dict]:
    """Check security-related settings."""
    issues = []

    if doc.get("_privileged"):
        issues.append({
            "resource": resource_name,
            "rule": "K8S005",
            "severity": "critical",
            "message": "Container running in privileged mode",
            "fix": "Remove privileged: true unless absolutely necessary",
        })

    if doc.get("_hostNetwork"):
        issues.append({
            "resource": resource_name,
            "rule": "K8S006",
            "severity": "critical",
            "message": "Pod using host network",
            "fix": "Remove hostNetwork: true — use Services for networking",
        })

    if doc.get("_hostPID"):
        issues.append({
            "resource": resource_name,
            "rule": "K8S007",
            "severity": "critical",
            "message": "Pod sharing host PID namespace",
            "fix": "Remove hostPID: true",
        })

    if not doc.get("_runAsNonRoot") and "securityContext" in content:
        issues.append({
            "resource": resource_name,
            "rule": "K8S008",
            "severity": "medium",
            "message": "runAsNonRoot not set to true",
            "fix": "Add securityContext.runAsNonRoot: true",
        })

    if not doc.get("_readOnlyRootFs"):
        issues.append({
            "resource": resource_name,
            "rule": "K8S009",
            "severity": "medium",
            "message": "readOnlyRootFilesystem not enabled",
            "fix": "Add securityContext.readOnlyRootFilesystem: true",
        })

    if doc.get("_allowPrivEsc", True):
        issues.append({
            "resource": resource_name,
            "rule": "K8S010",
            "severity": "medium",
            "message": "allowPrivilegeEscalation not set to false",
            "fix": "Add securityContext.allowPrivilegeEscalation: false",
        })

    # Check for latest tags
    for image in doc.get("_images", []):
        if image.endswith(":latest") or ":" not in image:
            issues.append({
                "resource": resource_name,
                "rule": "K8S011",
                "severity": "high",
                "message": f"Image '{image}' uses 'latest' tag or no tag",
                "fix": "Pin to a specific image version tag",
            })

    return issues


def validate_file(path: Path) -> dict:
    """Validate a single K8s manifest file."""
    content = path.read_text()
    documents = parse_yaml_documents(content)
    # Split content into per-document text slices (same separator as parse_yaml_documents)
    doc_slices = [s for s in content.split("---") if s.strip()]
    resources = []
    issues = []

    for doc, doc_text in zip(documents, doc_slices):
        kind = doc.get("kind", "Unknown")
        name = doc.get("metadata", {}).get("name", "unnamed")
        namespace = doc.get("metadata", {}).get("namespace", "default")
        resource_name = f"{kind}/{name}"

        resources.append({
            "kind": kind,
            "name": name,
            "namespace": namespace,
            "file": path.name,
        })

        issues.extend(check_resource_limits(doc_text, resource_name))
        issues.extend(check_health_checks(doc_text, resource_name))
        issues.extend(check_security(doc, doc_text, resource_name))

    return {"resources": resources, "issues": issues}


def main():
    parser = argparse.ArgumentParser(description="Validate Kubernetes manifests")
    parser.add_argument("path", help="Path to K8s manifest file or directory")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(json.dumps({"error": f"Path not found: {args.path}"}))
        sys.exit(1)

    all_resources = []
    all_issues = []

    if path.is_dir():
        yaml_files = sorted(itertools.chain(path.glob("**/*.yaml"), path.glob("**/*.yml")))
        if not yaml_files:
            print(json.dumps({"error": f"No YAML files found in {args.path}"}))
            sys.exit(1)
        for f in yaml_files:
            result = validate_file(f)
            all_resources.extend(result["resources"])
            all_issues.extend(result["issues"])
    else:
        result = validate_file(path)
        all_resources = result["resources"]
        all_issues = result["issues"]

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_issues.sort(key=lambda x: severity_order.get(x["severity"], 4))

    output = {
        "path": str(path),
        "resources": all_resources,
        "issues": all_issues,
        "summary": {
            "total_resources": len(all_resources),
            "issues_by_severity": {
                "critical": sum(1 for i in all_issues if i["severity"] == "critical"),
                "high": sum(1 for i in all_issues if i["severity"] == "high"),
                "medium": sum(1 for i in all_issues if i["severity"] == "medium"),
                "low": sum(1 for i in all_issues if i["severity"] == "low"),
            },
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
