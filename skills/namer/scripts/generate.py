#!/usr/bin/env python3
"""Name analysis and generation helpers.

Phonetic breakdown, variation generation, sound symbolism scoring,
and hard filtering. Outputs JSON to stdout, warnings to stderr.

Usage:
    uv run python skills/namer/scripts/generate.py analyze neon
    uv run python skills/namer/scripts/generate.py variations neon
    uv run python skills/namer/scripts/generate.py phonetics neon --vibe energetic
    uv run python skills/namer/scripts/generate.py filter neon flux z0mbie
"""

from __future__ import annotations

import json
import re
import sys
from enum import StrEnum
from typing import Annotated

import typer
from loguru import logger

# ---------------------------------------------------------------------------
# Loguru: warnings/errors to stderr only
# ---------------------------------------------------------------------------
logger.remove()
logger.add(sys.stderr, level="WARNING", format="{level}: {message}")

app = typer.Typer(help="Name analysis, variation generation, phonetic scoring, and hard filtering.")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VOWELS = set("aeiouy")
CONSONANTS = set("bcdfghjklmnpqrstvwxz")

PLOSIVES = set("bpktdg")
FRICATIVES = set("fsvz")  # sh/zh handled separately
SONORANTS = set("lmnr")
AFFRICATES = {"ch", "j"}

FRONT_VOWELS = {"ee", "ih", "eh", "i", "e"}
BACK_VOWELS = {"oo", "ah", "aw", "o", "u", "a"}

# Sound symbolism: which consonant/vowel classes evoke which vibes
VIBE_PROFILES: dict[str, dict[str, float]] = {
    "vibrant": {"plosive": 0.6, "fricative": 0.3, "front_vowel": 0.7, "back_vowel": 0.3, "short": 0.6},
    "reliable": {
        "plosive": 0.3, "fricative": 0.4, "sonorant": 0.8, "back_vowel": 0.6, "front_vowel": 0.3, "short": 0.4,
    },
    "innovative": {"plosive": 0.5, "fricative": 0.7, "front_vowel": 0.6, "back_vowel": 0.3, "short": 0.7},
    "warm": {"sonorant": 0.9, "fricative": 0.2, "back_vowel": 0.8, "front_vowel": 0.2, "short": 0.3},
    "energetic": {"plosive": 0.8, "fricative": 0.5, "front_vowel": 0.8, "back_vowel": 0.2, "short": 0.8},
}

# Programming language reserved words
RESERVED_WORDS: set[str] = set()
for _lang_keywords in [
    # Python
    ["false", "none", "true", "and", "as", "assert", "async", "await", "break", "class",
     "continue", "def", "del", "elif", "else", "except", "finally", "for", "from", "global",
     "if", "import", "in", "is", "lambda", "nonlocal", "not", "or", "pass", "raise",
     "return", "try", "while", "with", "yield"],
    # JavaScript/TypeScript
    ["abstract", "arguments", "boolean", "byte", "case", "catch", "char", "const",
     "debugger", "default", "delete", "do", "double", "enum", "eval", "export",
     "extends", "final", "float", "function", "goto", "implements", "instanceof",
     "int", "interface", "let", "long", "native", "new", "null", "package", "private",
     "protected", "public", "short", "static", "super", "switch", "synchronized",
     "this", "throw", "throws", "transient", "typeof", "undefined", "var", "void",
     "volatile"],
    # Rust
    ["crate", "extern", "fn", "impl", "loop", "match", "mod", "move", "mut", "pub",
     "ref", "self", "struct", "trait", "type", "unsafe", "use", "where"],
    # Go
    ["chan", "defer", "fallthrough", "func", "go", "interface", "map", "range",
     "select", "struct", "type"],
    # Java
    ["abstract", "boolean", "byte", "catch", "class", "double", "final", "finally",
     "float", "implements", "import", "instanceof", "int", "interface", "long",
     "native", "new", "null", "package", "private", "protected", "public", "return",
     "short", "static", "super", "switch", "synchronized", "this", "throw", "throws",
     "transient", "try", "void", "volatile"],
    # C
    ["auto", "char", "const", "double", "enum", "extern", "float", "goto", "inline",
     "int", "long", "register", "restrict", "return", "short", "signed", "sizeof",
     "static", "struct", "switch", "typedef", "union", "unsigned", "void", "volatile"],
    # Ruby
    ["alias", "begin", "defined", "end", "ensure", "module", "next", "nil", "redo",
     "rescue", "retry", "self", "then", "undef", "unless", "until", "when"],
]:
    RESERVED_WORDS.update(_lang_keywords)

