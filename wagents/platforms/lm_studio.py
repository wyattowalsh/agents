"""LM Studio adapter: MCP, instruction/agent presets, and optional skills mirror.

Compatible surfaces projected into the resolved LM Studio home:

- **MCP** — Cursor-compatible ``mcp.json`` (MCPHub remote-stdio by default)
- **Instructions** — managed config preset ``wagents-repo.preset.json``
- **Agents** — managed ``wagents-agent-<name>.preset.json`` from ``agents/*.md``
- **Skills** — optional symlinks under ``{home}/skills/<name>/`` (default: none)

Unsupported: hooks, native Skills CLI agent id, app-only UI state.

Home resolution:

1. ``~/.lmstudio-home-pointer`` (existing dir)
2. ``~/.lmstudio``
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from wagents.context import get_repo_root
from wagents.parsing import parse_frontmatter
from wagents.platforms.base import (
    HOME,
    PlatformAdapter,
    SyncContext,
    dump_json,
    enabled_registry_servers,
    load_json,
    managed_registry_server_names,
    mcphub_bearer_env_var,
    mcphub_enabled,
    mcphub_endpoint_specs,
    mcphub_projection_mode,
    merge_server_maps,
    render_env_value,
    render_mcphub_stdio_server,
    replace_arg_placeholders,
)

LM_STUDIO_HOME_POINTER = HOME / ".lmstudio-home-pointer"
LM_STUDIO_DEFAULT_HOME = HOME / ".lmstudio"

MANAGED_PRESET_PREFIX = "wagents-"
INSTRUCTION_PRESET_FILENAME = "wagents-repo.preset.json"
AGENT_PRESET_PREFIX = "wagents-agent-"
INSTRUCTION_PRESET_CHAR_BUDGET = 14_000
AGENT_PRESET_CHAR_BUDGET = 10_000
MANAGED_PRESET_MARKER = "Managed by wagents. Do not edit; regenerated on sync."

# Opt-in skill mirror. Default none avoids flooding LMS home with the full skills tree.
SKILL_MIRROR_ENV = "WAGENTS_LM_STUDIO_SKILLS"
SkillMirrorMode = Literal["none", "allowlist", "all"]


@dataclass(frozen=True)
class SkillMirrorConfig:
    """Skill symlink policy for LM Studio home sync."""

    mode: SkillMirrorMode = "none"
    allowlist: frozenset[str] = frozenset()


def resolve_skill_mirror_config(
    env: dict[str, str] | None = None,
) -> SkillMirrorConfig:
    """Parse ``WAGENTS_LM_STUDIO_SKILLS`` into a skill mirror config.

    | Raw value | Result |
    | --- | --- |
    | unset / empty | mode=none |
    | none | mode=none |
    | all | mode=all |
    | allowlist:a,b,c | mode=allowlist |
    | a,b,c | mode=allowlist |
    | invalid keyword-only | mode=none (fail-closed) |
    """
    source = env if env is not None else os.environ
    raw = str(source.get(SKILL_MIRROR_ENV, "")).strip()
    if not raw:
        return SkillMirrorConfig(mode="none")

    lowered = raw.casefold()
    if lowered == "none":
        return SkillMirrorConfig(mode="none")
    if lowered == "all":
        return SkillMirrorConfig(mode="all")

    if lowered.startswith("allowlist:"):
        names_part = raw.split(":", 1)[1]
    elif "," in raw:
        names_part = raw
    else:
        # Single unknown token (not none/all) — fail closed.
        return SkillMirrorConfig(mode="none")

    names = frozenset(part.strip() for part in names_part.split(",") if part.strip())
    if not names:
        return SkillMirrorConfig(mode="none")
    return SkillMirrorConfig(mode="allowlist", allowlist=names)


def select_skill_dirs(skill_dirs: list[Path], cfg: SkillMirrorConfig) -> list[Path]:
    """Filter portable skill directories according to mirror config."""
    if cfg.mode == "none":
        return []
    if cfg.mode == "all":
        return list(skill_dirs)
    return [path for path in skill_dirs if path.name in cfg.allowlist]


def resolve_lm_studio_home() -> Path | None:
    """Return the LM Studio user-data root, or None if not installed/detectable."""
    if LM_STUDIO_HOME_POINTER.is_file():
        raw = LM_STUDIO_HOME_POINTER.read_text(encoding="utf-8").strip()
        if raw:
            candidate = Path(raw).expanduser()
            if candidate.is_dir():
                return candidate
    if LM_STUDIO_DEFAULT_HOME.is_dir():
        return LM_STUDIO_DEFAULT_HOME
    return None


def lm_studio_mcp_path(home: Path | None = None) -> Path | None:
    root = home if home is not None else resolve_lm_studio_home()
    if root is None:
        return None
    return root / "mcp.json"


def config_presets_dir(home: Path) -> Path:
    return home / "config-presets"


def skills_dir(home: Path) -> Path:
    return home / "skills"


def _read_text_if_exists(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _truncate(text: str, budget: int) -> str:
    text = text.strip()
    if len(text) <= budget:
        return text
    return text[: max(0, budget - 80)].rstrip() + "\n\n…[truncated for local-model context budget]"


def _strip_import_lines(markdown: str) -> str:
    """Drop @./relative imports used by bridge files; keep body prose."""
    lines: list[str] = []
    for line in markdown.splitlines():
        if re.match(r"^@\./", line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def render_instruction_preset_body(
    *,
    overlay: str,
    global_md: str,
    agents_index: str,
) -> str:
    parts = [
        MANAGED_PRESET_MARKER,
        "",
        "# Repo instructions (LM Studio preset)",
        "",
        "Repo policy source: local agents repository checkout (path not embedded).",
        "Full policy lives in the clone; this preset is a compact projection for local models.",
        "",
        "## LM Studio overlay",
        "",
        _strip_import_lines(overlay) or "(missing instructions/lm-studio-global.md)",
        "",
        "## Shared global policy (excerpt)",
        "",
        _truncate(_strip_import_lines(global_md), INSTRUCTION_PRESET_CHAR_BUDGET // 2),
        "",
        "## Portable agents available as presets",
        "",
        agents_index or "(no agents)",
        "",
        "## Skills",
        "",
        "Skill symlink mirror defaults to **none** (MCP + presets only).",
        f"Set `{SKILL_MIRROR_ENV}=all` or `allowlist:name1,name2` before home sync to populate "
        "`{lmstudio-home}/skills/` for a skills-capable plugin. "
        "Skills CLI has no native lm-studio agent.",
    ]
    return _truncate("\n".join(parts), INSTRUCTION_PRESET_CHAR_BUDGET)


def render_preset(name: str, pre_prompt: str, *, description: str = "") -> dict[str, Any]:
    """Render an LM Studio config-preset JSON object (community-compatible shape)."""
    return {
        "name": name,
        "description": description or MANAGED_PRESET_MARKER,
        "inference_params": {
            "pre_prompt": pre_prompt,
            "pre_prompt_prefix": "",
            "pre_prompt_suffix": "\n",
        },
        "load_params": {},
        "wagents": {
            "managed": True,
            "marker": MANAGED_PRESET_MARKER,
        },
    }


def portable_agent_files(repo_root: Path | None = None) -> list[Path]:
    root = repo_root or get_repo_root()
    agents_dir = root / "agents"
    if not agents_dir.is_dir():
        return []
    return sorted(path for path in agents_dir.glob("*.md") if path.name != "README.md")


def portable_skill_dirs(repo_root: Path | None = None) -> list[Path]:
    root = repo_root or get_repo_root()
    skills_root = root / "skills"
    if not skills_root.is_dir():
        return []
    return sorted(path for path in skills_root.iterdir() if path.is_dir() and (path / "SKILL.md").is_file())


def render_agent_preset(path: Path) -> tuple[str, dict[str, Any]]:
    frontmatter, body = parse_frontmatter(path.read_text(encoding="utf-8"))
    name = str(frontmatter.get("name") or path.stem)
    description = str(frontmatter.get("description") or "")
    pre_prompt = _truncate(
        "\n".join([
            MANAGED_PRESET_MARKER,
            "",
            f"# Agent: {name}",
            "",
            description,
            "",
            body.strip(),
        ]),
        AGENT_PRESET_CHAR_BUDGET,
    )
    filename = f"{AGENT_PRESET_PREFIX}{name}.preset.json"
    preset = render_preset(
        name=f"wagents/{name}",
        pre_prompt=pre_prompt,
        description=description[:200] if description else MANAGED_PRESET_MARKER,
    )
    return filename, preset


def render_all_agent_presets(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    files: dict[str, dict[str, Any]] = {}
    for path in portable_agent_files(repo_root):
        filename, preset = render_agent_preset(path)
        files[filename] = preset
    return files


def render_instruction_preset(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or get_repo_root()
    overlay = _read_text_if_exists(root / "instructions" / "lm-studio-global.md")
    global_md = _read_text_if_exists(root / "instructions" / "global.md")
    agent_lines: list[str] = []
    for path in portable_agent_files(root):
        frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        name = str(frontmatter.get("name") or path.stem)
        desc = str(frontmatter.get("description") or "").strip()
        agent_lines.append(f"- `{name}` — {desc}" if desc else f"- `{name}`")
    body = render_instruction_preset_body(
        overlay=overlay,
        global_md=global_md,
        agents_index="\n".join(agent_lines),
    )
    return render_preset(
        name="wagents/repo-instructions",
        pre_prompt=body,
        description="Repo-managed LM Studio instruction pack (global + overlay).",
    )


def _is_managed_preset_filename(name: str) -> bool:
    return name.startswith(MANAGED_PRESET_PREFIX) and name.endswith(".preset.json")


def sync_presets(ctx: SyncContext, home: Path, *, repo_root: Path | None = None) -> None:
    root = repo_root or get_repo_root()
    presets = config_presets_dir(home)
    if ctx.apply:
        presets.mkdir(parents=True, exist_ok=True)

    desired: dict[str, dict[str, Any]] = {
        INSTRUCTION_PRESET_FILENAME: render_instruction_preset(root),
        **render_all_agent_presets(root),
    }

    for filename, payload in sorted(desired.items()):
        dest = presets / filename
        content = dump_json(payload)
        current = dest.read_text(encoding="utf-8") if dest.is_file() else None
        if current == content:
            continue
        ctx.note(f"update {dest}")
        if ctx.apply:
            dest.write_text(content, encoding="utf-8")

    if not presets.is_dir():
        return
    for existing in sorted(presets.iterdir()):
        if not existing.is_file() or not _is_managed_preset_filename(existing.name):
            continue
        if existing.name in desired:
            continue
        ctx.note(f"remove stale managed preset {existing}")
        if ctx.apply:
            existing.unlink()


def _is_managed_repo_skill_symlink(entry: Path, skills_root: Path) -> bool:
    """True when entry is a symlink whose target lives under the repo skills tree."""
    if not entry.is_symlink():
        return False
    try:
        target = entry.resolve()
    except OSError:
        return False
    try:
        return target.is_relative_to(skills_root)
    except (OSError, ValueError, AttributeError):
        return False


def sync_skills(
    ctx: SyncContext,
    home: Path,
    *,
    repo_root: Path | None = None,
    cfg: SkillMirrorConfig | None = None,
) -> None:
    root = repo_root or get_repo_root()
    policy = cfg if cfg is not None else resolve_skill_mirror_config()
    target_root = skills_dir(home)
    skill_dirs = select_skill_dirs(portable_skill_dirs(root), policy)
    expected = {skill.name for skill in skill_dirs}
    skills_root = (root / "skills").resolve()

    if policy.mode == "none" and not expected and not target_root.is_dir():
        # Nothing to create and no prior tree to purge.
        return

    if ctx.apply and (skill_dirs or target_root.is_dir()):
        target_root.mkdir(parents=True, exist_ok=True)

    for skill_dir in skill_dirs:
        destination = target_root / skill_dir.name
        try:
            if destination.is_symlink() and destination.resolve() == skill_dir.resolve():
                continue
        except OSError:
            pass
        if destination.exists() and not destination.is_symlink():
            # Do not clobber a real user directory.
            ctx.note(f"skip skill {destination} (exists and is not a symlink)")
            continue
        ctx.note(f"symlink {skill_dir} -> {destination}")
        if ctx.apply:
            if destination.is_symlink() or destination.exists():
                destination.unlink()
            destination.symlink_to(skill_dir)

    if not target_root.is_dir():
        return
    for entry in sorted(target_root.iterdir()):
        if entry.name in expected:
            continue
        if not entry.is_symlink():
            continue
        if not _is_managed_repo_skill_symlink(entry, skills_root):
            continue
        ctx.note(f"remove stale skill symlink {entry}")
        if ctx.apply:
            entry.unlink()


class Adapter(PlatformAdapter):
    name = "lm-studio"

    def is_available(self) -> bool:
        return resolve_lm_studio_home() is not None

    def home_config_paths(self) -> list[Path]:
        home = resolve_lm_studio_home()
        if home is None:
            base = LM_STUDIO_DEFAULT_HOME
            return [base / "mcp.json", base / "config-presets", base / "skills"]
        return [home / "mcp.json", config_presets_dir(home), skills_dir(home)]

    def repo_config_paths(self) -> list[Path]:
        return [get_repo_root() / "instructions" / "lm-studio-global.md"]

    def sync_repo(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        hook_registry: dict[str, Any],
        policy: dict[str, Any],
    ) -> None:
        # Instruction overlay is hand-authored under instructions/; no generated repo MCP.
        return

    def sync_home(
        self,
        ctx: SyncContext,
        registry: dict[str, Any],
        policy: dict[str, Any],
        fallbacks: dict[str, str],
        hook_registry: dict[str, Any],
    ) -> None:
        home = resolve_lm_studio_home()
        if home is None:
            return
        self._sync_mcp(ctx, home, registry, fallbacks)
        sync_presets(ctx, home)
        sync_skills(ctx, home)

    def _sync_mcp(
        self,
        ctx: SyncContext,
        home: Path,
        registry: dict[str, Any],
        fallbacks: dict[str, str],
    ) -> None:
        path = home / "mcp.json"
        rendered = self.render_mcp(registry, fallbacks)["mcpServers"]
        known = managed_registry_server_names(registry, self.name)

        if path.exists():
            data = load_json(path)
            existing = data.get("mcpServers")
            data["mcpServers"] = merge_server_maps(
                rendered,
                existing if isinstance(existing, dict) else {},
                known,
            )
        else:
            data = {"mcpServers": rendered}

        ctx.write_json(path, data)

    def render_mcp(
        self,
        registry: dict[str, Any],
        fallbacks: dict[str, str],
        harness: str | None = None,
    ) -> dict[str, Any]:
        target = harness or self.name
        if mcphub_enabled(registry):
            mode = mcphub_projection_mode(registry, target, "remote-stdio")
            token_env = mcphub_bearer_env_var(registry)
            servers: dict[str, Any] = {}
            for spec in mcphub_endpoint_specs(registry, target):
                if not spec.get("enabled"):
                    continue
                name = str(spec["name"])
                if mode == "http":
                    servers[name] = {
                        "url": spec["url"],
                        "headers": {"Authorization": f"Bearer ${{{token_env}}}"},
                    }
                else:
                    entry = render_mcphub_stdio_server(
                        registry,
                        str(spec["url"]),
                        fallbacks,
                        bool(spec["enabled"]),
                        local_values=False,
                    )
                    entry["command"] = str((get_repo_root() / "scripts" / "mcphub" / "remote-stdio.sh").resolve())
                    servers[name] = entry
            return {"mcpServers": servers}

        servers: dict[str, Any] = {}
        for name, entry in enabled_registry_servers(registry, target).items():
            transport = str(entry.get("transport", "stdio"))
            if transport in {"streamable-http", "http", "sse"} and entry.get("url"):
                server: dict[str, Any] = {"url": str(entry["url"])}
                headers = entry.get("headers")
                if isinstance(headers, dict):
                    server["headers"] = {str(k): str(v) for k, v in headers.items()}
            else:
                server = {
                    "command": entry["command"],
                    "args": replace_arg_placeholders(entry.get("args", []), fallbacks, local_values=False),
                }
                if entry.get("env"):
                    server["env"] = {
                        key: render_env_value(value, fallbacks, local_values=False)
                        for key, value in entry["env"].items()
                    }
            servers[name] = server
        return {"mcpServers": servers}
