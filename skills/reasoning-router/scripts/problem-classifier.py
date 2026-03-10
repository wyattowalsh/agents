"""Deterministic problem classifier for the reasoning-router skill.

Pure keyword/pattern matching — no LLM calls, no API calls, no external dependencies.
Takes problem text as a CLI argument and outputs JSON classification.
"""

import json
import re
import sys

# ---------------------------------------------------------------------------
# Axis 1 — Structure (8 types)
# ---------------------------------------------------------------------------
STRUCTURE_SIGNALS: dict[str, list[str]] = {
    "decomposable": [
        "break down", "sub-questions", "parts", "components", "decompose",
        "separate", "individually", "each aspect", "multi-hop", "chain of",
        "depends on previous",
    ],
    "sequential": [
        "step by step", "first then", "process", "procedure", "workflow",
        "in order", "sequence", "one at a time", "walk through", "trace through",
    ],
    "branching": [
        "explore options", "what if", "alternatives", "compare", "versus",
        "trade-offs", "pros and cons", "different angles", "perspectives",
        "scenarios",
    ],
    "constrained": [
        "given that", "requirements", "constraints", "must satisfy",
        "specifications", "formal", "prove", "guarantee", "invariant",
        "bounded by",
    ],
    "interconnected": [
        "dependencies", "circular", "complex system", "feedback loop",
        "coupled", "emergent", "interrelated", "web of", "network of",
        "entangled",
    ],
    "creative": [
        "brainstorm", "novel", "innovative", "stuck", "reframe",
        "outside the box", "unconventional", "imagine",
        "what would happen if", "new approach",
    ],
    "contradictory": [
        "paradox", "both true", "tension", "dilemma", "seemingly opposite",
        "reconcile", "on one hand", "conflict between", "contradiction",
    ],
    "investigative": [
        "why did", "root cause", "what caused", "debug", "investigate",
        "diagnose", "troubleshoot", "figure out why", "trace back", "bisect",
    ],
}

# ---------------------------------------------------------------------------
# Axis 2 — Complexity (4 levels)
# ---------------------------------------------------------------------------
COMPLEXITY_KEYWORDS: dict[str, list[str]] = {
    "simple": ["quick", "simple", "basic", "trivial", "straightforward"],
    "moderate": [
        "several", "multiple", "a few", "some", "requirements",
        "constraints", "trade-off", "considerations", "factors",
        "tried", "approaches", "options", "scenarios",
    ],
    "complex": [
        "many", "numerous", "cross-domain", "cross domain", "interdisciplinary",
        "uncertain", "ambiguous", "multi-region", "compliance",
        "simultaneously", "concurrent", "interacting", "cascading",
        "guarantee", "consistency", "failover", "latency",
    ],
    "wicked": [
        "no clear solution", "contested", "values",
        "fundamental disagreement", "impossible to fully solve",
        "paradox", "irreconcilable", "both true",
    ],
}

# ---------------------------------------------------------------------------
# Axis 3 — Domain (9 domains)
# ---------------------------------------------------------------------------
DOMAIN_SIGNALS: dict[str, list[str]] = {
    "engineering": [
        "architecture", "system design", "scalability", "infrastructure",
        "deployment", "performance", "optimization", "service",
        "microservice", "api",
    ],
    "debugging": [
        "bug", "error", "exception", "crash", "failing", "broken",
        "regression", "unexpected behavior", "stack trace", "log",
    ],
    "research": [
        "literature", "state of the art", "survey", "compare approaches",
        "evidence", "study", "findings", "analysis",
    ],
    "math": [
        "prove", "theorem", "equation", "algorithm", "complexity",
        "formula", "mathematical", "compute", "calculate",
    ],
    "strategy": [
        "decision", "choose", "prioritize", "trade-off", "risk",
        "roadmap", "plan", "strategy", "evaluate options",
    ],
    "creative": [
        "design", "ux", "user experience", "visual", "aesthetic",
        "brand", "creative direction", "ideate",
    ],
    "philosophy": [
        "ethical", "moral", "meaning", "consciousness", "free will",
        "justice", "rights", "values", "existential",
    ],
    "planning": [
        "roadmap", "timeline", "milestones", "phases", "schedule",
        "project plan", "sprint", "backlog", "prioritize tasks",
    ],
    "patterns": [
        "recurring", "pattern", "across sessions", "remember",
        "track over time", "historical", "trend",
    ],
}

