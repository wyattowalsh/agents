#!/usr/bin/env python3
"""Inventory Draw Things CLI, local rig, and recommended model pack status."""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MODELS_DIR = Path(
    os.environ.get(
        "DRAWTHINGS_MODELS_DIR",
        "~/Library/Containers/com.liuliu.draw-things/Data/Documents/Models",
    )
).expanduser()


@dataclass(frozen=True)
class RecommendedModel:
    model_id: str
    pack: str
    role: str
    reason: str

    @property
    def ensure_command(self) -> str:
        return f"draw-things-cli models ensure --model {self.model_id}"


RECOMMENDED_MODELS = [
    RecommendedModel(
        model_id="z_image_turbo_1.0_q8p.ckpt",
        pack="image",
        role="fast image default",
        reason="Fast current Z Image Turbo draft model for this 32 GiB Mac.",
    ),
    RecommendedModel(
        model_id="qwen_image_2512_q8p.ckpt",
        pack="image",
        role="best text layout realism",
        reason="Current Qwen Image model for typography, layout, and polished realism.",
    ),
    RecommendedModel(
        model_id="z_image_1.0_q8p.ckpt",
        pack="image",
        role="creative controllable base",
        reason="Current Z Image base model for broader creative control.",
    ),
    RecommendedModel(
        model_id="flux_2_dev_q6p.ckpt",
        pack="image",
        role="high-end FLUX reference edit",
        reason="FLUX.2 dev q6p balances capability and memory on 32 GiB unified memory.",
    ),
    RecommendedModel(
        model_id="qwen_image_edit_2511_q8p.ckpt",
        pack="image",
        role="instruction image edit",
        reason="Current Qwen edit model for img2img instruction editing.",
    ),
    RecommendedModel(
        model_id="hidream_i1_full_q5p.ckpt",
        pack="image",
        role="art prompt-following alternative",
        reason="HiDream I1 Full quality variant with q5p memory fit for this rig.",
    ),
    RecommendedModel(
        model_id="ltx_2.3_22b_distilled_q6p.ckpt",
        pack="media",
        role="fast local media",
        reason="Current LTX 2.3 distilled media model, q6p for 32 GiB memory safety.",
    ),
    RecommendedModel(
        model_id="wan_v2.2_5b_ti2v_q8p.ckpt",
        pack="media",
        role="rig-fit Wan media",
        reason="Current Wan 2.2 5B model; A14B variants are excluded for this rig.",
    ),
]

OPTIONAL_MODELS = [
    RecommendedModel(
        model_id="qwen_image_layered_1.0_bf16_q8p.ckpt",
        pack="image",
        role="optional layer decomposition editability",
        reason=(
            "Direct official Qwen Layered artifact; repeated CLI downloads stalled on this rig, "
            "so it is optional until install succeeds."
        ),
    ),
    RecommendedModel(
        model_id="qwen_image_layered_1.0_bf16_q6p.ckpt",
        pack="image",
        role="optional lower-precision Qwen Layered fallback",
        reason=(
            "Lower-precision Qwen Layered catalog entry; verify failed with a checksum mismatch, "
            "so do not require it in the best effective pack."
        ),
    ),
]

LEGACY_MODELS = {
    "flux_1_schnell_q8p.ckpt": "Superseded by z_image_turbo_1.0_q8p.ckpt for fast current still images.",
    "flux_1_fill_dev_q8p.ckpt": "Superseded by Qwen Edit 2511 and Qwen Layered for edit workflows.",
    "flux_2_klein_4b_q6p.ckpt": "Current but redundant fallback when flux_2_dev_q6p.ckpt is available on this rig.",
}

STALE_PARTIALS = {
    "llama_3.1_8b_instruct_q8p.ckpt": (
        "Incomplete stale auxiliary text-model artifact; not a current Draw Things generation/media "
        "recommendation for mid-May 2026."
    ),
}


def run_command(args: list[str], timeout: int = 30) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            args,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError:
        return 127, "", f"command not found: {args[0]}"
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return 124, stdout, stderr or f"timed out after {timeout}s"

    return completed.returncode, completed.stdout, completed.stderr


def machine_value(command: list[str]) -> str | None:
    code, stdout, _stderr = run_command(command, timeout=10)
    if code != 0:
        return None
    return stdout.strip() or None