# Basic profanity filter (English, obvious cases)
PROFANITY_LIST: set[str] = {
    "ass", "damn", "fuck", "shit", "hell", "crap", "dick", "cock", "pussy",
    "bitch", "bastard", "slut", "whore", "piss", "tits", "boob", "anus",
    "fag", "nigger", "nigga", "cunt", "twat", "wank",
}

PREFIXES = ["go", "un", "re", "my", "no", "on", "up", "hi", "ez", "ok"]
SUFFIXES = ["kit", "lab", "ify", "ly", "io", "ai", "hq", "js", "py", "rs", "go", "dev", "app", "run", "hub"]


class Vibe(StrEnum):
    vibrant = "vibrant"
    reliable = "reliable"
    innovative = "innovative"
    warm = "warm"
    energetic = "energetic"


# ---------------------------------------------------------------------------
# Phonetic analysis
# ---------------------------------------------------------------------------


def _count_syllables(name: str) -> int:
    """Approximate syllable count by counting vowel groups."""
    name = name.lower()
    count = 0
    in_vowel = False
    for ch in name:
        if ch in VOWELS:
            if not in_vowel:
                count += 1
                in_vowel = True
        else:
            in_vowel = False
    return max(count, 1)


def _stress_pattern(name: str, syllables: int) -> str:
    """Heuristic stress pattern. First syllable for 2-syllable words, varies for longer."""
    if syllables == 1:
        return "STRESSED"
    if syllables == 2:
        return "STRESS-unstress"
    if syllables == 3:
        return "STRESS-unstress-unstress"
    return "STRESS" + "-unstress" * (syllables - 1)


def _classify_consonants(name: str) -> dict[str, list[str]]:
    """Classify consonants in the name by phonetic category."""
    name_lower = name.lower()
    result: dict[str, list[str]] = {
        "plosives": [],
        "fricatives": [],
        "sonorants": [],
        "affricates": [],
    }
    i = 0
    while i < len(name_lower):
        # Check digraphs first
        if i + 1 < len(name_lower):
            digraph = name_lower[i : i + 2]
            if digraph in ("ch", "tch"):
                result["affricates"].append(digraph)
                i += 2
                continue
            if digraph in ("sh", "zh", "th"):
                result["fricatives"].append(digraph)
                i += 2
                continue
        ch = name_lower[i]
        if ch in PLOSIVES:
            result["plosives"].append(ch)
        elif ch in FRICATIVES:
            result["fricatives"].append(ch)
        elif ch in SONORANTS:
            result["sonorants"].append(ch)
        elif ch == "j":
            result["affricates"].append(ch)
        i += 1
    return result


def _classify_vowels(name: str) -> dict[str, list[str]]:
    """Classify vowels in the name as front or back."""
    result: dict[str, list[str]] = {"front": [], "back": []}
    for ch in name.lower():
        if ch in ("e", "i"):
            result["front"].append(ch)
        elif ch in ("a", "o", "u"):
            result["back"].append(ch)
        elif ch == "y":
            # y as vowel is typically front
            result["front"].append(ch)
    return result


def _consonant_vowel_flow(name: str) -> str:
    """Generate a CV flow pattern (e.g., 'CVCV' for 'neon')."""
    pattern = []
    for ch in name.lower():
        if ch in VOWELS:
            if not pattern or pattern[-1] != "V":
                pattern.append("V")
        elif ch in CONSONANTS and (not pattern or pattern[-1] != "C"):
            pattern.append("C")
    return "".join(pattern)


def _analyze_name(name: str) -> dict:
    """Full phonetic analysis of a name."""
    syllables = _count_syllables(name)
    consonants = _classify_consonants(name)
    vowels_classified = _classify_vowels(name)
    return {
        "name": name,
        "length": len(name),
        "syllables": syllables,
        "stress_pattern": _stress_pattern(name, syllables),
        "cv_flow": _consonant_vowel_flow(name),
        "consonants": consonants,
        "vowels": vowels_classified,
        "total_consonants": sum(len(v) for v in consonants.values()),
        "total_vowels": sum(len(v) for v in vowels_classified.values()),
    }


# ---------------------------------------------------------------------------
# Sound symbolism scoring
# ---------------------------------------------------------------------------


