import os
import shutil
import stat
import subprocess
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
OC = ROOT / "bin" / "oc"


def write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def require_jq() -> None:
    if shutil.which("jq") is None:
        pytest.skip("bin/oc requires jq")


def write_healthy_server_tools(tools: Path) -> None:
    write_executable(
        tools / "curl",
        r"""
        #!/usr/bin/env bash
        out=""
        while [ "$#" -gt 0 ]; do
          case "$1" in
            -o)
              out="$2"
              shift 2
              ;;
            -w|-u|--connect-timeout|--max-time|-H|--data|-X)
              shift 2
              ;;
            *)
              shift
              ;;
          esac
        done
        [ -n "$out" ] && printf '{"healthy":true}\n' >"$out"
        printf '200'
        """,
    )
    write_executable(
        tools / "route",
        """
        #!/usr/bin/env bash
        printf '   interface: en0\n'
        """,
    )
    write_executable(
        tools / "ipconfig",
        """
        #!/usr/bin/env bash
        printf '192.168.1.10\n'
        """,
    )
    write_executable(
        tools / "ifconfig",
        """
        #!/usr/bin/env bash
        cat <<'EOF'
        en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST>
            inet 192.168.1.10 netmask 0xffffff00 broadcast 192.168.1.255
        en1: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST>
            inet 192.168.1.11 netmask 0xffffff00 broadcast 192.168.1.255
        utun0: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST>
            inet 100.64.0.1 --> 100.64.0.1 netmask 0xffffffff
        EOF
        """,
    )
    write_executable(
        tools / "lsof",
        """
        #!/usr/bin/env bash
        if printf '%s\n' "$*" | grep -q -- '-Fp'; then
          printf 'p12345\n'
          exit 0
        fi
        cat <<'EOF'
        COMMAND   PID USER   FD   TYPE DEVICE SIZE/OFF NODE NAME
        opencode 123 ww     11u  IPv4 0      0t0      TCP *:4096 (LISTEN)
        EOF
        """,
    )