# ---------------------------------------------------------------------------
# Method mapping (structure → primary, fallback)
# ---------------------------------------------------------------------------
METHOD_MAP: dict[str, tuple[str, str]] = {
    "decomposable":   ("atom-of-thoughts",    "cascade-thinking"),
    "sequential":     ("sequential-thinking",  "crash"),
    "branching":      ("cascade-thinking",     "think-strategies"),
    "constrained":    ("shannon-thinking",     "sequential-thinking"),
    "interconnected": ("atom-of-thoughts",     "cascade-thinking"),
    "creative":       ("creative-thinking",    "deep-lucid-3d"),
    "contradictory":  ("lotus-wisdom",         "cascade-thinking"),
    "investigative":  ("crash",                "sequential-thinking"),
}

# Tier 1 (cheap) methods for simple-complexity efficiency override
TIER1_FOR_STRUCTURE: dict[str, str] = {
    "decomposable":   "aot-light",
    "sequential":     "sequential-thinking",
    "branching":      "sequential-thinking",
    "constrained":    "sequential-thinking",
    "interconnected": "aot-light",
    "creative":       "aot-light",
    "contradictory":  "sequential-thinking",
    "investigative":  "sequential-thinking",
}

DOMAIN_METHOD_MAP: dict[str, str] = {
    "engineering": "shannon-thinking",
    "debugging":   "crash",
    "research":    "cascade-thinking",
    "math":        "atom-of-thoughts",
    "strategy":    "think-strategies",
    "creative":    "creative-thinking",
    "philosophy":  "lotus-wisdom",
    "planning":    "sequential-thinking",
    "patterns":    "structured-thinking",
}

TOKEN_TIER: dict[str, int] = {
    "simple": 1,
    "moderate": 2,
    "complex": 3,
    "wicked": 4,
}

