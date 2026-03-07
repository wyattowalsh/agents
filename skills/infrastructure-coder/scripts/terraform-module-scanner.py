#!/usr/bin/env python3
"""Parse Terraform files for resource inventory.

Output JSON: {resources: [{type, name, provider}], variables: [...], outputs: [...]}
"""

import argparse
import bisect
import json
import re
import sys
from pathlib import Path


def _build_line_index(content: str) -> list[int]:
    """Build a list of newline positions for O(log n) line number lookups."""
    positions = [-1]
    for i, ch in enumerate(content):
        if ch == '\n':
            positions.append(i)
    return positions


def _get_line_num(positions: list[int], offset: int) -> int:
    """Return 1-based line number for a character offset using binary search."""
    return bisect.bisect_right(positions, offset)


def extract_blocks(content: str, block_types: list[str], line_index: list[int] | None = None) -> dict[str, list[dict]]:
    """Extract top-level blocks of given types using regex.

    Returns a dict mapping each block type to its list of extracted blocks.
    """
    if line_index is None:
        line_index = _build_line_index(content)

    results = {bt: [] for bt in block_types}

    for block_type in block_types:
        pattern = rf'^{block_type}\s+"([^"]+)"(?:\s+"([^"]+)")?\s*\{{'

        for match in re.finditer(pattern, content, re.MULTILINE):
            first = match.group(1)
            second = match.group(2)
            line = _get_line_num(line_index, match.start())

            if block_type == "resource":
                results[block_type].append({
                    "type": first,
                    "name": second or "",
                    "provider": first.split("_")[0] if "_" in first else first,
                    "line": line,
                })
            elif block_type == "data":
                results[block_type].append({
                    "type": first,
                    "name": second or "",
                    "provider": first.split("_")[0] if "_" in first else first,
                    "line": line,
                })
            elif block_type == "variable":
                # Extract type and default from block body
                block_end = find_block_end(content, match.end() - 1)
                block_body = content[match.end():block_end] if block_end else ""

                var_type = "string"
                type_match = re.search(r'type\s*=\s*(\S+)', block_body)
                if type_match:
                    var_type = type_match.group(1)

                has_default = "default" in block_body
                has_validation = "validation" in block_body

                desc_match = re.search(r'description\s*=\s*"([^"]*)"', block_body)
                description = desc_match.group(1) if desc_match else ""

                results[block_type].append({
                    "name": first,
                    "type": var_type,
                    "has_default": has_default,
                    "has_validation": has_validation,
                    "description": description,
                    "line": line,
                })
            elif block_type == "output":
                results[block_type].append({
                    "name": first,
                    "line": line,
                })
            elif block_type == "module":
                # Extract source
                block_end = find_block_end(content, match.end() - 1)
                block_body = content[match.end():block_end] if block_end else ""

                source_match = re.search(r'source\s*=\s*"([^"]*)"', block_body)
                source = source_match.group(1) if source_match else ""

                results[block_type].append({
                    "name": first,
                    "source": source,
                    "line": line,
                })

    return results


def find_block_end(content: str, start: int) -> int | None:
    """Find matching closing brace."""
    depth = 0
    for i in range(start, len(content)):
        if content[i] == "{":
            depth += 1
        elif content[i] == "}":
            depth -= 1
            if depth == 0:
                return i
    return None


def extract_providers(content: str) -> list[dict]:
    """Extract required_providers block."""
    providers = []
    match = re.search(r'required_providers\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}', content)
    if match:
        block = match.group(1)
        for provider_match in re.finditer(
            r'(\w+)\s*=\s*\{[^}]*source\s*=\s*"([^"]*)"[^}]*version\s*=\s*"([^"]*)"',
            block, re.DOTALL
        ):
            providers.append({
                "name": provider_match.group(1),
                "source": provider_match.group(2),
                "version": provider_match.group(3),
            })
    return providers


def scan_directory(path: Path) -> dict:
    """Scan a directory for all .tf files."""
    tf_files = sorted(path.glob("**/*.tf"))
    if not tf_files:
        return {"error": f"No .tf files found in {path}"}

    all_resources = []
    all_data_sources = []
    all_variables = []
    all_outputs = []
    all_modules = []
    all_providers = []
    files_scanned = []

    for tf_file in tf_files:
        content = tf_file.read_text()
        rel_path = str(tf_file.relative_to(path))
        files_scanned.append(rel_path)

        line_index = _build_line_index(content)
        blocks = extract_blocks(content, ["resource", "data", "variable", "output", "module"], line_index)

        for r in blocks["resource"]:
            r["file"] = rel_path
            all_resources.append(r)

        for d in blocks["data"]:
            d["file"] = rel_path
            all_data_sources.append(d)

        for v in blocks["variable"]:
            v["file"] = rel_path
            all_variables.append(v)

        for o in blocks["output"]:
            o["file"] = rel_path
            all_outputs.append(o)

        for m in blocks["module"]:
            m["file"] = rel_path
            all_modules.append(m)

        providers = extract_providers(content)
        for p in providers:
            p["file"] = rel_path
            all_providers.append(p)

    # Analyze provider usage
    provider_set = set()
    for r in all_resources:
        provider_set.add(r["provider"])
    for d in all_data_sources:
        provider_set.add(d["provider"])

    return {
        "path": str(path),
        "files_scanned": files_scanned,
        "resources": all_resources,
        "data_sources": all_data_sources,
        "variables": all_variables,
        "outputs": all_outputs,
        "modules": all_modules,
        "providers": all_providers,
        "summary": {
            "files": len(files_scanned),
            "resources": len(all_resources),
            "data_sources": len(all_data_sources),
            "variables": len(all_variables),
            "outputs": len(all_outputs),
            "modules": len(all_modules),
            "providers_used": sorted(provider_set),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Scan Terraform files for resource inventory")
    parser.add_argument("path", help="Path to Terraform file or directory")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        print(json.dumps({"error": f"Path not found: {args.path}"}))
        sys.exit(1)

    if path.is_dir():
        result = scan_directory(path)
    else:
        content = path.read_text()
        line_index = _build_line_index(content)
        blocks = extract_blocks(content, ["resource", "data", "variable", "output", "module"], line_index)
        result = {
            "path": str(path),
            "files_scanned": [path.name],
            "resources": blocks["resource"],
            "data_sources": blocks["data"],
            "variables": blocks["variable"],
            "outputs": blocks["output"],
            "modules": blocks["module"],
            "providers": extract_providers(content),
        }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
