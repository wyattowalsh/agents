#!/usr/bin/env python3
"""Deterministic scoring engine for name candidates.

Reads candidate data with intrinsic scores and availability info,
applies context-preset weights, computes composite scores, and
outputs ranked JSON to stdout.

Usage:
    uv run python skills/namer/scripts/score.py score --input candidates.json
    uv run python skills/namer/scripts/score.py rank --input candidates.json
    echo '{"candidates": [...]}' | uv run python skills/namer/scripts/score.py score
    uv run python skills/namer/scripts/score.py matrix --input availability.json
"""

from __future__ import annotations

import json
import sys
from enum import StrEnum
from typing import Annotated

import typer
from loguru import logger
from rich.console import Console
from rich.table import Table

# ---------------------------------------------------------------------------
# Loguru: warnings/errors to stderr only
# ---------------------------------------------------------------------------
logger.remove()
logger.add(sys.stderr, level="WARNING", format="{level}: {message}")

app = typer.Typer(help="Deterministic scoring engine for naming candidates.")
console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTRINSIC_DIMENSIONS = [
    "phonetic_quality",
    "semantic_fit",
    "memorability",
    "morphological_flexibility",
    "visual_quality",
]

EXTRINSIC_DIMENSIONS = [
    "domain_availability",
    "registry_availability",
    "handle_consistency",
    "search_distinctiveness",
    "typeability",
]

# Platform keys grouped by extrinsic dimension
DOMAIN_PLATFORMS = ["domain_com", "domain_dev", "domain_net"]
REGISTRY_PLATFORMS = ["github", "npm", "pypi", "crates"]
HANDLE_PLATFORMS = ["reddit", "bluesky"]
ALL_PLATFORMS = DOMAIN_PLATFORMS + REGISTRY_PLATFORMS + HANDLE_PLATFORMS

# Search result thresholds aligned with scoring-rubric.md
SEARCH_RESULTS_THRESHOLDS = [
    (10_000, 10),
    (100_000, 8),
    (1_000_000, 6),
    (10_000_000, 4),
]


class Preset(StrEnum):
    cli_tool = "cli-tool"
    oss_library = "oss-library"
    product = "product"
    brand = "brand"
    creative = "creative"
    side_project = "side-project"


# Intrinsic dimension weights per preset (from scoring-rubric.md)
INTRINSIC_WEIGHTS: dict[str, dict[str, float]] = {
    "cli-tool": {
        "phonetic_quality": 0.10,
        "semantic_fit": 0.15,
        "memorability": 0.25,
        "morphological_flexibility": 0.10,
        "visual_quality": 0.40,
    },
    "oss-library": {
        "phonetic_quality": 0.15,
        "semantic_fit": 0.25,
        "memorability": 0.20,
        "morphological_flexibility": 0.15,
        "visual_quality": 0.25,
    },
    "product": {
        "phonetic_quality": 0.25,
        "semantic_fit": 0.30,
        "memorability": 0.25,
        "morphological_flexibility": 0.15,
        "visual_quality": 0.05,
    },
    "brand": {
        "phonetic_quality": 0.30,
        "semantic_fit": 0.30,
        "memorability": 0.20,
        "morphological_flexibility": 0.15,
        "visual_quality": 0.05,
    },
    "creative": {
        "phonetic_quality": 0.35,
        "semantic_fit": 0.15,
        "memorability": 0.35,
        "morphological_flexibility": 0.05,
        "visual_quality": 0.10,
    },
    "side-project": {
        "phonetic_quality": 0.10,
        "semantic_fit": 0.15,
        "memorability": 0.20,
        "morphological_flexibility": 0.05,
        "visual_quality": 0.50,
    },
}