# Composition pattern for wicked complexity
WICKED_FALLBACK: dict[str, str] = {
    "decomposable":   "cascade-thinking",
    "sequential":     "cascade-thinking",
    "branching":      "deep-lucid-3d",
    "constrained":    "deep-lucid-3d",
    "interconnected": "deep-lucid-3d",
    "creative":       "lotus-wisdom",
    "contradictory":  "deep-lucid-3d",
    "investigative":  "cascade-thinking",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    """Lowercase and strip non-alphanumeric characters (keep spaces/hyphens)."""
    text = text.lower()
    text = re.sub(r"[^\w\s-]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _first_sentence(text: str) -> str:
    """Extract the first sentence, skipping abbreviation periods."""
    match = re.search(r"[?!\n]|\.(?:\s+[A-Z]|\s*$)", text)
    if match:
        return text[: match.start() + 1]
    return text


def _count_words(text: str) -> int:
    return len(text.split())


def _score_signals(
    normalized: str,
    first_sent: str,
    signals: dict[str, list[str]],
) -> dict[str, tuple[float, list[str]]]:
    """Score each category. Returns {category: (raw_score, matched_signals)}."""
    results: dict[str, tuple[float, list[str]]] = {}
    for category, phrases in signals.items():
        score = 0.0
        matched: list[str] = []
        for phrase in phrases:
            # Build a regex that matches the phrase as whole words
            pattern = r"\b" + re.escape(phrase) + r"\b"
            hits = len(re.findall(pattern, normalized))
            if hits > 0:
                matched.append(phrase)
                base = hits
                # Position weighting: 1.5x if signal appears in first sentence
                if re.search(pattern, first_sent):
                    base *= 1.5
                score += base
        results[category] = (score, matched)
    return results


def _pick_top(
    scored: dict[str, tuple[float, list[str]]],
) -> tuple[str, float, list[str]]:
    """Pick the highest-scored category. Ties broken by dict order (first wins)."""
    best_cat = ""
    best_score = -1.0
    best_signals: list[str] = []
    for cat, (score, signals) in scored.items():
        if score > best_score:
            best_cat = cat
            best_score = score
            best_signals = signals
    return best_cat, best_score, best_signals


def _normalize_confidence(
    scored: dict[str, tuple[float, list[str]]],
    winner: str,
) -> float:
    """Normalize winner's score to 0.0-1.0 relative to total scores."""
    total = sum(s for s, _ in scored.values())
    if total == 0:
        return 0.0
    raw = scored[winner][0] / total
    return round(min(raw, 1.0), 2)


def _classify_complexity(
    normalized: str,
    word_count: int,
    structure_signal_count: int = 0,
) -> tuple[str, float, list[str]]:
    """Classify complexity using word count + keyword signals + structural richness."""
    # Base level from word count (conservative thresholds)
    if word_count < 25:
        wc_level = "simple"
    elif word_count < 100:
        wc_level = "moderate"
    else:
        wc_level = "complex"

    levels = ["simple", "moderate", "complex", "wicked"]

    # Multiple structure signals indicate a richer problem — boost by 1 level
    if structure_signal_count >= 3 and wc_level == "simple":
        wc_level = "moderate"

    # Keyword signals can push the level up (never down)
    level_idx = levels.index(wc_level)
    matched_signals: list[str] = []

    for level in levels:
        for kw in COMPLEXITY_KEYWORDS[level]:
            pattern = r"\b" + re.escape(kw) + r"\b"
            if re.search(pattern, normalized):
                kw_idx = levels.index(level)
                matched_signals.append(kw)
                if kw_idx > level_idx:
                    level_idx = kw_idx

    final_level = levels[level_idx]

    # Confidence: higher when word count and keywords agree
    if matched_signals:
        # Keywords found — confidence is higher if they agree with word count
        agreement = 1.0 if final_level == wc_level else 0.7
        signal_bonus = min(len(matched_signals) / 5, 0.2)
        confidence = round(min(0.5 + 0.3 * agreement + signal_bonus, 1.0), 2)
    else:
        # No keywords — rely on word count alone, lower confidence
        confidence = 0.4

    return final_level, confidence, matched_signals


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------

def classify(problem_text: str) -> dict[str, object]:
    """Classify a problem along 3 axes and suggest a reasoning method."""
    normalized = _normalize(problem_text)
    first_sent = _normalize(_first_sentence(problem_text))
    word_count = _count_words(normalized)

    # Axis 1 — Structure
    structure_scored = _score_signals(normalized, first_sent, STRUCTURE_SIGNALS)
    struct_val, _, struct_signals = _pick_top(structure_scored)
    # Default if nothing matched
    if struct_signals:
        struct_conf = _normalize_confidence(structure_scored, struct_val)
    else:
        struct_val = "sequential"
        struct_conf = 0.1
        struct_signals = []

    # Axis 2 — Complexity (boosted by structure signal richness)
    total_struct_signals = sum(1 for _, sigs in structure_scored.values() if sigs)
    comp_val, comp_conf, comp_signals = _classify_complexity(
        normalized, word_count, total_struct_signals,
    )

    # Axis 3 — Domain
    domain_scored = _score_signals(normalized, first_sent, DOMAIN_SIGNALS)
    dom_val, _, dom_signals = _pick_top(domain_scored)
    if dom_signals:
        dom_conf = _normalize_confidence(domain_scored, dom_val)
    else:
        dom_val = "unknown"
        dom_conf = 0.1
        dom_signals = []

    # Method selection
    primary, fallback = METHOD_MAP[struct_val]
    if struct_conf < 0.3 and dom_conf > struct_conf and dom_val in DOMAIN_METHOD_MAP:
        primary = DOMAIN_METHOD_MAP[dom_val]
    token_tier = TOKEN_TIER[comp_val]

    # Efficiency gate
    efficiency_override = None
    if comp_val == "simple":
        tier1_method = TIER1_FOR_STRUCTURE[struct_val]
        efficiency_override = {
            "method": tier1_method,
            "reason": f"Simple complexity — downgraded to Tier 1 ({tier1_method}) to save tokens",
        }

    # Wicked composition hint
    if comp_val == "wicked":
        fallback = WICKED_FALLBACK.get(struct_val, "cascade-thinking")

    return {
        "structure": {
            "value": struct_val,
            "confidence": struct_conf,
            "signals": struct_signals,
        },
        "complexity": {
            "value": comp_val,
            "confidence": comp_conf,
            "signals": comp_signals,
        },
        "domain": {
            "value": dom_val,
            "confidence": dom_conf,
            "signals": dom_signals,
        },
        "suggested_method": primary,
        "suggested_fallback": fallback,
        "token_tier": token_tier,
        "efficiency_override": efficiency_override,
        "signals_found": struct_signals + comp_signals + dom_signals,
    }


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(
        description="Deterministic problem classifier for reasoning-router. "
        "Keyword/pattern matching — no LLM calls.",
    )
    ap.add_argument("problem_text", help="The problem text to classify.")
    args = ap.parse_args()

    if not args.problem_text.strip():
        print("Error: problem_text must not be empty.", file=sys.stderr)
        sys.exit(1)

    result = classify(args.problem_text)
    print(json.dumps(result, indent=2))
