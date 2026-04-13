#!/usr/bin/env python3
"""Analyze Dockerfile for optimization opportunities.

Output JSON: {base_image, stages, layers: [{instruction, size_impact, cacheable}],
              issues: [{line, rule, severity, fix}]}
"""

import argparse
import json
import re
import sys
from pathlib import Path

RULES = {
    "DL3007": {
        "pattern": r"^FROM\s+\S+:latest",
        "severity": "high",
        "message": "Using 'latest' tag",
        "fix": "Pin to a specific version tag (e.g., node:20-alpine)",
    },
    "DL3002": {
        "pattern": None,  # Checked via logic: no USER directive
        "severity": "high",
        "message": "No USER directive — container runs as root",
        "fix": "Add USER directive with a non-root user",
    },
    "DL3009": {
        "pattern": r"apt-get\s+update(?!.*&&.*rm\s+-rf\s+/var/lib/apt/lists)",
        "severity": "medium",
        "message": "apt-get update without cleanup in same RUN",
        "fix": "Add '&& rm -rf /var/lib/apt/lists/*' in the same RUN layer",
    },
    "DL3013": {
        "pattern": r"pip\s+install(?!.*--no-cache-dir)",
        "severity": "low",
        "message": "pip install without --no-cache-dir",
        "fix": "Add --no-cache-dir to pip install",
    },
    "DL3015": {
        "pattern": r"apt-get\s+install(?!.*--no-install-recommends)",
        "severity": "low",
        "message": "apt-get install without --no-install-recommends",
        "fix": "Add --no-install-recommends to reduce image size",
    },
    "DL3020": {
        "pattern": r"^ADD\s+(?!https?://)",
        "severity": "medium",
        "message": "Using ADD instead of COPY for local files",
        "fix": "Use COPY for local files; ADD is only needed for URLs or tar extraction",
    },
    "DL3025": {
        "pattern": r'^CMD\s+["\']?(?:sh|bash)\s+-c',
        "severity": "low",
        "message": "Using shell form for CMD",
        "fix": "Use exec form: CMD [\"executable\", \"arg1\"]",
    },
    "SC1001": {
        "pattern": r"^COPY\s+\.\s+\.",
        "severity": "medium",
        "message": "COPY . . copies everything including unnecessary files",
        "fix": "COPY specific files/directories, use .dockerignore",
    },
    "DL3003": {
        "pattern": r"^RUN\s+cd\s+",
        "severity": "low",
        "message": "Using 'cd' in RUN instead of WORKDIR",
        "fix": "Use WORKDIR directive to change directories",
    },
    "LAYER001": {
        "pattern": None,  # Checked via logic: consecutive RUN instructions
        "severity": "medium",
        "message": "Consecutive RUN instructions — can be combined",
        "fix": "Combine consecutive RUN instructions with && to reduce layers",
    },
}

SIZE_IMPACT = {
    "FROM": "none",
    "RUN": "high",
    "COPY": "medium",
    "ADD": "medium",
    "ENV": "minimal",
    "ARG": "none",
    "EXPOSE": "none",
    "WORKDIR": "minimal",
    "USER": "none",
    "CMD": "none",
    "ENTRYPOINT": "none",
    "LABEL": "none",
    "VOLUME": "none",
    "HEALTHCHECK": "none",
    "SHELL": "none",
    "STOPSIGNAL": "none",
    "ONBUILD": "none",
}

CACHEABLE_INSTRUCTIONS = {"ENV", "ARG", "EXPOSE", "WORKDIR", "USER", "LABEL", "VOLUME"}


