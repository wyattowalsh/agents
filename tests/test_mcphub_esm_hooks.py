"""Negative proof that MCPHub no longer relies on Node preload hooks."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "mcphub"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_all_preload_and_bind_hook_files_are_retired() -> None:
    for name in (
        "bind-loopback.cjs",
        "mcphub-esm-hooks.mjs",
        "mcphub-esm-loader.mjs",
    ):
        assert not (SCRIPTS / name).exists()


def test_runtime_launch_surfaces_do_not_install_preloads_or_loaders() -> None:
    paths = (
        SCRIPTS / "common.sh",
        SCRIPTS / "start-server.sh",
        SCRIPTS / "launch-agent-run.sh",
        ROOT / "config" / "launchd" / "com.wyattowalsh.mcphub.plist",
        ROOT / ".env.mcphub.example",
    )
    forbidden = re.compile(
        r"(?:^|\s)(?:export\s+)?NODE_OPTIONS=|"
        r"--(?:experimental-)?loader(?:=|\s)|"
        r"--import(?:=|\s)|--require(?:=|\s)|"
        r"mcphub-esm-(?:hooks|loader)|bind-loopback",
        re.MULTILINE,
    )
    for path in paths:
        assert forbidden.search(_read(path)) is None, path


def test_sealed_entry_and_provider_use_static_imports_only() -> None:
    runtime = ROOT / "mcp" / "mcphub" / "downstream" / "src" / "runtime"
    main = _read(runtime / "main.ts")
    provider = _read(runtime / "provider.ts")
    assert "export async function main" in main
    assert '@samanhappy/mcphub/dist/server.js"' in main
    assert '@samanhappy/mcphub/dist/services/mcpService.js"' in provider
    assert '@samanhappy/mcphub/dist/services/sseService.js"' in provider
    assert "import(" not in main
    assert "import(" not in provider
    assert "dist/index.js" not in main + provider