def detect_rig() -> dict[str, Any]:
    memsize_raw = machine_value(["sysctl", "-n", "hw.memsize"])
    mem_gib = None
    if memsize_raw and memsize_raw.isdigit():
        mem_gib = round(int(memsize_raw) / (1024**3), 1)

    return {
        "date_utc": machine_value(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]),
        "machine": platform.machine(),
        "macos_version": machine_value(["sw_vers", "-productVersion"]),
        "macos_build": machine_value(["sw_vers", "-buildVersion"]),
        "cpu": machine_value(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "memory_gib": mem_gib,
    }


def parse_downloaded_models(stdout: str) -> list[str]:
    models: list[str] = []
    for line in stdout.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("Models directory:"):
            continue
        first_column = stripped.split()[0]
        if first_column.endswith((".ckpt", ".safetensors")):
            models.append(first_column)
    return sorted(set(models))


def local_file_models(models_dir: Path) -> list[str]:
    if not models_dir.is_dir():
        return []
    suffixes = {".ckpt", ".safetensors"}
    return sorted(path.name for path in models_dir.iterdir() if path.suffix in suffixes)


def local_partial_files(models_dir: Path) -> list[str]:
    if not models_dir.is_dir():
        return []
    return sorted(path.name for path in models_dir.iterdir() if path.name.endswith((".ckpt.part", ".safetensors.part")))


def downloaded_models(cli_path: str | None, models_dir: Path) -> tuple[list[str], dict[str, Any]]:
    if not cli_path:
        return local_file_models(models_dir), {"source": "filesystem", "error": "draw-things-cli not found"}

    code, stdout, stderr = run_command([cli_path, "models", "list", "--downloaded-only"], timeout=60)
    if code == 0:
        return parse_downloaded_models(stdout), {"source": "draw-things-cli"}

    return local_file_models(models_dir), {
        "source": "filesystem",
        "error": stderr.strip() or f"models list failed with code {code}",
    }


def selected_recommendations(pack: str) -> list[RecommendedModel]:
    if pack == "all":
        return RECOMMENDED_MODELS
    return [model for model in RECOMMENDED_MODELS if model.pack == pack]


def incomplete_downloads(
    partials: list[str],
    recommendations: list[RecommendedModel],
    optional_models: list[RecommendedModel],
) -> list[dict[str, Any]]:
    recommended_by_id = {model.model_id: model for model in recommendations}
    optional_by_id = {model.model_id: model for model in optional_models}
    items: list[dict[str, Any]] = []

    for partial in partials:
        model_id = partial.removesuffix(".part")
        recommended = recommended_by_id.get(model_id)
        if recommended:
            items.append(
                {
                    "file": partial,
                    "model_id": model_id,
                    "recommended": True,
                    "status": "interrupted_recommended_download",
                    "reason": recommended.reason,
                    "action": recommended.ensure_command,
                }
            )
            continue

        optional = optional_by_id.get(model_id)
        if optional:
            items.append(
                {
                    "file": partial,
                    "model_id": model_id,
                    "recommended": False,
                    "status": "interrupted_optional_download",
                    "reason": optional.reason,
                    "action": (
                        "Retry only if the user explicitly wants Qwen Layered despite prior install failures; "
                        "prune only after separate approval."
                    ),
                }
            )
            continue

        items.append(
            {
                "file": partial,
                "model_id": model_id,
                "recommended": False,
                "status": "stale_or_unclassified_partial" if model_id in STALE_PARTIALS else "unclassified_partial",
                "reason": STALE_PARTIALS.get(
                    model_id,
                    "Incomplete partial file is not in the current recommended pack; do not treat it as installed.",
                ),
                "action": (
                    "Do not resume unless the user explicitly asks for this model; prune only after separate "
                    "approval."
                ),
            }
        )

    return items


def auxiliary_or_dependency_files(
    local_models: list[str],
    downloaded: list[str],
    recommendations: list[RecommendedModel],
    optional_models: list[RecommendedModel],
) -> list[dict[str, Any]]:
    downloaded_set = set(downloaded)
    recommended_set = {model.model_id for model in recommendations}
    optional_set = {model.model_id for model in optional_models}
    legacy_set = set(LEGACY_MODELS)

    auxiliary = []
    for model_id in local_models:
        if (
            model_id in downloaded_set
            or model_id in recommended_set
            or model_id in optional_set
            or model_id in legacy_set
        ):
            continue
        auxiliary.append(
            {
                "model_id": model_id,
                "reason": (
                    "Local helper, dependency, or manually imported file; not part of the current best "
                    "generation/media pack."
                ),
            }
        )
    return auxiliary


