#!/usr/bin/env python3
"""
email-whiz memory — Long-term user memory for email-whiz.

Persists VIP/noise senders, triage overrides, corrections, filter history,
label preferences, and inbox patterns across sessions.

Storage: ~/.claude/email-whiz/memory.json
Output:  JSON to stdout (for LLM consumption)
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Annotated

import typer
from constants import EMAIL_WHIZ_DIR

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MEMORY_DIR = EMAIL_WHIZ_DIR
MEMORY_FILE = os.path.join(MEMORY_DIR, "memory.json")
MAX_FILE_SIZE = 50 * 1024  # 50KB
MAX_STRING_LEN = 500  # Defense-in-depth: truncate persisted free-text fields


def _truncate(s: str) -> str:
    """Truncate string to MAX_STRING_LEN to prevent unbounded storage."""
    return s[:MAX_STRING_LEN] if len(s) > MAX_STRING_LEN else s

# Mode → topics mapping
MODE_TOPICS: dict[str, list[str]] = {
    "triage": ["senders", "triage", "corrections"],
    "inbox-zero": ["senders", "triage", "corrections", "inbox_patterns"],
    "filters": ["senders", "filters", "corrections"],
    "auto-rules": ["senders", "filters", "corrections"],
    "analytics": ["inbox_patterns", "senders"],
    "senders": ["senders", "corrections"],
    "cleanup": ["senders", "triage"],
    "newsletters": ["senders", "filters"],
    "labels": ["labels"],
    "audit": ["senders", "triage", "corrections", "filters", "labels", "inbox_patterns"],
    "auto-scan": ["senders", "triage", "corrections", "filters", "labels", "inbox_patterns"],
    "search": [],
    "digest": [],
}

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class SenderType(StrEnum):
    vip = "vip"
    noise = "noise"


class Bucket(StrEnum):
    DO = "DO"
    DELEGATE = "DELEGATE"
    DEFER = "DEFER"
    REFERENCE = "REFERENCE"
    NOISE = "NOISE"


class Effectiveness(StrEnum):
    high = "high"
    medium = "medium"
    low = "low"
    failed = "failed"


# ---------------------------------------------------------------------------
# Storage helpers
# ---------------------------------------------------------------------------


def _empty_memory() -> dict:
    return {
        "version": 1,
        "updated_at": datetime.now().isoformat(),
        "correction_sequence": 0,
        "senders": {"vip": [], "noise": []},
        "triage": {"overrides": []},
        "corrections": [],
        "filters": {"effective": [], "failed": []},
        "labels": {},
        "inbox_patterns": {},
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
        # Validate nested structure — replace null/wrong-type with defaults
        for key, default in base.items():
            if isinstance(default, (dict, list)) and not isinstance(data[key], type(default)):
                data[key] = default
        for parent, sub_defaults in [
            ("senders", {"vip": [], "noise": []}),
            ("triage", {"overrides": []}),
            ("filters", {"effective": [], "failed": []}),
        ]:
            for sub_key, sub_default in sub_defaults.items():
                if not isinstance(data[parent].get(sub_key), list):
                    data[parent][sub_key] = sub_default
        # Migrate correction_sequence from existing IDs if newly added
        if data.get("correction_sequence", 0) == 0 and data.get("corrections"):
            max_n = 0
            for c in data["corrections"]:
                cid = c.get("id", "")
                if cid.startswith("C-") and cid[2:].isdigit():
                    max_n = max(max_n, int(cid[2:]))
            if max_n > 0:
                data["correction_sequence"] = max_n
        return data
    except (json.JSONDecodeError, OSError, TypeError, ValueError):
        return _empty_memory()


def save_memory(data: dict) -> None:
    """Atomically write memory to disk (write temp + rename)."""
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


def _out(obj: dict) -> None:
    """Print JSON to stdout."""
    print(json.dumps(obj, indent=2))


def _file_size_warning(data: dict) -> dict | None:
    """Return warning dict if memory file exceeds MAX_FILE_SIZE."""
    if os.path.exists(MEMORY_FILE) and os.path.getsize(MEMORY_FILE) > MAX_FILE_SIZE:
        return {"warning": f"memory.json exceeds {MAX_FILE_SIZE // 1024}KB — consider running prune"}
    return None


def _next_correction_id(data: dict) -> str:
    """Generate next monotonic correction ID from stored sequence counter."""
    seq = data.get("correction_sequence", 0) + 1
    data["correction_sequence"] = seq
    return f"C-{seq:03d}"


# ---------------------------------------------------------------------------
# Typer app
# ---------------------------------------------------------------------------

app = typer.Typer(help="Long-term user memory for email-whiz.", no_args_is_help=True)


@app.command()
def load(
    topic: Annotated[
        str | None,
        typer.Option(help="Filter by topic: senders, triage, corrections, filters, labels, inbox_patterns"),
    ] = None,
    mode: Annotated[
        str | None,
        typer.Option(help="Filter by email-whiz mode (e.g. triage, inbox-zero)"),
    ] = None,
) -> None:
    """Load memories, optionally filtered by topic or mode."""
    data = load_memory()
    result: dict = {}

    if mode:
        topics = MODE_TOPICS.get(mode)
        if topics is None:
            _out({"status": "error", "message": f"Unknown mode: {mode}. Valid: {', '.join(sorted(MODE_TOPICS))}"})
            raise typer.Exit(1) from None
        for t in topics:
            if t in data:
                result[t] = data[t]
    elif topic:
        if topic in data:
            result[topic] = data[topic]
        else:
            _out({"status": "error", "message": f"Unknown topic: {topic}"})
            raise typer.Exit(1) from None
    else:
        result = {k: v for k, v in data.items() if k not in ("version", "updated_at", "correction_sequence")}

    output = {"status": "ok", "memory": result}
    warning = _file_size_warning(data)
    if warning:
        output.update(warning)
    _out(output)


@app.command("save-sender")
def save_sender(
    email: Annotated[str, typer.Option(help="Sender email address")],
    sender_type: Annotated[SenderType, typer.Option("--type", help="Sender type: vip or noise")],
    reason: Annotated[str, typer.Option(help="Why this sender is VIP/noise")],
    source: Annotated[str, typer.Option(help="Which mode identified this sender")],
    name: Annotated[str | None, typer.Option(help="Sender display name")] = None,
    confidence: Annotated[float, typer.Option(help="Confidence score 0.0-1.0")] = 0.8,
) -> None:
    """Add or update a VIP or noise sender (upserts by email)."""
    data = load_memory()
    sender_list = data["senders"][sender_type.value]
    today = date.today().isoformat()
    truncated_reason = _truncate(reason)

    # Upsert: find existing by email
    existing = next((s for s in sender_list if s.get("email") == email), None)
    if existing:
        existing["reason"] = truncated_reason
        existing["confidence"] = confidence
        existing["last_confirmed"] = today
        existing["source"] = source
        if name:
            existing["name"] = _truncate(name)
        action = "updated"
    else:
        entry: dict = {
            "email": email,
            "reason": truncated_reason,
            "confidence": confidence,
            "first_seen": today,
            "last_confirmed": today,
            "source": source,
        }
        if name:
            entry["name"] = _truncate(name)
        # Extract domain for noise senders
        if sender_type == SenderType.noise and "@" in email:
            entry["domain"] = email.split("@", 1)[1]
        sender_list.append(entry)
        action = "saved"

    save_memory(data)
    _out({"status": action, "type": sender_type.value, "email": email})


@app.command("save-override")
def save_override(
    pattern: Annotated[str, typer.Option(help="Gmail search pattern (e.g. 'from:hr@co.com subject:survey')")],
    bucket: Annotated[Bucket, typer.Option(help="Target triage bucket")],
    reason: Annotated[str, typer.Option(help="Why this override exists")],
    confidence: Annotated[float, typer.Option(help="Confidence score 0.0-1.0")] = 0.85,
) -> None:
    """Add or update a triage override (upserts by pattern)."""
    data = load_memory()
    overrides = data["triage"]["overrides"]
    today = date.today().isoformat()

    truncated_pattern = _truncate(pattern)
    truncated_reason = _truncate(reason)

    existing = next((o for o in overrides if o.get("pattern") == truncated_pattern), None)
    if existing:
        existing["bucket"] = bucket.value
        existing["reason"] = truncated_reason
        existing["confidence"] = confidence
        existing["last_used"] = today
        action = "updated"
    else:
        overrides.append({
            "pattern": truncated_pattern,
            "bucket": bucket.value,
            "reason": truncated_reason,
            "confidence": confidence,
            "created": today,
            "last_used": today,
            "use_count": 0,
        })
        action = "saved"

    save_memory(data)
    _out({"status": action, "pattern": pattern, "bucket": bucket.value})


@app.command("save-correction")
def save_correction(
    mode: Annotated[str, typer.Option(help="Which mode made the wrong classification")],
    what: Annotated[str, typer.Option(help="What was misclassified")],
    correction: Annotated[str, typer.Option(help="What the user corrected it to")],
    pattern: Annotated[str, typer.Option(help="Gmail pattern to match in future")],
    action: Annotated[Bucket, typer.Option(help="Correct triage bucket")],
) -> None:
    """Record a user correction of an auto-classification."""
    data = load_memory()
    corrections = data["corrections"]
    today = date.today().isoformat()
    truncated_pattern = _truncate(pattern)
    truncated_what = _truncate(what)
    truncated_correction = _truncate(correction)

    # Check for existing correction on same pattern
    existing = next((c for c in corrections if c.get("pattern") == truncated_pattern), None)
    if existing:
        existing["mode"] = mode
        existing["what"] = truncated_what
        existing["correction"] = truncated_correction
        existing["action"] = action.value
        existing["last_used"] = today
        existing["applied_count"] = existing.get("applied_count", 0) + 1
        cid = existing["id"]
        status = "updated"
    else:
        cid = _next_correction_id(data)
        corrections.append({
            "id": cid,
            "mode": mode,
            "what": truncated_what,
            "correction": truncated_correction,
            "pattern": truncated_pattern,
            "action": action.value,
            "created": today,
            "last_used": today,
            "applied_count": 0,
        })
        status = "saved"

    save_memory(data)
    _out({"status": status, "id": cid, "pattern": truncated_pattern})


@app.command("save-filter")
def save_filter(
    filter_id: Annotated[str, typer.Option(help="Gmail filter ID or 'rejected' for failed suggestions")],
    description: Annotated[str, typer.Option(help="Human-readable filter description")],
    monthly_matches: Annotated[int | None, typer.Option(help="Estimated monthly match count")] = None,
    effectiveness: Annotated[Effectiveness, typer.Option(help="Filter effectiveness rating")] = Effectiveness.medium,
) -> None:
    """Record filter effectiveness or a rejected suggestion."""
    data = load_memory()
    today = date.today().isoformat()
    truncated_desc = _truncate(description)

    if effectiveness == Effectiveness.failed:
        # Check for existing failed filter with same description
        failed_list = data["filters"]["failed"]
        existing = next((f for f in failed_list if f.get("description") == truncated_desc), None)
        if not existing:
            failed_list.append({
                "criteria": filter_id,
                "description": truncated_desc,
                "reason": "User rejected suggestion",
                "created": today,
            })
        save_memory(data)
        _out({"status": "saved", "type": "failed", "description": truncated_desc})
    else:
        effective_list = data["filters"]["effective"]
        existing = next((f for f in effective_list if f.get("filter_id") == filter_id), None)
        if existing:
            existing["description"] = truncated_desc
            existing["last_checked"] = today
            if monthly_matches is not None:
                existing["monthly_matches"] = monthly_matches
            existing["effectiveness"] = effectiveness.value
            status = "updated"
        else:
            entry = {
                "filter_id": filter_id,
                "description": truncated_desc,
                "created": today,
                "last_checked": today,
                "effectiveness": effectiveness.value,
            }
            if monthly_matches is not None:
                entry["monthly_matches"] = monthly_matches
            effective_list.append(entry)
            status = "saved"
        save_memory(data)
        _out({"status": status, "filter_id": filter_id})


@app.command("save-labels")
def save_labels(
    structure: Annotated[
        str | None,
        typer.Option(help="Preferred label structure (e.g. '_projects/, _dev/')"),
    ] = None,
    convention: Annotated[
        str | None,
        typer.Option(help="Naming convention (e.g. 'underscore-prefix, slash')"),
    ] = None,
    avoid: Annotated[str | None, typer.Option(help="JSON array of label names to avoid")] = None,
) -> None:
    """Update label preferences."""
    data = load_memory()

    if structure:
        data["labels"]["preferred_structure"] = structure
    if convention:
        data["labels"]["naming_convention"] = convention
    if avoid:
        try:
            data["labels"]["avoid"] = json.loads(avoid)
        except json.JSONDecodeError:
            _out({"status": "error", "message": "Invalid JSON for --avoid"})
            raise typer.Exit(1) from None

    save_memory(data)
    _out({"status": "saved", "labels": data["labels"]})


@app.command("save-patterns")
def save_patterns(
    daily_volume: Annotated[int | None, typer.Option(help="Typical daily email volume")] = None,
    busy: Annotated[str | None, typer.Option(help="JSON array of busy periods (e.g. '[\"Monday mornings\"]')")] = None,
    quiet: Annotated[str | None, typer.Option(help="JSON array of quiet periods")] = None,
) -> None:
    """Update inbox pattern observations."""
    data = load_memory()
    patterns = data["inbox_patterns"]

    if daily_volume is not None:
        patterns["typical_daily_volume"] = daily_volume
    if busy:
        try:
            patterns["busy_periods"] = json.loads(busy)
        except json.JSONDecodeError:
            _out({"status": "error", "message": "Invalid JSON for --busy"})
            raise typer.Exit(1) from None
    if quiet:
        try:
            patterns["quiet_periods"] = json.loads(quiet)
        except json.JSONDecodeError:
            _out({"status": "error", "message": "Invalid JSON for --quiet"})
            raise typer.Exit(1) from None

    patterns["last_computed"] = date.today().isoformat()
    save_memory(data)
    _out({"status": "saved", "inbox_patterns": patterns})


@app.command()
def remove(
    topic: Annotated[str, typer.Option(help="Topic: senders, triage, corrections, filters")],
    email: Annotated[str | None, typer.Option(help="Sender email to remove (for senders topic)")] = None,
    id: Annotated[str | None, typer.Option(help="Correction ID to remove (for corrections topic)")] = None,
    pattern: Annotated[str | None, typer.Option(help="Override pattern to remove (for triage topic)")] = None,
    filter_id: Annotated[str | None, typer.Option(help="Filter ID to remove (for filters topic)")] = None,
) -> None:
    """Remove a memory entry by topic and identifier."""
    data = load_memory()
    removed = False

    if topic == "senders" and email:
        for sender_type in ("vip", "noise"):
            before = len(data["senders"][sender_type])
            data["senders"][sender_type] = [
                s for s in data["senders"][sender_type] if s.get("email") != email
            ]
            if len(data["senders"][sender_type]) < before:
                removed = True

    elif topic == "corrections" and id:
        before = len(data["corrections"])
        data["corrections"] = [c for c in data["corrections"] if c.get("id") != id]
        removed = len(data["corrections"]) < before

    elif topic == "triage" and pattern:
        before = len(data["triage"]["overrides"])
        data["triage"]["overrides"] = [
            o for o in data["triage"]["overrides"] if o.get("pattern") != pattern
        ]
        removed = len(data["triage"]["overrides"]) < before

    elif topic == "filters" and filter_id:
        for ftype in ("effective", "failed"):
            before = len(data["filters"][ftype])
            key = "filter_id" if ftype == "effective" else "criteria"
            data["filters"][ftype] = [
                f for f in data["filters"][ftype] if f.get(key) != filter_id
            ]
            if len(data["filters"][ftype]) < before:
                removed = True

    else:
        msg = "Provide --topic with --email, --id, --pattern, or --filter-id"
        _out({"status": "error", "message": msg})
        raise typer.Exit(1)

    if removed:
        save_memory(data)
        _out({"status": "removed", "topic": topic})
    else:
        _out({"status": "not_found", "topic": topic})


@app.command()
def prune(
    vip_stale_days: Annotated[int, typer.Option(help="Remove VIPs unconfirmed for N days")] = 90,
    noise_stale_days: Annotated[int, typer.Option(help="Remove noise senders unconfirmed for N days")] = 90,
    override_stale_days: Annotated[int, typer.Option(help="Remove overrides unused for N days")] = 60,
    correction_stale_days: Annotated[int, typer.Option(help="Remove corrections unused for N days")] = 120,
    dry_run: Annotated[bool, typer.Option("--dry-run", help="Show what would be pruned without removing")] = False,
) -> None:
    """Remove stale memory entries based on age thresholds."""
    data = load_memory()
    today = date.today()
    pruned: dict[str, list] = {"vip": [], "noise": [], "overrides": [], "corrections": []}

    def _is_stale(entry: dict, date_field: str, max_days: int) -> bool:
        val = entry.get(date_field)
        if not val:
            return True  # No date = stale
        try:
            entry_date = date.fromisoformat(val)
            return (today - entry_date) > timedelta(days=max_days)
        except (ValueError, TypeError):
            return True

    # Prune VIP senders
    kept_vip = []
    for s in data["senders"]["vip"]:
        if _is_stale(s, "last_confirmed", vip_stale_days):
            pruned["vip"].append(s.get("email", "unknown"))
        else:
            kept_vip.append(s)

    # Prune noise senders
    kept_noise = []
    for s in data["senders"]["noise"]:
        if _is_stale(s, "last_confirmed", noise_stale_days):
            pruned["noise"].append(s.get("email", "unknown"))
        else:
            kept_noise.append(s)

    # Prune overrides
    kept_overrides = []
    for o in data["triage"]["overrides"]:
        if _is_stale(o, "last_used", override_stale_days):
            pruned["overrides"].append(o.get("pattern", "unknown"))
        else:
            kept_overrides.append(o)

    # Prune corrections
    kept_corrections = []
    for c in data["corrections"]:
        if _is_stale(c, "last_used", correction_stale_days):
            pruned["corrections"].append(c.get("id", "unknown"))
        else:
            kept_corrections.append(c)

    total_pruned = sum(len(v) for v in pruned.values())

    if not dry_run and total_pruned > 0:
        data["senders"]["vip"] = kept_vip
        data["senders"]["noise"] = kept_noise
        data["triage"]["overrides"] = kept_overrides
        data["corrections"] = kept_corrections
        save_memory(data)

    _out({
        "status": "dry_run" if dry_run else "pruned",
        "total_removed": total_pruned,
        "removed": {k: v for k, v in pruned.items() if v},
    })


@app.command()
def stats() -> None:
    """Show summary statistics of stored memories."""
    data = load_memory()

    def _oldest(entries: list[dict], field: str) -> str | None:
        dates = [e.get(field) for e in entries if e.get(field)]
        return min(dates) if dates else None

    result = {
        "status": "ok",
        "counts": {
            "vip_senders": len(data["senders"]["vip"]),
            "noise_senders": len(data["senders"]["noise"]),
            "triage_overrides": len(data["triage"]["overrides"]),
            "corrections": len(data["corrections"]),
            "effective_filters": len(data["filters"]["effective"]),
            "failed_filters": len(data["filters"]["failed"]),
            "has_label_prefs": bool(data["labels"]),
            "has_inbox_patterns": bool(data["inbox_patterns"]),
        },
        "oldest_entry": _oldest(
            data["senders"]["vip"]
            + data["senders"]["noise"]
            + data["triage"]["overrides"]
            + data["corrections"],
            "first_seen",
        )
        or _oldest(
            data["triage"]["overrides"] + data["corrections"],
            "created",
        ),
        "updated_at": data.get("updated_at"),
    }

    warning = _file_size_warning(data)
    if warning:
        result.update(warning)
    _out(result)


if __name__ == "__main__":
    app()
