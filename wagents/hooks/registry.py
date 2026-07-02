"""Cached hook registry loading and render fingerprint helpers."""

from __future__ import annotations

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from wagents.context import get_repo_root

if TYPE_CHECKING:
    from collections.abc import Callable

DEFAULT_HOOK_REGISTRY_PATH = get_repo_root() / "config" / "hook-registry.json"
SYNC_HOOK_HASH_PATH = Path.home() / ".cache" / "wagents" / "sync-hook-hash.json"

# Bumping this constant invalidates every recorded sync-skip cache entry even
# when the registry content and rendered destination are byte-identical to
# the last recorded render. Bump whenever the *rendering logic* itself
# changes (not just registry content) so a stale cache entry from before the
# logic change can never cause `sync_agent_stack.py --check`/`--apply` to
# skip a re-render that would now produce different output.
RENDER_FINGERPRINT_VERSION = 2


def _registry_cache_key(path: Path) -> tuple[str, int, int]:
    stat = path.stat()
    return (str(path.resolve()), stat.st_mtime_ns, stat.st_size)


@lru_cache(maxsize=4)
def _load_hook_registry_cached(cache_key: tuple[str, int, int]) -> dict[str, Any]:
    path = Path(cache_key[0])
    return json.loads(path.read_text(encoding="utf-8"))


def load_hook_registry(path: Path | None = None) -> dict[str, Any]:
    """Load ``config/hook-registry.json`` with an mtime+size keyed parse cache."""
    registry_path = path or DEFAULT_HOOK_REGISTRY_PATH
    if not registry_path.is_file():
        return {"version": 1, "hooks": []}
    return _load_hook_registry_cached(_registry_cache_key(registry_path))


def hook_registry_fingerprint(path: Path | None = None, *, extra: str = "") -> str:
    """Sha256 fingerprint for registry content plus optional render-input suffix."""
    registry_path = path or DEFAULT_HOOK_REGISTRY_PATH
    payload = registry_path.read_bytes()
    if extra:
        payload += extra.encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def hook_render_fingerprint(
    harness: str,
    *,
    perf_tier: str,
    registry_path: Path | None = None,
) -> str:
    """Sha256 fingerprint of every input that determines one harness's hook render.

    Combines the registry's content hash with ``harness``, ``perf_tier``, and
    ``RENDER_FINGERPRINT_VERSION`` so a cached skip decision is invalidated
    whenever any of those inputs change -- not just the raw registry bytes.
    """
    extra = f"|harness={harness}|perf_tier={perf_tier}|render_version={RENDER_FINGERPRINT_VERSION}"
    return hook_registry_fingerprint(registry_path, extra=extra)


def content_sha256(data: bytes) -> str:
    """Sha256 hex digest of on-disk rendered content (shared helper for callers)."""
    return hashlib.sha256(data).hexdigest()


def read_hook_render_fingerprints(*, cache_path: Path | None = None) -> dict[str, Any]:
    path = cache_path or SYNC_HOOK_HASH_PATH
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def record_hook_render_fingerprint(
    harness: str,
    fingerprint: str,
    *,
    content_sha256: str,
    cache_path: Path | None = None,
) -> None:
    """Record ``{registry_fp, content_sha256, render_version}`` for one harness.

    ``content_sha256`` must be the sha256 of the *actual on-disk destination
    file* immediately after a successful render+write, so a later
    ``should_skip_hook_render()`` call can detect a hand-edited or corrupted
    destination even when the registry fingerprint is unchanged (RV-004).
    """
    path = cache_path or SYNC_HOOK_HASH_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    data = read_hook_render_fingerprints(cache_path=path)
    data[harness] = {
        "registry_fp": fingerprint,
        "content_sha256": content_sha256,
        "render_version": RENDER_FINGERPRINT_VERSION,
    }
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def should_skip_hook_render(
    harness: str,
    fingerprint: str,
    dest_path: Path,
    *,
    cache_path: Path | None = None,
) -> bool:
    """True only when the registry fingerprint *and* the on-disk content hash both match.

    RV-004: the previous implementation skipped re-rendering based solely on
    the registry fingerprint, so a hand-edited or corrupted destination file
    would silently report "no drift" on `--check` as long as the registry
    itself had not changed. Requiring the destination's current content hash
    to also match the hash recorded at the last successful render closes that
    gap: any out-of-band edit to ``dest_path`` forces a fresh render.
    """
    recorded = read_hook_render_fingerprints(cache_path=cache_path).get(harness)
    if not isinstance(recorded, dict):
        return False
    if recorded.get("render_version") != RENDER_FINGERPRINT_VERSION:
        return False
    if recorded.get("registry_fp") != fingerprint:
        return False
    if not dest_path.is_file():
        return False
    try:
        on_disk_sha256 = content_sha256(dest_path.read_bytes())
    except OSError:
        return False
    return recorded.get("content_sha256") == on_disk_sha256


def sync_hook_projection(
    write_fn: Callable[[Path, Any], None],
    *,
    harness: str,
    dest_path: Path,
    render_fn: Callable[[], Any],
    perf_tier: str,
    apply: bool,
    cache_path: Path | None = None,
) -> bool:
    """Render + write one hook-only JSON projection through the RV-004 skip gate.

    Skips calling ``render_fn``/``write_fn`` entirely when
    :func:`should_skip_hook_render` confirms the registry fingerprint *and*
    the on-disk destination content both still match the last recorded
    render. Only meant for hook-only destination files that wagents fully
    owns (no interleaved non-hook managed keys); callers that merge hooks
    into a larger settings file alongside other managed keys should keep
    their existing full read-merge-write path instead.

    ``render_fn`` may return ``None`` to mean "nothing to render" (for
    example no hooks enabled for this harness); in that case nothing is
    written and no fingerprint is recorded.

    Returns ``True`` when the render was skipped, ``False`` when it ran.
    """
    fingerprint = hook_render_fingerprint(harness, perf_tier=perf_tier)
    if should_skip_hook_render(harness, fingerprint, dest_path, cache_path=cache_path):
        return True
    rendered = render_fn()
    if rendered is None:
        return False
    write_fn(dest_path, rendered)
    if apply and dest_path.is_file():
        record_hook_render_fingerprint(
            harness,
            fingerprint,
            content_sha256=content_sha256(dest_path.read_bytes()),
            cache_path=cache_path,
        )
    return False
