"""Registry perf metadata coverage for bundle groups and logical policies."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "config" / "hook-registry.json"


def _registry() -> dict[str, Any]:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _hooks() -> list[dict[str, Any]]:
    hooks = _registry().get("hooks", [])
    assert isinstance(hooks, list)
    return [hook for hook in hooks if isinstance(hook, dict)]


def test_every_hook_row_has_logical_policy():
    for hook in _hooks():
        assert hook.get("logical_policy"), f"missing logical_policy on {hook.get('id')}"


def test_bundle_groups_include_mode_and_are_contiguous():
    seen_groups: dict[str, list[int]] = {}
    for index, hook in enumerate(_hooks()):
        group = hook.get("bundle_group")
        if not group:
            continue
        assert hook.get("bundle_mode"), f"{hook['id']} missing bundle_mode"
        seen_groups.setdefault(str(group), []).append(index)

    for group, indexes in seen_groups.items():
        assert indexes == list(range(indexes[0], indexes[-1] + 1)), f"{group} rows are not contiguous"


def test_image_optimizer_matcher_is_not_catch_all():
    image = next(hook for hook in _hooks() if hook.get("id") == "image-input-optimizer-guard")
    assert image.get("matcher") != ".*"


def test_copilot_post_edit_rows_share_bundle_group():
    post_edit = [hook for hook in _hooks() if hook.get("id") in {"post-edit-format", "post-edit-lint"}]
    assert len(post_edit) == 2
    assert post_edit[0].get("bundle_group") == post_edit[1].get("bundle_group") == "copilot-post-edit-quality"