def _sound_symbolism_score(name: str, vibe: str) -> dict:
    """Score a name's phonetic alignment with a target vibe (0-10)."""
    profile = VIBE_PROFILES.get(vibe)
    if not profile:
        return {"score": 5.0, "reasoning": f"Unknown vibe '{vibe}', returning neutral score.", "vibe": vibe}

    consonants = _classify_consonants(name)
    vowels_classified = _classify_vowels(name)
    total_consonants = sum(len(v) for v in consonants.values()) or 1
    total_vowels = sum(len(v) for v in vowels_classified.values()) or 1

    factors: list[tuple[str, float, float]] = []

    # Plosive ratio
    plosive_ratio = len(consonants["plosives"]) / total_consonants
    target = profile.get("plosive", 0.5)
    alignment = 1.0 - abs(plosive_ratio - target)
    factors.append(("plosive_alignment", alignment, target))

    # Fricative ratio
    fricative_ratio = len(consonants["fricatives"]) / total_consonants
    target = profile.get("fricative", 0.5)
    alignment = 1.0 - abs(fricative_ratio - target)
    factors.append(("fricative_alignment", alignment, target))

    # Sonorant ratio
    sonorant_ratio = len(consonants["sonorants"]) / total_consonants
    target = profile.get("sonorant", 0.5)
    alignment = 1.0 - abs(sonorant_ratio - target)
    factors.append(("sonorant_alignment", alignment, target))

    # Front vowel ratio
    front_ratio = len(vowels_classified["front"]) / total_vowels
    target = profile.get("front_vowel", 0.5)
    alignment = 1.0 - abs(front_ratio - target)
    factors.append(("front_vowel_alignment", alignment, target))

    # Shortness (inversely proportional to length)
    shortness = max(0, 1.0 - (len(name) - 3) / 10)
    target = profile.get("short", 0.5)
    alignment = 1.0 - abs(shortness - target)
    factors.append(("shortness_alignment", alignment, target))

    avg_alignment = sum(f[1] for f in factors) / len(factors)
    score = round(avg_alignment * 10, 1)

    reasoning_parts = []
    for factor_name, alignment_val, _target in factors:
        label = factor_name.replace("_", " ").title()
        if alignment_val >= 0.7:
            reasoning_parts.append(f"{label}: strong match")
        elif alignment_val >= 0.4:
            reasoning_parts.append(f"{label}: moderate match")
        else:
            reasoning_parts.append(f"{label}: weak match")

    return {
        "name": name,
        "vibe": vibe,
        "score": score,
        "reasoning": "; ".join(reasoning_parts),
        "factors": {f[0]: round(f[1], 2) for f in factors},
    }


# ---------------------------------------------------------------------------
# Variation generation
# ---------------------------------------------------------------------------


def _generate_variations(name: str) -> list[dict]:
    """Generate 10-15 variations of a name."""
    variations: list[dict] = []
    name_lower = name.lower()

    # Prefixes
    for prefix in PREFIXES[:5]:
        candidate = f"{prefix}{name_lower}"
        if candidate != name_lower:
            variations.append({"name": candidate, "strategy": "prefix", "detail": f"{prefix}- prefix"})

    # Suffixes
    for suffix in SUFFIXES[:5]:
        candidate = f"{name_lower}{suffix}"
        if candidate != name_lower:
            variations.append({"name": candidate, "strategy": "suffix", "detail": f"-{suffix} suffix"})

    # Vowel dropping
    vowel_dropped = re.sub(r"[aeiouy](?=[bcdfghjklmnpqrstvwxz])", "", name_lower, count=1)
    if vowel_dropped != name_lower and len(vowel_dropped) >= 3:
        variations.append({"name": vowel_dropped, "strategy": "vowel_drop", "detail": "dropped internal vowel"})

    # Full vowel strip (keep first and last char vowels)
    if len(name_lower) > 3:
        stripped = name_lower[0]
        for _i, ch in enumerate(name_lower[1:-1], 1):
            if ch not in VOWELS:
                stripped += ch
        stripped += name_lower[-1]
        if stripped != name_lower and len(stripped) >= 3:
            variations.append({"name": stripped, "strategy": "vowel_strip", "detail": "stripped interior vowels"})

    # Respelling: common letter swaps
    respellings = [
        (r"ck", "k"),
        (r"ph", "f"),
        (r"c(?=[eiy])", "s"),
        (r"c(?=[aou])", "k"),
        (r"x", "ks"),
        (r"qu", "kw"),
    ]
    for pattern, replacement in respellings:
        respelled = re.sub(pattern, replacement, name_lower)
        if respelled != name_lower:
            variations.append({"name": respelled, "strategy": "respelling", "detail": f"{pattern} -> {replacement}"})

    # Scoped (npm-style)
    variations.append({"name": f"@{name_lower}/{name_lower}", "strategy": "scoped", "detail": "npm scoped package"})

    # Doubled final consonant + suffix
    if name_lower[-1] in CONSONANTS:
        doubled = f"{name_lower}{name_lower[-1]}er"
        variations.append({"name": doubled, "strategy": "morpheme", "detail": "doubled consonant + -er"})

    # Truncation (first N chars)
    if len(name_lower) > 4:
        truncated = name_lower[:4]
        variations.append({"name": truncated, "strategy": "truncation", "detail": "first 4 chars"})

    # Deduplicate and limit
    seen: set[str] = set()
    unique: list[dict] = []
    for v in variations:
        if v["name"] not in seen:
            seen.add(v["name"])
            unique.append(v)
    return unique[:15]


