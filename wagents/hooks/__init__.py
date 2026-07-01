"""Shared hook rendering and merge core for cross-harness projection.

This package is the single source of truth for:

- ``merge``: hook stripping/merging helpers (``strip_generated_hook_entries``,
  ``merge_hook_groups``) shared by ``wagents.platforms.base`` and
  ``scripts.sync_agent_stack``.
- ``render``: logical-event maps and per-harness hook renderers consumed by the
  platform adapters and the APM materializer so every projection stays in sync.

Keeping these helpers here avoids the duplicate ``strip_generated_hook_entries``
implementations that previously drifted between ``base.py`` and the sync script,
and gives the Cursor adapter and APM materializer one flat-shape renderer.
"""

from __future__ import annotations

from wagents.hooks.merge import (
    HOOK_COMMAND_MARKERS,
    merge_cursor_flat_hooks,
    merge_hook_groups,
    strip_foreign_claude_hook_entries,
    strip_generated_hook_entries,
)
from wagents.hooks.render import (
    CURSOR_EVENT_MAP,
    enabled_hooks_for_harness,
    render_cursor_global_hooks,
    render_cursor_hooks,
    render_hook_command,
)

__all__ = [
    "CURSOR_EVENT_MAP",
    "HOOK_COMMAND_MARKERS",
    "enabled_hooks_for_harness",
    "merge_cursor_flat_hooks",
    "merge_hook_groups",
    "render_cursor_global_hooks",
    "render_cursor_hooks",
    "render_hook_command",
    "strip_foreign_claude_hook_entries",
    "strip_generated_hook_entries",
]
