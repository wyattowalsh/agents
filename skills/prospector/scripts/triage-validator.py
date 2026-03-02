#!/usr/bin/env python3
"""Triage validator for prospector skill.

Validates LLM-assigned triage ratings and computes tier deterministically.
Does NOT assign ratings — those come from the LLM in Wave 2.

Input: JSON from stdin or --input with 6 dimension ratings + metadata.
Output: Validated triage with tier, hard rules applied, warnings.

Usage:
  echo '{"bootstrappability":"strong",...}' | python triage-validator.py --input -
  python triage-validator.py --input triage.json
"""
import argparse
import json
import sys

# --- Constants ---

_VALID_RATINGS = {"strong", "moderate", "weak"}

_REQUIRED_DIMENSIONS = [
    "bootstrappability",
    "pmf_signals",
    "competition",
    "revenue_potential",
    "technical_feasibility",
    "moat_potential",
]

_VALID_SIGNAL_TYPES = {
    "pain_no_solution",
    "dying_product",
    "platform_expansion",
    "rising_trend",
    "terrible_ux",
    "manual_workflow",
}


# --- Validation ---

def validate_dimensions(data: dict) -> tuple[dict[str, str], list[str]]:
    """Validate that all 6 dimensions are present with valid values.

    Returns (dimensions_dict, error_list).
    """
    dimensions: dict[str, str] = {}
    errors: list[str] = []

    for dim in _REQUIRED_DIMENSIONS:
        val = data.get(dim)
        if val is None:
            errors.append(f"missing dimension: {dim}")
        elif val not in _VALID_RATINGS:
            errors.append(f"invalid rating for {dim}: {val!r} (must be strong/moderate/weak)")
        else:
            dimensions[dim] = val

    return dimensions, errors


# --- Hard rules ---

def apply_hard_rules(
    dimensions: dict[str, str],
    data: dict,
) -> tuple[str, list[str], list[str]]:
    """Apply hard rules and compute tier.

    Returns (tier, hard_rules_applied, warnings).
    """
    hard_rules: list[str] = []
    warnings: list[str] = []

    # Count strong and weak
    strong_count = sum(1 for v in dimensions.values() if v == "strong")
    weak_count = sum(1 for v in dimensions.values() if v == "weak")

    # Compute base tier
    tier = _compute_tier(dimensions, strong_count, weak_count)

    # Hard rule 1: Single-signal cap
    signal_count = data.get("signal_count")
    if signal_count is not None:
        try:
            signal_count = int(signal_count)
        except (ValueError, TypeError):
            signal_count = None

    if signal_count is not None and signal_count <= 1:
        if tier == "strong":
            tier = "moderate"
            hard_rules.append("single-signal cap: tier capped at moderate")
        warnings.append("only 1 signal detected — consider gathering more evidence")

    # Hard rule 2: Freshness check
    stale = data.get("stale_signals", False)
    freshness_months = data.get("freshness_months")
    if freshness_months is not None:
        try:
            freshness_months = float(freshness_months)
        except (ValueError, TypeError):
            freshness_months = None

    if stale or (freshness_months is not None and freshness_months > 6):
        if tier in ("strong", "moderate"):
            tier = "weak"
            hard_rules.append("freshness cap: signals >6 months old, tier capped at weak")
        warnings.append("signals may be stale (>6 months old)")

    # Hard rule 3: Independence check
    independent_sources = data.get("independent_sources")
    if independent_sources is not None:
        try:
            independent_sources = int(independent_sources)
        except (ValueError, TypeError):
            independent_sources = None

    if independent_sources is not None and independent_sources < 2:
        warnings.append(
            f"only {independent_sources} independent source(s) — "
            "signals may be echo chamber"
        )

    # Hard rule 4: Strong incumbent found
    strong_incumbent = data.get("strong_incumbent", False)
    if strong_incumbent and dimensions.get("competition") != "weak":
        dimensions["competition"] = "weak"
        hard_rules.append("strong incumbent found: competition forced to weak")
        # Recompute tier after adjustment
        strong_count = sum(1 for v in dimensions.values() if v == "strong")
        weak_count = sum(1 for v in dimensions.values() if v == "weak")
        tier = _compute_tier(dimensions, strong_count, weak_count)

    # Additional warnings
    if dimensions.get("pmf_signals") == "weak":
        warnings.append("pmf_signals is weak — opportunity may lack product-market fit evidence")
    if dimensions.get("bootstrappability") == "weak":
        warnings.append("bootstrappability is weak — may not be suitable for solo/bootstrap founder")

    return tier, hard_rules, warnings


def _compute_tier(
    dimensions: dict[str, str],
    strong_count: int,
    weak_count: int,
) -> str:
    """Deterministic tier assignment from dimension ratings.

    Strong: 4+ strong, 0 weak.
           OR 3 strong including pmf_signals, 0-1 weak.
    Moderate: 2-3 strong, <=2 weak.
              No critical weakness in pmf + bootstrappability.
    Weak: <=1 strong, or pmf_signals weak, or bootstrappability weak.
    """
    pmf = dimensions.get("pmf_signals")
    bootstrap = dimensions.get("bootstrappability")

    # Weak conditions (checked first — they override)
    if pmf == "weak":
        return "weak"
    if bootstrap == "weak":
        return "weak"
    if strong_count <= 1:
        return "weak"

    # Strong conditions
    if strong_count >= 4 and weak_count == 0:
        return "strong"
    if strong_count >= 3 and pmf == "strong" and weak_count <= 1:
        return "strong"

    # Moderate conditions
    if 2 <= strong_count <= 3 and weak_count <= 2:
        return "moderate"

    # Fallback
    return "moderate"


# --- Panel eligibility ---

def check_panel_eligible(tier: str, signal_count: int | None) -> bool:
    """Strong tier opportunities with 2+ signals are panel-eligible."""
    if tier != "strong":
        return False
    return not (signal_count is not None and signal_count < 2)


# --- Main ---

def validate(data: dict) -> dict:
    dimensions, errors = validate_dimensions(data)
    if errors:
        return {
            "valid": False,
            "errors": errors,
            "dimensions": dimensions,
            "tier": None,
            "hard_rules_applied": [],
            "warnings": [],
            "panel_eligible": False,
        }

    tier, hard_rules, warnings = apply_hard_rules(dimensions, data)

    signal_count = data.get("signal_count")
    if signal_count is not None:
        try:
            signal_count = int(signal_count)
        except (ValueError, TypeError):
            signal_count = None

    panel_eligible = check_panel_eligible(tier, signal_count)

    return {
        "valid": True,
        "dimensions": dimensions,
        "tier": tier,
        "hard_rules_applied": hard_rules,
        "warnings": warnings,
        "panel_eligible": panel_eligible,
    }


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Validate LLM-assigned triage ratings and compute tier. "
        "Input: JSON with 6 dimension ratings (strong/moderate/weak). "
        "Output: validated triage + tier + warnings.",
    )
    ap.add_argument(
        "--input",
        dest="input_source",
        default="-",
        help="JSON file path or '-' for stdin (default: stdin).",
    )
    args = ap.parse_args()

    try:
        if args.input_source == "-":
            raw = sys.stdin.read()
        else:
            with open(args.input_source) as f:
                raw = f.read()
    except OSError as exc:
        print(f"Error: could not read input: {exc}", file=sys.stderr)
        sys.exit(1)

    if not raw.strip():
        print("Error: empty input.", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        print(f"Error: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)

    if not isinstance(data, dict):
        print("Error: input must be a JSON object.", file=sys.stderr)
        sys.exit(1)

    result = validate(data)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