# Extrinsic dimension weights per preset (from scoring-rubric.md)
EXTRINSIC_WEIGHTS: dict[str, dict[str, float]] = {
    "cli-tool": {
        "domain_availability": 0.10,
        "registry_availability": 0.35,
        "handle_consistency": 0.05,
        "search_distinctiveness": 0.20,
        "typeability": 0.30,
    },
    "oss-library": {
        "domain_availability": 0.15,
        "registry_availability": 0.35,
        "handle_consistency": 0.10,
        "search_distinctiveness": 0.25,
        "typeability": 0.15,
    },
    "product": {
        "domain_availability": 0.35,
        "registry_availability": 0.05,
        "handle_consistency": 0.20,
        "search_distinctiveness": 0.25,
        "typeability": 0.15,
    },
    "brand": {
        "domain_availability": 0.35,
        "registry_availability": 0.00,
        "handle_consistency": 0.30,
        "search_distinctiveness": 0.25,
        "typeability": 0.10,
    },
    "creative": {
        "domain_availability": 0.25,
        "registry_availability": 0.00,
        "handle_consistency": 0.35,
        "search_distinctiveness": 0.30,
        "typeability": 0.10,
    },
    "side-project": {
        "domain_availability": 0.15,
        "registry_availability": 0.20,
        "handle_consistency": 0.05,
        "search_distinctiveness": 0.20,
        "typeability": 0.40,
    },
}

# Intrinsic/extrinsic split per preset (from scoring-rubric.md)
PRESET_SPLITS: dict[str, tuple[float, float]] = {
    "cli-tool": (0.30, 0.70),
    "oss-library": (0.35, 0.65),
    "product": (0.45, 0.55),
    "brand": (0.50, 0.50),
    "creative": (0.55, 0.45),
    "side-project": (0.25, 0.75),
}


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------


def _read_input(input_file: str | None) -> dict:
    """Read JSON from --input file or stdin."""
    if input_file:
        try:
            with open(input_file) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            raise typer.Exit(code=1) from None
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON in {input_file}: {exc}")
            raise typer.Exit(code=1) from None
    else:
        if sys.stdin.isatty():
            logger.error("No --input file and stdin is a terminal. Pipe JSON or use --input.")
            raise typer.Exit(code=1)
        try:
            return json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON on stdin: {exc}")
            raise typer.Exit(code=1) from None


def _intrinsic_avg(candidate: dict) -> float:
    """Compute average intrinsic score (0-10)."""
    intrinsic = candidate.get("intrinsic", {})
    present = {dim: intrinsic[dim] for dim in INTRINSIC_DIMENSIONS if dim in intrinsic}
    if len(present) < 3:
        logger.warning(
            f"Candidate '{candidate.get('name', '?')}' has only {len(present)}/5 "
            "intrinsic dimensions — score may be unreliable"
        )
    values = [intrinsic.get(dim, 0) for dim in INTRINSIC_DIMENSIONS]
    return sum(values) / len(values) if values else 0.0


def _weighted_intrinsic(candidate: dict, weights: dict[str, float]) -> float:
    """Compute weighted intrinsic score using preset dimension weights (0-10)."""
    intrinsic = candidate.get("intrinsic", {})
    total_weight = sum(weights.get(dim, 0) for dim in INTRINSIC_DIMENSIONS)
    if total_weight == 0:
        return _intrinsic_avg(candidate)
    weighted = sum(intrinsic.get(dim, 0) * weights.get(dim, 0) for dim in INTRINSIC_DIMENSIONS)
    return weighted / total_weight


# ---------------------------------------------------------------------------
# Extrinsic sub-dimension scorers
# ---------------------------------------------------------------------------


def _domain_score(availability: dict) -> float:
    """Score domain availability (0-10). .com=10, .dev=7, .net=5."""
    if availability.get("domain_com") is True:
        return 10.0
    if availability.get("domain_dev") is True:
        return 7.0
    if availability.get("domain_net") is True:
        return 5.0
    taken = sum(1 for k in DOMAIN_PLATFORMS if availability.get(k) is False)
    if taken == len(DOMAIN_PLATFORMS):
        return 0.0
    return 2.0  # some unknown, none confirmed available


def _registry_score(availability: dict) -> float:
    """Score registry availability (0-10)."""
    available = sum(1 for p in REGISTRY_PLATFORMS if availability.get(p) is True)
    total = len(REGISTRY_PLATFORMS)
    return (available / total) * 10 if total else 0.0


def _handle_score(availability: dict) -> float:
    """Score handle/social availability (0-10)."""
    available = sum(1 for p in HANDLE_PLATFORMS if availability.get(p) is True)
    total = len(HANDLE_PLATFORMS)
    return (available / total) * 10 if total else 0.0