def build_inventory(pack: str) -> dict[str, Any]:
    cli_path = shutil.which("draw-things-cli")
    models, source = downloaded_models(cli_path, MODELS_DIR)
    local_models = local_file_models(MODELS_DIR)
    partials = local_partial_files(MODELS_DIR)
    model_set = set(models) | set(local_models)
    cli_model_set = set(models)
    local_model_set = set(local_models)
    recommendations = selected_recommendations(pack)
    optional_models = [model for model in OPTIONAL_MODELS if pack in {"all", model.pack}]

    recommended_status = [
        {
            "model_id": model.model_id,
            "pack": model.pack,
            "role": model.role,
            "installed": model.model_id in model_set,
            "installed_source": "draw-things-cli"
            if model.model_id in cli_model_set
            else "filesystem"
            if model.model_id in local_model_set
            else None,
            "ensure_command": model.ensure_command,
            "reason": model.reason,
        }
        for model in recommendations
    ]

    missing = [item for item in recommended_status if not item["installed"]]
    optional_status = [
        {
            "model_id": model.model_id,
            "pack": model.pack,
            "role": model.role,
            "installed": model.model_id in model_set,
            "installed_source": "draw-things-cli"
            if model.model_id in cli_model_set
            else "filesystem"
            if model.model_id in local_model_set
            else None,
            "ensure_command": model.ensure_command,
            "reason": model.reason,
        }
        for model in optional_models
    ]
    installed_legacy = [
        {"model_id": model_id, "reason": reason, "prune_requires_approval": True}
        for model_id, reason in LEGACY_MODELS.items()
        if model_id in model_set
    ]

    return {
        "status": "installed" if cli_path else "not_installed",
        "cli_path": cli_path,
        "install_command": "brew install drawthingsai/draw-things/draw-things-cli" if not cli_path else None,
        "models_dir": str(MODELS_DIR),
        "rig": detect_rig(),
        "recommended_pack": pack,
        "downloaded_models_source": source,
        "downloaded_models": models,
        "local_model_files": local_models,
        "recommended_models": recommended_status,
        "missing_recommended_models": missing,
        "ensure_commands": [item["ensure_command"] for item in missing],
        "optional_models": optional_status,
        "legacy_or_redundant_downloads": installed_legacy,
        "incomplete_downloads": incomplete_downloads(partials, recommendations, optional_models),
        "auxiliary_or_dependency_files": auxiliary_or_dependency_files(
            local_models, models, recommendations, optional_models
        ),
        "notes": [
            "Do not prune legacy models without explicit approval.",
            "Do not treat auxiliary text/VLM files or .part files as recommended generation models.",
            "Qwen Layered is optional on this rig because both q6p and q8p installs failed or stalled repeatedly.",
            "Use draw-things-cli generate --help as the direct-flag source of truth.",
            "Always pass --output for durable files.",
        ],
    }


def render_text(inventory: dict[str, Any]) -> str:
    lines = [
        f"status: {inventory['status']}",
        f"cli_path: {inventory['cli_path']}",
        f"models_dir: {inventory['models_dir']}",
        f"recommended_pack: {inventory['recommended_pack']}",
        "missing_recommended_models:",
    ]
    if inventory["missing_recommended_models"]:
        for item in inventory["missing_recommended_models"]:
            lines.append(f"  - {item['model_id']} ({item['role']})")
            lines.append(f"    {item['ensure_command']}")
    else:
        lines.append("  - none")

    lines.append("optional_models:")
    if inventory["optional_models"]:
        for item in inventory["optional_models"]:
            status = "installed" if item["installed"] else "not installed"
            lines.append(f"  - {item['model_id']} ({status}): {item['reason']}")
    else:
        lines.append("  - none")

    lines.append("legacy_or_redundant_downloads:")
    if inventory["legacy_or_redundant_downloads"]:
        for item in inventory["legacy_or_redundant_downloads"]:
            lines.append(f"  - {item['model_id']}: {item['reason']}")
    else:
        lines.append("  - none")

    lines.append("incomplete_downloads:")
    if inventory["incomplete_downloads"]:
        for item in inventory["incomplete_downloads"]:
            lines.append(f"  - {item['file']}: {item['reason']}")
    else:
        lines.append("  - none")

    return "\n".join(lines)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--recommended-pack",
        choices=["image", "media", "all"],
        default="all",
        help="Recommended pack to report.",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Output format. JSON is intended for agents.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    inventory = build_inventory(args.recommended_pack)

    if args.format == "json":
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(render_text(inventory))

    return 0 if inventory["status"] == "installed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
