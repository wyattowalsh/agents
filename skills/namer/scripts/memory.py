#!/usr/bin/env python3
"""Namer memory — Long-term naming preferences across sessions.

Persists archetype affinities, phonetic likes/dislikes, length
preferences, weight overrides, inspirations, selections, and rejections.

Storage: ~/.claude/namer/memory.json
Output:  JSON to stdout (for LLM consumption)
"""

from __future__ import annotations

import json
import os


def get_agent_dir(skill_name: str) -> Path:
    """Get the base directory for a skill based on the active agent."""
    agent = os.environ.get("AGENT_NAME", "").lower()
    for cli, folder in [("GEMINI_CLI", ".gemini"), ("COPILOT_CLI", ".copilot"), ("CODEX_CLI", ".codex")]:
        if os.environ.get(cli) == "1" or folder.strip(".") in agent:
            return Path.home() / folder / skill_name
    return Path.home() / ".claude" / skill_name

import sys
import tempfile
from collections import Counter
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Annotated

import typer
from loguru import logger

# ---------------------------------------------------------------------------
# Loguru: warnings/errors to stderr only
# ---------------------------------------------------------------------------
logger.remove()
logger.add(sys.stderr, level="WARNING", format="{level}: {message}")

app = typer.Typer(help="Long-term naming preference memory.", no_args_is_help=True)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MEMORY_DIR = str(get_agent_dir("namer"))
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")
MAX_FILE_SIZE = 50 * 1024  # 50KB
MAX_STRING_LEN = 500
MAX_SELECTIONS = 100  # Keep last N selections
MAX_REJECTIONS = 50
MAX_INSPIRATIONS = 30

ARCHETYPES = [
    "evocative_fragment",
    "classical_root",
    "compound_blend",
    "invented_word",
    "metaphorical_transfer",
    "descriptive_creative",
]


class PrefType(StrEnum):
    archetype = "archetype"
    phonetic = "phonetic"
    length = "length"
    vibe = "vibe"


class RejectionType(StrEnum):
    phonetic = "phonetic"
    archetype = "archetype"
    name = "name"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truncate(s: str) -> str:
    return s[:MAX_STRING_LEN] if len(s) > MAX_STRING_LEN else s


def _out(obj: dict) -> None:
    print(json.dumps(obj, indent=2))


def _empty_memory() -> dict:
    return {
        "version": 1,
        "updated_at": datetime.now().isoformat(),
        "style_preferences": {
            "archetype_affinities": {},
            "preferred_length": {},
            "phonetic_likes": [],
            "phonetic_dislikes": [],
            "vibe_words": [],
        },
        "selections": [],
        "rejections": [],
        "weight_overrides": {
            "intrinsic_split": None,
            "extrinsic_split": None,
            "dimension_overrides": {},
        },
        "context_defaults": {
            "most_common_context": None,
            "typical_platforms": [],
            "session_count": 0,
        },
        "inspirations": [],
    }


def load_memory() -> dict:
    """Load memory from disk. Returns empty structure if missing/corrupt."""
    if not os.path.exists(MEMORY_FILE):
        return _empty_memory()
    try:
        with open(MEMORY_FILE) as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return _empty_memory()
        # Ensure all top-level keys exist
        base = _empty_memory()
        for key in base:
            if key not in data:
                data[key] = base[key]
        # Ensure nested dicts
        for parent, defaults in [
            ("style_preferences", base["style_preferences"]),
            ("weight_overrides", base["weight_overrides"]),
            ("context_defaults", base["context_defaults"]),
        ]:
            if not isinstance(data.get(parent), dict):
                data[parent] = defaults
            else:
                for k, v in defaults.items():
                    if k not in data[parent]:
                        data[parent][k] = v
        # Ensure lists
        for parent_key in ("selections", "rejections", "inspirations"):
            if not isinstance(data.get(parent_key), list):
                data[parent_key] = []
        sp = data["style_preferences"]
        for list_key in ("phonetic_likes", "phonetic_dislikes", "vibe_words"):
            if not isinstance(sp.get(list_key), list):
                sp[list_key] = []
        if not isinstance(sp.get("archetype_affinities"), dict):
            sp["archetype_affinities"] = {}
        if not isinstance(sp.get("preferred_length"), dict):
            sp["preferred_length"] = {}
        return data
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return _empty_memory()