def _search_distinctiveness(availability: dict) -> float:
    """Score search distinctiveness from search_results count (0-10). Lower results = higher score."""
    results = availability.get("search_results", 100_000)
    if not isinstance(results, int | float):
        return 5.0
    for threshold, score in SEARCH_RESULTS_THRESHOLDS:
        if results <= threshold:
            return float(score)
    return 2.0


def _typeability_score(name: str) -> float:
    """Score typeability based on length and character composition (0-10)."""
    n = len(name)
    if n <= 4:
        return 10.0
    if n <= 6:
        return 9.0
    if n <= 8:
        return 7.0
    if n <= 10:
        return 5.0
    return 3.0


def _compute_extrinsic(candidate: dict) -> dict[str, float]:
    """Compute all 5 extrinsic dimension scores from raw availability data."""
    availability = candidate.get("availability", {})
    name = candidate.get("name", "")
    return {
        "domain_availability": _domain_score(availability),
        "registry_availability": _registry_score(availability),
        "handle_consistency": _handle_score(availability),
        "search_distinctiveness": _search_distinctiveness(availability),
        "typeability": _typeability_score(name),
    }


def _weighted_extrinsic(extrinsic_scores: dict[str, float], weights: dict[str, float]) -> float:
    """Compute weighted extrinsic score (0-10)."""
    total_weight = sum(weights.get(dim, 0) for dim in EXTRINSIC_DIMENSIONS)
    if total_weight == 0:
        return sum(extrinsic_scores.values()) / len(extrinsic_scores) if extrinsic_scores else 0.0
    return sum(extrinsic_scores.get(dim, 0) * weights.get(dim, 0) for dim in EXTRINSIC_DIMENSIONS) / total_weight


def _composite_score(
    intrinsic: float,
    extrinsic: float,
    intrinsic_split: float,
    extrinsic_split: float,
) -> float:
    """Compute composite score normalized to 0-100."""
    raw = (intrinsic_split * intrinsic) + (extrinsic_split * extrinsic)
    return round(raw * 10, 1)  # scale 0-10 to 0-100


def _availability_summary(availability: dict) -> str:
    """Summarize availability as 'N/M platforms'."""
    available_count = sum(1 for p in ALL_PLATFORMS if availability.get(p) is True)
    return f"{available_count}/{len(ALL_PLATFORMS)} platforms"


def _data_quality(candidate: dict) -> str:
    """Assess data quality of a candidate's scoring inputs."""
    intrinsic = candidate.get("intrinsic", {})
    availability = candidate.get("availability", {})
    intrinsic_present = sum(1 for dim in INTRINSIC_DIMENSIONS if dim in intrinsic)
    avail_present = sum(1 for p in ALL_PLATFORMS if p in availability)
    if intrinsic_present >= 4 and avail_present >= 6:
        return "complete"
    if intrinsic_present >= 3 or avail_present >= 3:
        return "partial"
    return "incomplete"


