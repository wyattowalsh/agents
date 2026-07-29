from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MCPHUB_SCRIPTS = ROOT / "scripts" / "mcphub"


def test_clean_environment_helper_forwards_only_allowlisted_values(tmp_path: Path) -> None:
    command = (
        f"source {MCPHUB_SCRIPTS / 'common.sh'}; "
        "ALLOWED_VALUE=present DO_NOT_LEAK=secret OPENAI_API_KEY=secret "
        "mcphub_run_clean ALLOWED_VALUE -- /usr/bin/env"
    )

    result = subprocess.run(
        ["/bin/bash", "-c", command],
        check=True,
        text=True,
        capture_output=True,
        env={"HOME": str(tmp_path), "PATH": "/usr/bin:/bin", "LANG": "C"},
    )

    names = {line.split("=", 1)[0] for line in result.stdout.splitlines() if "=" in line}
    assert "ALLOWED_VALUE" in names
    assert "DO_NOT_LEAK" not in names
    assert "OPENAI_API_KEY" not in names


def test_remote_stdio_keeps_bearer_value_out_of_argv_and_drops_unrelated_env(tmp_path: Path) -> None:
    fake_npx = tmp_path / "npx"
    fake_npx.write_text(
        """#!/usr/bin/env bash
printf 'argv='
printf '%q ' "$@"
printf '\\n'
printf 'token_present=%s\\n' "$([[ -n "${MCPHUB_BEARER_TOKEN:-}" ]] && printf yes || printf no)"
printf 'unrelated_present=%s\\n' "$([[ -n "${DO_NOT_LEAK:-}${OPENAI_API_KEY:-}" ]] && printf yes || printf no)"
""",
        encoding="utf-8",
    )
    fake_npx.chmod(0o755)
    command = (
        f"source {shlex.quote(str(MCPHUB_SCRIPTS / 'common.sh'))}; "
        "export MCPHUB_BEARER_TOKEN=dummy-bearer-value DO_NOT_LEAK=secret OPENAI_API_KEY=secret; "
        f"mcphub_exec_clean MCPHUB_BEARER_TOKEN -- {shlex.quote(str(fake_npx))} "
        "-y mcp-remote@0.1.38 http://127.0.0.1:46683/mcp/harness "
        "--allow-http --transport http-only --silent "
        "--header 'Authorization:Bearer ${MCPHUB_BEARER_TOKEN}'"
    )

    result = subprocess.run(
        ["/bin/bash", "-c", command],
        check=True,
        text=True,
        capture_output=True,
        timeout=10,
        env={
            "HOME": str(tmp_path),
            "PATH": "/usr/bin:/bin",
            "LANG": "C",
        },
    )

    wrapper = (MCPHUB_SCRIPTS / "remote-stdio.sh").read_text(encoding="utf-8")
    assert "mcp-remote@0.1.38" in wrapper
    assert "'Authorization:Bearer ${MCPHUB_BEARER_TOKEN}'" in wrapper
    assert "dummy-bearer-value" not in result.stdout
    assert "MCPHUB_BEARER_TOKEN" in result.stdout
    assert "token_present=yes" in result.stdout
    assert "unrelated_present=no" in result.stdout
    assert "mcp-remote@0.1.38" in result.stdout