def save_memory(data: dict) -> None:
    """Atomically write memory to disk."""
    to_write = {**data, "updated_at": datetime.now().isoformat()}
    os.makedirs(MEMORY_DIR, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=MEMORY_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(to_write, f, indent=2)
        os.replace(tmp_path, MEMORY_FILE)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def _file_size_warning() -> dict | None:
    if os.path.exists(MEMORY_FILE) and os.path.getsize(MEMORY_FILE) > MAX_FILE_SIZE:
        return {"warning": f"memory.json exceeds {MAX_FILE_SIZE // 1024}KB — consider running prune"}
    return None


def _update_context_defaults(data: dict) -> None:
    """Recompute context_defaults from selection history."""
    selections = data.get("selections", [])
    if not selections:
        return
    ctx = data["context_defaults"]
    ctx["session_count"] = ctx.get("session_count", 0) + 1
    contexts = [s["context"] for s in selections if s.get("context")]
    if contexts:
        ctx["most_common_context"] = Counter(contexts).most_common(1)[0][0]


def _update_archetype_affinities(data: dict) -> None:
    """Recompute archetype affinities from selections (recency-weighted)."""
    selections = data.get("selections", [])
    if not selections:
        return
    counts: dict[str, float] = {}
    total = 0.0
    for i, sel in enumerate(selections):
        arch = sel.get("archetype")
        if arch:
            weight = 1.0 + (i / max(len(selections), 1))  # newer = higher weight
            counts[arch] = counts.get(arch, 0) + weight
            total += weight
    if total > 0:
        data["style_preferences"]["archetype_affinities"] = {
            k: round(v / total, 3) for k, v in sorted(counts.items(), key=lambda x: -x[1])
        }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@app.command()
def load(
    topic: Annotated[
        str | None,
        typer.Option(help="Filter by topic: style_preferences, selections, rejections, weight_overrides, inspirations"),
    ] = None,
) -> None:
    """Load memory, optionally filtered by topic."""
    data = load_memory()
    if topic:
        if topic in data and topic not in ("version", "updated_at"):
            result = {topic: data[topic]}
        else:
            _out({"status": "error", "message": f"Unknown topic: {topic}"})
            raise typer.Exit(1) from None
    else:
        result = {k: v for k, v in data.items() if k not in ("version", "updated_at")}
    output: dict = {"status": "ok", "memory": result}
    warning = _file_size_warning()
    if warning:
        output.update(warning)
    _out(output)


@app.command("save-selection")
def save_selection(
    name: Annotated[str, typer.Option(help="Selected name")],
    archetype: Annotated[str, typer.Option(help="Name archetype (e.g. evocative_fragment)")],
    context: Annotated[str, typer.Option(help="Naming context preset (e.g. cli-tool)")],
    score: Annotated[int, typer.Option(help="Composite score 0-100")],
    query: Annotated[str, typer.Option(help="What was being named")],
) -> None:
    """Record a name the user selected."""
    data = load_memory()
    today = date.today().isoformat()
    data["selections"].append({
        "name": _truncate(name),
        "archetype": _truncate(archetype),
        "context": _truncate(context),
        "composite_score": score,
        "date": today,
        "query": _truncate(query),
    })
    # Trim oldest if over limit
    if len(data["selections"]) > MAX_SELECTIONS:
        data["selections"] = data["selections"][-MAX_SELECTIONS:]
    _update_archetype_affinities(data)
    _update_context_defaults(data)
    save_memory(data)
    _out({"status": "saved", "name": name, "archetype": archetype})


@app.command("save-preference")
def save_preference(
    pref_type: Annotated[PrefType, typer.Option("--type", help="Preference type")],
    value: Annotated[str, typer.Option(help="Preference value")],
    like: Annotated[bool, typer.Option("--like", help="Mark as liked (for phonetic/archetype)")] = True,
    dislike: Annotated[bool, typer.Option("--dislike", help="Mark as disliked (for phonetic)")] = False,
) -> None:
    """Save a style preference."""
    data = load_memory()
    sp = data["style_preferences"]
    val = _truncate(value)

    if pref_type == PrefType.archetype:
        # Boost or suppress an archetype
        affinities = sp["archetype_affinities"]
        current = affinities.get(val, 0.1)
        if dislike:
            affinities[val] = max(0.0, round(current - 0.05, 3))
        else:
            affinities[val] = min(1.0, round(current + 0.05, 3))
        action = "boosted" if not dislike else "suppressed"

    elif pref_type == PrefType.phonetic:
        target = sp["phonetic_dislikes"] if dislike else sp["phonetic_likes"]
        if val not in target:
            target.append(val)
        # Remove from opposite list if present
        opposite = sp["phonetic_likes"] if dislike else sp["phonetic_dislikes"]
        if val in opposite:
            opposite.remove(val)
        action = "disliked" if dislike else "liked"

    elif pref_type == PrefType.length:
        # Parse "min=4", "max=7", "min=4,max=7"
        for part in val.split(","):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip()
                if k in ("min", "max") and v.strip().isdigit():
                    sp["preferred_length"][k] = int(v.strip())
        action = "set"

    elif pref_type == PrefType.vibe:
        if val not in sp["vibe_words"]:
            sp["vibe_words"].append(val)
        action = "added"

    else:
        _out({"status": "error", "message": f"Unknown type: {pref_type}"})
        raise typer.Exit(1) from None

    save_memory(data)
    _out({"status": action, "type": pref_type.value, "value": val})


@app.command("save-rejection")
def save_rejection(
    pattern: Annotated[str, typer.Option(help="Rejected pattern or name")],
    rejection_type: Annotated[RejectionType, typer.Option("--type", help="Rejection type")],
    reason: Annotated[str, typer.Option(help="Why it was rejected")] = "",
) -> None:
    """Record a rejected naming pattern."""
    data = load_memory()
    today = date.today().isoformat()
    truncated_pattern = _truncate(pattern)

    # Upsert by pattern + type
    existing = next(
        (r for r in data["rejections"]
         if r.get("pattern") == truncated_pattern and r.get("type") == rejection_type.value),
        None,
    )
    if existing:
        existing["date"] = today
        if reason:
            existing["reason"] = _truncate(reason)
        action = "updated"
    else:
        data["rejections"].append({
            "pattern": truncated_pattern,
            "type": rejection_type.value,
            "date": today,
            "reason": _truncate(reason),
        })
        action = "saved"

    # Trim oldest if over limit
    if len(data["rejections"]) > MAX_REJECTIONS:
        data["rejections"] = data["rejections"][-MAX_REJECTIONS:]

    # Also add to phonetic_dislikes if phonetic rejection
    if rejection_type == RejectionType.phonetic:
        dislikes = data["style_preferences"]["phonetic_dislikes"]
        if truncated_pattern not in dislikes:
            dislikes.append(truncated_pattern)

    save_memory(data)
    _out({"status": action, "pattern": truncated_pattern, "type": rejection_type.value})


@app.command("save-inspiration")
def save_inspiration(
    name: Annotated[str, typer.Option(help="Inspirational name (e.g. Vercel)")],
    context: Annotated[str, typer.Option(help="Context where cited")] = "",
) -> None:
    """Record a name the user cited as aspirational."""
    data = load_memory()
    today = date.today().isoformat()
    truncated_name = _truncate(name)

    # Upsert by name
    existing = next(
        (i for i in data["inspirations"] if i.get("name") == truncated_name), None
    )
    if existing:
        existing["cited"] = today
        if context:
            existing["context"] = _truncate(context)
        action = "updated"
    else:
        entry: dict = {"name": truncated_name, "cited": today}
        if context:
            entry["context"] = _truncate(context)
        data["inspirations"].append(entry)
        action = "saved"

    # Trim oldest if over limit
    if len(data["inspirations"]) > MAX_INSPIRATIONS:
        data["inspirations"] = data["inspirations"][-MAX_INSPIRATIONS:]

    save_memory(data)
    _out({"status": action, "name": truncated_name})


@app.command("save-weights")
def save_weights(
    intrinsic_split: Annotated[float | None, typer.Option(help="Intrinsic weight split (0.0-1.0)")] = None,
    extrinsic_split: Annotated[float | None, typer.Option(help="Extrinsic weight split (0.0-1.0)")] = None,
    dimension: Annotated[list[str] | None, typer.Option(help="Dimension override KEY=VAL (repeatable)")] = None,
) -> None:
    """Save custom scoring weight overrides."""
    data = load_memory()
    wo = data["weight_overrides"]

    if intrinsic_split is not None:
        wo["intrinsic_split"] = round(min(1.0, max(0.0, intrinsic_split)), 2)
    if extrinsic_split is not None:
        wo["extrinsic_split"] = round(min(1.0, max(0.0, extrinsic_split)), 2)
    if dimension:
        for d in dimension:
            if "=" in d:
                k, v = d.split("=", 1)
                try:
                    wo["dimension_overrides"][k.strip()] = round(float(v.strip()), 3)
                except ValueError:
                    logger.warning(f"Ignoring invalid dimension override: {d}")

    save_memory(data)
    _out({"status": "saved", "weight_overrides": wo})


@app.command()
def remove(
    topic: Annotated[
        str,
        typer.Option(help="Topic: selections, rejections, inspirations, phonetic_likes, phonetic_dislikes"),
    ],
    key: Annotated[str, typer.Option(help="Value to remove (name, pattern, or word)")],
) -> None:
    """Remove a memory entry by topic and key."""
    data = load_memory()
    removed = False

    if topic == "selections":
        before = len(data["selections"])
        data["selections"] = [s for s in data["selections"] if s.get("name") != key]
        removed = len(data["selections"]) < before
        if removed:
            _update_archetype_affinities(data)

    elif topic == "rejections":
        before = len(data["rejections"])
        data["rejections"] = [r for r in data["rejections"] if r.get("pattern") != key]
        removed = len(data["rejections"]) < before

    elif topic == "inspirations":
        before = len(data["inspirations"])
        data["inspirations"] = [i for i in data["inspirations"] if i.get("name") != key]
        removed = len(data["inspirations"]) < before

    elif topic in ("phonetic_likes", "phonetic_dislikes", "vibe_words"):
        sp = data["style_preferences"]
        if key in sp.get(topic, []):
            sp[topic].remove(key)
            removed = True

    else:
        _out({"status": "error", "message": f"Unknown topic: {topic}"})
        raise typer.Exit(1) from None

    if removed:
        save_memory(data)
        _out({"status": "removed", "topic": topic, "key": key})
    else:
        _out({"status": "not_found", "topic": topic, "key": key})


@app.command()
def prune(
    stale_days: Annotated[int, typer.Option(help="Remove entries older than N days")] = 120,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be pruned")] = False,
) -> None:
    """Remove stale memory entries."""
    data = load_memory()
    today = date.today()
    pruned: dict[str, list] = {"selections": [], "rejections": [], "inspirations": []}

    def _is_stale(entry: dict, field: str) -> bool:
        val = entry.get(field)
        if not val:
            return True
        try:
            return (today - date.fromisoformat(val)) > timedelta(days=stale_days)
        except (ValueError, TypeError):
            return True

    kept_selections = []
    for s in data["selections"]:
        if _is_stale(s, "date"):
            pruned["selections"].append(s.get("name", "?"))
        else:
            kept_selections.append(s)

    kept_rejections = []
    for r in data["rejections"]:
        if _is_stale(r, "date"):
            pruned["rejections"].append(r.get("pattern", "?"))
        else:
            kept_rejections.append(r)

    kept_inspirations = []
    for i in data["inspirations"]:
        if _is_stale(i, "cited"):
            pruned["inspirations"].append(i.get("name", "?"))
        else:
            kept_inspirations.append(i)

    total = sum(len(v) for v in pruned.values())

    if not dry_run and total > 0:
        data["selections"] = kept_selections
        data["rejections"] = kept_rejections
        data["inspirations"] = kept_inspirations
        _update_archetype_affinities(data)
        save_memory(data)

    _out({
        "status": "dry_run" if dry_run else "pruned",
        "total_removed": total,
        "removed": {k: v for k, v in pruned.items() if v},
    })


@app.command()
def stats() -> None:
    """Show summary statistics of stored memories."""
    data = load_memory()
    sp = data["style_preferences"]
    result: dict = {
        "status": "ok",
        "counts": {
            "selections": len(data["selections"]),
            "rejections": len(data["rejections"]),
            "inspirations": len(data["inspirations"]),
            "phonetic_likes": len(sp.get("phonetic_likes", [])),
            "phonetic_dislikes": len(sp.get("phonetic_dislikes", [])),
            "vibe_words": len(sp.get("vibe_words", [])),
            "archetype_affinities": len(sp.get("archetype_affinities", {})),
            "has_weight_overrides": any(
                v is not None and v != {}
                for v in data.get("weight_overrides", {}).values()
            ),
            "has_length_prefs": bool(sp.get("preferred_length")),
            "session_count": data.get("context_defaults", {}).get("session_count", 0),
        },
        "top_archetype": None,
        "most_common_context": data.get("context_defaults", {}).get("most_common_context"),
        "updated_at": data.get("updated_at"),
    }
    affinities = sp.get("archetype_affinities", {})
    if affinities:
        result["top_archetype"] = max(affinities, key=affinities.get)

    warning = _file_size_warning()
    if warning:
        result.update(warning)
    _out(result)


@app.command("compute-affinities")
def compute_affinities() -> None:
    """Recompute archetype affinities from full selection history."""
    data = load_memory()
    _update_archetype_affinities(data)
    save_memory(data)
    _out({
        "status": "recomputed",
        "archetype_affinities": data["style_preferences"]["archetype_affinities"],
    })


if __name__ == "__main__":
    app()