def _score_candidates(data: dict) -> dict:
    """Score and rank all candidates, return output dict."""
    candidates = data.get("candidates", [])
    preset_name = data.get("preset", "product")

    if preset_name not in INTRINSIC_WEIGHTS:
        logger.warning(f"Unknown preset '{preset_name}', falling back to 'product'")
        preset_name = "product"

    i_weights = INTRINSIC_WEIGHTS[preset_name]
    e_weights = EXTRINSIC_WEIGHTS[preset_name]
    i_split, e_split = PRESET_SPLITS[preset_name]

    scored = []
    for candidate in candidates:
        name = candidate.get("name", "unnamed")
        archetype = candidate.get("archetype", "unknown")
        availability = candidate.get("availability", {})

        intrinsic_val = _weighted_intrinsic(candidate, i_weights)
        extrinsic_scores = _compute_extrinsic(candidate)
        extrinsic_val = _weighted_extrinsic(extrinsic_scores, e_weights)
        composite = _composite_score(intrinsic_val, extrinsic_val, i_split, e_split)

        dimensions = {}
        for dim in INTRINSIC_DIMENSIONS:
            dimensions[dim] = candidate.get("intrinsic", {}).get(dim, 0)
        for dim, val in extrinsic_scores.items():
            dimensions[dim] = round(val, 1)

        scored.append({
            "name": name,
            "archetype": archetype,
            "intrinsic_score": round(intrinsic_val * 10, 1),
            "extrinsic_score": round(extrinsic_val * 10, 1),
            "composite_score": composite,
            "dimensions": dimensions,
            "availability_summary": _availability_summary(availability),
            "data_quality": _data_quality(candidate),
        })

    scored.sort(key=lambda c: c["composite_score"], reverse=True)
    for i, entry in enumerate(scored, 1):
        entry["rank"] = i

    return {
        "ranked": scored,
        "preset": preset_name,
        "weights": {
            "intrinsic_split": i_split,
            "extrinsic_split": e_split,
            "intrinsic_weights": i_weights,
            "extrinsic_weights": e_weights,
        },
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def score(
    input_file: Annotated[
        str | None,
        typer.Option("--input", "-i", help="Path to input JSON file. Reads stdin if omitted."),
    ] = None,
) -> None:
    """Score candidates and output sorted JSON to stdout."""
    data = _read_input(input_file)
    result = _score_candidates(data)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


@app.command()
def rank(
    input_file: Annotated[
        str | None,
        typer.Option("--input", "-i", help="Path to input JSON file. Reads stdin if omitted."),
    ] = None,
) -> None:
    """Score candidates, print a Rich table to stderr, and output JSON to stdout."""
    data = _read_input(input_file)
    result = _score_candidates(data)

    # Rich table to stderr
    table = Table(title=f"Name Rankings — preset: {result['preset']}")
    table.add_column("#", justify="right", style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("Archetype", style="dim")
    table.add_column("Intrinsic", justify="right")
    table.add_column("Extrinsic", justify="right")
    table.add_column("Composite", justify="right", style="bold green")
    table.add_column("Availability", justify="center")

    for entry in result["ranked"]:
        table.add_row(
            str(entry["rank"]),
            entry["name"],
            entry["archetype"],
            f"{entry['intrinsic_score']:.0f}",
            f"{entry['extrinsic_score']:.0f}",
            f"{entry['composite_score']:.0f}",
            entry["availability_summary"],
        )

    console.print(table)

    # JSON to stdout
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


@app.command()
def matrix(
    input_file: Annotated[
        str | None,
        typer.Option("--input", "-i", help="Path to input JSON file. Reads stdin if omitted."),
    ] = None,
) -> None:
    """Generate an availability matrix table (stderr) and JSON (stdout)."""
    data = _read_input(input_file)
    candidates = data.get("candidates", [])

    # Build matrix data
    matrix_data: list[dict] = []
    for candidate in candidates:
        name = candidate.get("name", "unnamed")
        availability = candidate.get("availability", {})
        row: dict = {"name": name}
        for platform in ALL_PLATFORMS:
            val = availability.get(platform)
            if val is True:
                row[platform] = "available"
            elif val is False:
                row[platform] = "taken"
            else:
                row[platform] = "unknown"
        row["search_results"] = availability.get("search_results", "N/A")
        matrix_data.append(row)

    # Rich table to stderr
    platform_labels = {
        "domain_com": ".com",
        "domain_dev": ".dev",
        "domain_net": ".net",
        "github": "GitHub",
        "npm": "npm",
        "pypi": "PyPI",
        "crates": "Crates",
        "reddit": "Reddit",
        "bluesky": "Bsky",
    }
    table = Table(title="Availability Matrix")
    table.add_column("Name", style="cyan")
    for platform in ALL_PLATFORMS:
        table.add_column(platform_labels.get(platform, platform), justify="center")
    table.add_column("Search", justify="right")

    status_style = {"available": "[green]Y[/green]", "taken": "[red]N[/red]", "unknown": "[yellow]?[/yellow]"}

    for row in matrix_data:
        cells = [row["name"]]
        for platform in ALL_PLATFORMS:
            cells.append(status_style.get(row[platform], "?"))
        cells.append(str(row.get("search_results", "N/A")))
        table.add_row(*cells)

    console.print(table)

    # JSON to stdout
    output = {"matrix": matrix_data, "platforms": list(platform_labels.values())}
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    app()