def parse_dockerfile(content: str) -> dict:
    lines = content.splitlines()
    stages = []
    layers = []
    current_stage = None
    base_image = None
    has_user = False
    issues = []
    consecutive_runs = []

    i = 0
    while i < len(lines):
        raw_line = lines[i]
        line_num = i + 1
        line = raw_line.strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        # Handle line continuations
        while line.endswith("\\") and i + 1 < len(lines):
            i += 1
            line = line[:-1] + " " + lines[i].strip()

        instruction = line.split()[0].upper() if line.split() else ""

        if instruction == "FROM":
            match = re.match(r"FROM\s+(\S+)(?:\s+AS\s+(\S+))?", line, re.IGNORECASE)
            if match:
                image = match.group(1)
                alias = match.group(2)
                if base_image is None:
                    base_image = image
                current_stage = alias or f"stage-{len(stages)}"
                stages.append({"name": current_stage, "base": image})

        if instruction == "USER":
            has_user = True

        # Track consecutive RUNs
        if instruction == "RUN":
            consecutive_runs.append(line_num)
        else:
            if len(consecutive_runs) > 1:
                issues.append({
                    "line": consecutive_runs[0],
                    "rule": "LAYER001",
                    "severity": "medium",
                    "message": RULES["LAYER001"]["message"],
                    "fix": RULES["LAYER001"]["fix"],
                })
            consecutive_runs = []

        # Check regex-based rules
        for rule_id, rule in RULES.items():
            if rule["pattern"] is None:
                continue
            if re.search(rule["pattern"], line, re.IGNORECASE):
                issues.append({
                    "line": line_num,
                    "rule": rule_id,
                    "severity": rule["severity"],
                    "message": rule["message"],
                    "fix": rule["fix"],
                })

        # Build layer info
        if instruction in SIZE_IMPACT:
            cacheable = instruction in CACHEABLE_INSTRUCTIONS
            # COPY/ADD of frequently changing files break cache
            if instruction in ("COPY", "ADD"):
                cacheable = "package" in line.lower() or "requirements" in line.lower() or "go.sum" in line.lower()

            layers.append({
                "instruction": instruction,
                "line": line_num,
                "content": line[:120],
                "size_impact": SIZE_IMPACT.get(instruction, "unknown"),
                "cacheable": cacheable,
                "stage": current_stage,
            })

        i += 1

    # Handle trailing consecutive RUNs
    if len(consecutive_runs) > 1:
        issues.append({
            "line": consecutive_runs[0],
            "rule": "LAYER001",
            "severity": "medium",
            "message": RULES["LAYER001"]["message"],
            "fix": RULES["LAYER001"]["fix"],
        })

    # Check for missing USER directive
    if not has_user:
        issues.append({
            "line": len(lines),
            "rule": "DL3002",
            "severity": "high",
            "message": RULES["DL3002"]["message"],
            "fix": RULES["DL3002"]["fix"],
        })

    # Check layer ordering: dependencies should come before source
    copy_indices = [l for l in layers if l["instruction"] == "COPY"]
    if len(copy_indices) >= 2:
        first_copy = copy_indices[0]
        if "." in first_copy["content"] and "package" not in first_copy["content"].lower():
            issues.append({
                "line": first_copy["line"],
                "rule": "ORDER001",
                "severity": "medium",
                "message": "Source files copied before dependency files — poor layer caching",
                "fix": "COPY dependency files (package.json, requirements.txt) first, install, then COPY source",
            })

    return {
        "base_image": base_image,
        "stages": stages,
        "is_multistage": len(stages) > 1,
        "layers": layers,
        "issues": sorted(issues, key=lambda x: {"high": 0, "medium": 1, "low": 2}.get(x["severity"], 3)),
        "summary": {
            "total_layers": len(layers),
            "stages": len(stages),
            "issues_by_severity": {
                "high": sum(1 for i in issues if i["severity"] == "high"),
                "medium": sum(1 for i in issues if i["severity"] == "medium"),
                "low": sum(1 for i in issues if i["severity"] == "low"),
            },
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Analyze Dockerfile for optimization")
    parser.add_argument("path", help="Path to Dockerfile")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(json.dumps({"error": f"File not found: {args.path}"}))
        sys.exit(1)

    content = path.read_text()
    result = parse_dockerfile(content)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