def base_env(tmp_path: Path, tools: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update({
        "OC_STATE_DIR": str(tmp_path / "state"),
        "OPENCODE_SERVER_USERNAME": "user",
        "OPENCODE_SERVER_PASSWORD": "secret",
        "OPENCODE_SERVER_URL": "http://127.0.0.1:4096",
        "PATH": f"{tools}:{env['PATH']}",
    })
    return env


def write_tailscale(
    tools: Path,
    *,
    calls_path: Path,
    online: bool = True,
    serve_ok: bool = True,
) -> Path:
    tailscale = tools / "tailscale"
    online_json = "true" if online else "false"
    backend = "Running" if online else "Stopped"
    serve_block = "exit 0" if serve_ok else "printf 'HTTPS/MagicDNS consent required\\n' >&2; exit 1"
    write_executable(
        tailscale,
        f"""
        #!/usr/bin/env bash
        printf '%s\\n' "$*" >>"{calls_path}"
        if [ "$1" = "status" ] && [ "${{2:-}}" = "--json" ]; then
          cat <<'JSON'
        {{
          "BackendState": "{backend}",
          "Self": {{
            "Online": {online_json},
            "HostName": "macbook",
            "DNSName": "macbook.tailnet.ts.net.",
            "TailscaleIPs": ["100.64.0.7", "fd7a:115c:a1e0::7"]
          }}
        }}
        JSON
          exit 0
        fi
        if [ "$1" = "serve" ]; then
          {serve_block}
        fi
        exit 2
        """,
    )
    return tailscale


def test_oc_wrapper_has_valid_bash_syntax() -> None:
    subprocess.run(["bash", "-n", str(OC)], check=True)


def test_status_no_start_renders_all_lan_urls(tmp_path: Path) -> None:
    tools = tmp_path / "tools"
    state = tmp_path / "state"
    tools.mkdir()

    write_executable(
        tools / "curl",
        r"""
        #!/usr/bin/env bash
        out=""
        while [ "$#" -gt 0 ]; do
          case "$1" in
            -o)
              out="$2"
              shift 2
              ;;
            -w|-u|--connect-timeout|--max-time|-H|--data|-X)
              shift 2
              ;;
            *)
              shift
              ;;
          esac
        done
        printf '{"healthy":true}\n' >"$out"
        printf '200'
        """,
    )
    write_executable(
        tools / "jq",
        r"""
        #!/usr/bin/env bash
        if [ "$1" = "-e" ]; then
          grep -q '"healthy":true' "$3"
          exit $?
        fi
        exit 2
        """,
    )
    write_executable(
        tools / "route",
        """
        #!/usr/bin/env bash
        printf '   interface: en0\n'
        """,
    )
    write_executable(
        tools / "ipconfig",
        """
        #!/usr/bin/env bash
        printf '192.168.1.10\n'
        """,
    )
    write_executable(
        tools / "ifconfig",
        """
        #!/usr/bin/env bash
        cat <<'EOF'
        en0: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST>
            inet 192.168.1.10 netmask 0xffffff00 broadcast 192.168.1.255
        en1: flags=8863<UP,BROADCAST,SMART,RUNNING,SIMPLEX,MULTICAST>
            inet 192.168.1.11 netmask 0xffffff00 broadcast 192.168.1.255
        utun0: flags=8051<UP,POINTOPOINT,RUNNING,MULTICAST>
            inet 10.0.0.1 --> 10.0.0.1 netmask 0xffffffff
        EOF
        """,
    )

    env = os.environ.copy()
    env.update({
        "OC_STATE_DIR": str(state),
        "OPENCODE_SERVER_USERNAME": "user",
        "OPENCODE_SERVER_PASSWORD": "secret",
        "OPENCODE_SERVER_URL": "http://127.0.0.1:4096",
        "PATH": f"{tools}:{env['PATH']}",
    })

    result = subprocess.run(
        [str(OC), "status", "--no-start"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert result.stdout == textwrap.dedent(
        """\
        OpenCode server: healthy
        Mac-only URL: http://127.0.0.1:4096
        iOS URL: http://192.168.1.10:4096
        Alternate iOS URL: http://192.168.1.11:4096
        mDNS URL: http://opencode.local:4096
        Username: user
        Password: run `oc ios credentials`

        Sessions: run oc sessions for recent local sessions.
        """
    )


def test_ios_status_reports_missing_tailscale_cli_without_blocking_lan(tmp_path: Path) -> None:
    require_jq()
    tools = tmp_path / "tools"
    tools.mkdir()
    write_healthy_server_tools(tools)
    env = base_env(tmp_path, tools)
    env["TAILSCALE_BIN"] = str(tmp_path / "missing-tailscale")

    result = subprocess.run(
        [str(OC), "ios", "status"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "OpenCode iOS/LAN/Tailscale server: healthy" in result.stdout
    assert "Tailscale: unavailable (CLI not found" in result.stdout
    assert "Tailscale Serve URL: unavailable" in result.stdout
    assert "OpenCode iOS URL: http://192.168.1.10:4096" in result.stdout
    assert "Password: run `oc ios credentials`" in result.stdout
    assert "secret" not in result.stdout


def test_ios_status_clears_stale_server_lock_without_owner(tmp_path: Path) -> None:
    require_jq()
    tools = tmp_path / "tools"
    state = tmp_path / "state"
    lock = state / "server.lock"
    tools.mkdir()
    lock.mkdir(parents=True)
    os.utime(lock, (1, 1))
    write_healthy_server_tools(tools)
    env = base_env(tmp_path, tools)
    env["TAILSCALE_BIN"] = str(tmp_path / "missing-tailscale")

    result = subprocess.run(
        [str(OC), "ios", "status"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "OpenCode iOS/LAN/Tailscale server: healthy" in result.stdout
    assert not lock.exists()


def test_ios_configures_tailscale_serve_and_prints_tailnet_urls(tmp_path: Path) -> None:
    require_jq()
    tools = tmp_path / "tools"
    calls = tmp_path / "tailscale-calls"
    tools.mkdir()
    write_healthy_server_tools(tools)
    tailscale = write_tailscale(tools, calls_path=calls)
    env = base_env(tmp_path, tools)
    env["TAILSCALE_BIN"] = str(tailscale)

    result = subprocess.run(
        [str(OC), "ios"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "Preferred away-from-home URL: https://macbook.tailnet.ts.net" in result.stdout
    assert "Tailnet fallback URL: http://100.64.0.7:4096" in result.stdout
    assert "OpenCode iOS URL: http://192.168.1.10:4096" in result.stdout
    assert "secret" not in result.stdout
    assert "serve --bg --https=443 http://127.0.0.1:4096" in calls.read_text()
    metadata = tmp_path / "state" / "tailscale-serve.json"
    assert metadata.exists()
    assert "secret" not in metadata.read_text()


def test_ios_serve_failure_keeps_raw_tailnet_fallback(tmp_path: Path) -> None:
    require_jq()
    tools = tmp_path / "tools"
    calls = tmp_path / "tailscale-calls"
    tools.mkdir()
    write_healthy_server_tools(tools)
    tailscale = write_tailscale(tools, calls_path=calls, serve_ok=False)
    env = base_env(tmp_path, tools)
    env["TAILSCALE_BIN"] = str(tailscale)

    result = subprocess.run(
        [str(OC), "ios"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "Preferred away-from-home URL" not in result.stdout
    assert "Tailscale Serve URL: not configured (run oc ios)" in result.stdout
    assert "Tailnet fallback URL: http://100.64.0.7:4096" in result.stdout
    assert "Tailscale Serve: setup needed or failed." in result.stderr
    assert "serve --bg --https=443 http://127.0.0.1:4096" in result.stderr
    assert not (tmp_path / "state" / "tailscale-serve.json").exists()


def test_ios_credentials_only_place_password_is_credentials_command(tmp_path: Path) -> None:
    require_jq()
    tools = tmp_path / "tools"
    calls = tmp_path / "tailscale-calls"
    tools.mkdir()
    write_healthy_server_tools(tools)
    tailscale = write_tailscale(tools, calls_path=calls)
    env = base_env(tmp_path, tools)
    env["TAILSCALE_BIN"] = str(tailscale)

    status = subprocess.run(
        [str(OC), "ios"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )
    credentials = subprocess.run(
        [str(OC), "ios", "credentials"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "secret" not in status.stdout
    assert "Server URL: https://macbook.tailnet.ts.net" in credentials.stdout
    assert "Password: secret" in credentials.stdout


def test_ios_stop_serve_only_uses_wrapper_metadata(tmp_path: Path) -> None:
    require_jq()
    tools = tmp_path / "tools"
    calls = tmp_path / "tailscale-calls"
    tools.mkdir()
    write_healthy_server_tools(tools)
    tailscale = write_tailscale(tools, calls_path=calls)
    env = base_env(tmp_path, tools)
    env["TAILSCALE_BIN"] = str(tailscale)

    subprocess.run([str(OC), "ios"], check=True, capture_output=True, env=env, text=True)
    result = subprocess.run(
        [str(OC), "ios", "stop-serve"],
        check=True,
        capture_output=True,
        env=env,
        text=True,
    )

    assert "stopped wrapper-owned Tailscale Serve mapping" in result.stdout
    assert "serve --https=443 http://127.0.0.1:4096 off" in calls.read_text()
    assert not (tmp_path / "state" / "tailscale-serve.json").exists()
