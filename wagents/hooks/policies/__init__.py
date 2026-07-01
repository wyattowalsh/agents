"""Decoupled hook-policy decision functions.

These modules hold the *pure* decision logic for repo-managed hook policies so
that both the standalone dispatcher (``hooks/wagents-hook.py``) and unit tests
can import them without pulling in the dispatcher's runtime helpers.

Design contract:

- Every function here takes **primitive inputs** (``str``/``dict``/``list``)
  extracted by the dispatcher from its ``NormalizedPayload`` — never the payload
  object itself. This keeps policies free of dispatcher coupling and trivially
  unit-testable.
- Decision functions return ``str | None``: a non-empty reason string means
  *deny/block*; ``None`` means *allow*.
- Modules import only the Python standard library.
"""

from __future__ import annotations

from wagents.hooks.policies.before_mcp_execution import evaluate_before_mcp_execution
from wagents.hooks.policies.before_read_file_guard import evaluate_before_read_file
from wagents.hooks.policies.git_commit_push_guard import evaluate_git_commit_push
from wagents.hooks.policies.grok_deny_adapter import grok_deny_payload
from wagents.hooks.policies.stop_quality_gate import quality_gate_command
from wagents.hooks.policies.stop_wagents_validate import validate_asset_paths
from wagents.hooks.policies.subagent_start import subagent_start_context

__all__ = [
    "evaluate_before_mcp_execution",
    "evaluate_before_read_file",
    "evaluate_git_commit_push",
    "grok_deny_payload",
    "quality_gate_command",
    "subagent_start_context",
    "validate_asset_paths",
]