# ---------------------------------------------------------------------------
# Hard filters
# ---------------------------------------------------------------------------


def _run_hard_filters(name: str, max_length: int = 15) -> dict:
    """Run binary pass/fail filters on a name.

    Covers: length, special chars, reserved words, profanity (English), consonant clusters.
    AI-only (not implemented here): cross-linguistic safety, brand collision.
    """
    name_lower = name.lower()
    failures: list[str] = []

    # Length check
    if len(name_lower) > max_length:
        failures.append(f"exceeds max length of {max_length} characters ({len(name_lower)} chars)")

    # Special characters: only lowercase letters and digits allowed
    if not re.match(r"^[a-z0-9]+$", name_lower):
        failures.append("contains characters other than lowercase letters and digits")

    # Reserved words
    if name_lower in RESERVED_WORDS:
        failures.append("reserved word in a programming language")

    # Profanity check (exact match and substring)
    if name_lower in PROFANITY_LIST:
        failures.append("matches profanity list")
    else:
        for word in PROFANITY_LIST:
            if len(word) >= 3 and word in name_lower:
                failures.append(f"contains profanity substring '{word}'")
                break

    # Unpronounceable consonant clusters (3+ consonants in a row, excluding common clusters)
    common_clusters = {"str", "spr", "scr", "spl", "thr", "chr", "sch", "ntr", "ndr", "mpl", "rch", "nch", "ltr"}
    consonant_runs = re.findall(r"[bcdfghjklmnpqrstvwxz]{3,}", name_lower)
    for run in consonant_runs:
        if run not in common_clusters:
            failures.append(f"unpronounceable consonant cluster '{run}'")
            break

    return {
        "name": name,
        "pass": len(failures) == 0,
        "failures": failures,
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def analyze(
    name: Annotated[str, typer.Argument(help="Name to analyze phonetically.")],
) -> None:
    """Phonetic breakdown: syllables, stress, consonant/vowel flow, sound symbolism."""
    result = _analyze_name(name)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


@app.command()
def variations(
    name: Annotated[str, typer.Argument(help="Base name to generate variations for.")],
) -> None:
    """Generate 10-15 variations: prefixes, suffixes, vowel dropping, respelling, scoping."""
    result = _generate_variations(name)
    output = {"name": name, "variations": result, "count": len(result)}
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")


@app.command()
def phonetics(
    name: Annotated[str, typer.Argument(help="Name to score for sound symbolism.")],
    vibe: Annotated[
        Vibe,
        typer.Option("--vibe", "-v", help="Target vibe to score alignment against."),
    ] = Vibe.energetic,
) -> None:
    """Score a name's sound symbolism alignment with a target vibe (0-10)."""
    result = _sound_symbolism_score(name, vibe.value)
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")


@app.command("filter")
def filter_names(
    names: Annotated[list[str] | None, typer.Argument(help="Names to filter.")] = None,
    input_file: Annotated[
        str | None,
        typer.Option("--input", "-i", help="JSON file with a 'names' array. Overrides positional args."),
    ] = None,
    max_length: Annotated[
        int,
        typer.Option("--max-length", "-m", help="Maximum allowed name length."),
    ] = 15,
) -> None:
    """Run hard filters on names: length, reserved words, special chars, profanity."""
    name_list: list[str] = []

    if input_file:
        try:
            with open(input_file) as f:
                data = json.load(f)
            if isinstance(data, list):
                name_list = data
            elif isinstance(data, dict) and "names" in data:
                name_list = data["names"]
            elif isinstance(data, dict) and "candidates" in data:
                name_list = [c.get("name", "") for c in data["candidates"] if c.get("name")]
            else:
                logger.error("Input JSON must be a list or have a 'names'/'candidates' key.")
                raise typer.Exit(code=1)
        except FileNotFoundError:
            logger.error(f"Input file not found: {input_file}")
            raise typer.Exit(code=1) from None
        except json.JSONDecodeError as exc:
            logger.error(f"Invalid JSON in {input_file}: {exc}")
            raise typer.Exit(code=1) from None
    elif names:
        name_list = names
    else:
        logger.error("Provide names as arguments or via --input JSON file.")
        raise typer.Exit(code=1)

    results = [_run_hard_filters(n, max_length=max_length) for n in name_list]
    passed = [r for r in results if r["pass"]]
    failed = [r for r in results if not r["pass"]]

    output = {
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "results": results,
    }
    json.dump(output, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    app()
