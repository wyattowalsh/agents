"""Tests for wagents hooks CLI commands."""

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from wagents.cli import app
from wagents.parsing import KNOWN_HOOK_EVENTS, extract_hooks

REAL_REPO_ROOT = Path(__file__).resolve().parents[1]

_VERIFY_PATH = Path(__file__).parent.parent / "skills" / "skill-creator" / "scripts" / "verify.py"
_VERIFY_SPEC = importlib.util.spec_from_file_location("skill_creator_verify", _VERIFY_PATH)
assert _VERIFY_SPEC
assert _VERIFY_SPEC.loader
skill_creator_verify = importlib.util.module_from_spec(_VERIFY_SPEC)
_VERIFY_SPEC.loader.exec_module(skill_creator_verify)

runner = CliRunner()


@pytest.fixture
def patched_repo(tmp_path, monkeypatch):
    """Create a minimal repo skeleton in tmp_path and monkeypatch all ROOT refs."""
    for mod in ["wagents", "wagents.cli", "wagents.catalog", "wagents.rendering"]:
        monkeypatch.setattr(f"{mod}.ROOT", tmp_path)
    monkeypatch.setattr("wagents.rendering.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.DOCS_DIR", tmp_path / "docs")
    monkeypatch.setattr("wagents.docs.ROOT", tmp_path)
    monkeypatch.setattr("wagents.docs.CONTENT_DIR", tmp_path / "docs/src/content/docs")
    monkeypatch.setattr("wagents.docs.DOCS_DIR", tmp_path / "docs")
    (tmp_path / "skills").mkdir()
    (tmp_path / "agents").mkdir()
    (tmp_path / "mcp").mkdir()
    (tmp_path / ".claude").mkdir()
    pyproject = '[project]\nname = "wagents"\nrequires-python = ">=3.13"\n'
    (tmp_path / "pyproject.toml").write_text(pyproject, encoding="utf-8")
    shutil.copytree(REAL_REPO_ROOT / "scripts" / "validate", tmp_path / "scripts" / "validate")
    shutil.copytree(REAL_REPO_ROOT / "skills" / "skill-creator", tmp_path / "skills" / "skill-creator")
    shutil.copytree(REAL_REPO_ROOT / "wagents", tmp_path / "wagents")
    (tmp_path / "config").mkdir(exist_ok=True)
    for rel in (
        "config/mcp-registry.json",
        "config/sync-manifest.json",
        "config/tooling-policy.json",
        "config/harness-surface-registry.json",
        "planning/manifests/security-quarantine-register.json",
        "AGENTS.md",
    ):
        src = REAL_REPO_ROOT / rel
        if src.is_file():
            dest = tmp_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
    monkeypatch.setenv("WAGENTS_REPO_ROOT", str(tmp_path))
    return tmp_path


class TestExtractHooks:
    """Unit tests for extract_hooks helper."""

    def test_empty_dict(self):
        assert extract_hooks("test", {}) == []

    def test_command_hook(self):
        hooks_dict = {
            "PostToolUse": [
                {
                    "matcher": "Edit|Write",
                    "hooks": [{"type": "command", "command": "echo hello"}],
                }
            ]
        }
        result = extract_hooks("test", hooks_dict)
        assert len(result) == 1
        assert result[0].event == "PostToolUse"
        assert result[0].matcher == "Edit|Write"
        assert result[0].handler_type == "command"
        assert result[0].command == "echo hello"

    def test_prompt_hook(self):
        hooks_dict = {
            "Stop": [
                {
                    "hooks": [{"type": "prompt", "prompt": "Verify all tests pass"}],
                }
            ]
        }
        result = extract_hooks("test", hooks_dict)
        assert len(result) == 1
        assert result[0].handler_type == "prompt"
        assert result[0].prompt == "Verify all tests pass"
        assert result[0].matcher == ""

    def test_multiple_events(self):
        hooks_dict = {
            "PreToolUse": [{"matcher": "Bash", "hooks": [{"command": "echo pre"}]}],
            "PostToolUse": [{"matcher": "Write", "hooks": [{"command": "echo post"}]}],
        }
        result = extract_hooks("test", hooks_dict)
        assert len(result) == 2

    def test_non_dict_input(self):
        assert extract_hooks("test", "not a dict") == []
        assert extract_hooks("test", None) == []

    def test_shorthand_format(self):
        """Shorthand format with command directly on entry (no nested hooks)."""
        hooks_dict = {"PreToolUse": [{"matcher": "Edit", "command": "echo shorthand"}]}
        result = extract_hooks("test", hooks_dict)
        assert len(result) == 1
        assert result[0].command == "echo shorthand"
        assert result[0].handler_type == "command"
        assert result[0].matcher == "Edit"

    def test_shorthand_multiple_events(self):
        """Shorthand format across multiple events."""
        hooks_dict = {
            "PreToolUse": [{"matcher": "Edit", "command": "echo pre"}],
            "PostToolUse": [{"matcher": "Edit", "command": "echo post"}],
        }
        result = extract_hooks("test", hooks_dict)
        assert len(result) == 2


class TestHooksList:
    """Tests for wagents hooks list command."""

    def test_no_hooks(self, patched_repo):
        result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        assert "No hooks found" in result.output

    def test_no_hooks_json(self, patched_repo):
        result = runner.invoke(app, ["hooks", "list", "--format", "json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload == {"count": 0, "hooks": []}

    def test_settings_hooks(self, patched_repo):
        settings = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Edit|Write",
                        "hooks": [{"type": "command", "command": "echo format"}],
                    }
                ]
            }
        }
        (patched_repo / ".claude" / "settings.json").write_text(json.dumps(settings))
        result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        assert "settings.json" in result.output
        assert "PostToolUse" in result.output

    def test_skill_hooks(self, patched_repo):
        skill_dir = patched_repo / "skills" / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: Test\nhooks:\n"
            "  PreToolUse:\n    - matcher: Bash\n      hooks:\n"
            "        - type: command\n          command: echo check\n"
            "---\n\n# Test\n\nBody.\n"
        )
        result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        assert "skill:test-skill" in result.output
        assert "PreToolUse" in result.output

    def test_skill_hooks_jsonl(self, patched_repo):
        skill_dir = patched_repo / "skills" / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: Test\nhooks:\n"
            "  PreToolUse:\n    - matcher: Bash\n      hooks:\n"
            "        - type: command\n          command: echo check\n"
            "---\n\n# Test\n\nBody.\n"
        )
        result = runner.invoke(app, ["hooks", "list", "--format", "jsonl"])
        assert result.exit_code == 0
        records = [json.loads(line) for line in result.output.strip().splitlines()]
        assert records[0]["type"] == "hook"
        assert records[0]["source"] == "skill:test-skill"
        assert records[0]["handler_type"] == "command"
        assert records[-1] == {"type": "summary", "count": 1}

    def test_skill_shorthand_hooks(self, patched_repo):
        """Skills using shorthand format appear in list."""
        skill_dir = patched_repo / "skills" / "short-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: short-skill\ndescription: Test\nhooks:\n"
            "  PreToolUse:\n    - matcher: Edit\n"
            "      command: echo shorthand\n"
            "---\n\n# Short\n\nBody.\n"
        )
        result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        assert "skill:short-skill" in result.output
        assert "echo shorthand" in result.output

    def test_agent_hooks(self, patched_repo):
        (patched_repo / "agents" / "test-agent.md").write_text(
            "---\nname: test-agent\ndescription: Test\nhooks:\n"
            "  Stop:\n    - hooks:\n"
            "        - type: prompt\n          prompt: Check results\n"
            "---\n\n# Test Agent\n\nBody.\n"
        )
        result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        assert "agent:test-agent" in result.output
        assert "Stop" in result.output

    def test_hooks_list_real_repo(self):
        """Running hooks list against the real repo should succeed."""
        result = runner.invoke(app, ["hooks", "list"])
        assert result.exit_code == 0
        # Real repo has hooks in settings.json and skill-creator at minimum
        assert "settings.json" in result.output


class TestHooksValidate:
    """Tests for wagents hooks validate command."""

    def test_no_hooks_valid(self, patched_repo):
        result = runner.invoke(app, ["hooks", "validate"])
        assert result.exit_code == 0
        assert "All hooks valid" in result.output

    def test_no_hooks_valid_json(self, patched_repo):
        result = runner.invoke(app, ["hooks", "validate", "--format", "json"])
        assert result.exit_code == 0
        payload = json.loads(result.output)
        assert payload["ok"] is True
        assert payload["error_count"] == 0
        assert payload["errors"] == []

    def test_valid_hooks(self, patched_repo):
        settings = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Edit",
                        "hooks": [{"type": "command", "command": "echo ok"}],
                    }
                ]
            }
        }
        (patched_repo / ".claude" / "settings.json").write_text(json.dumps(settings))
        result = runner.invoke(app, ["hooks", "validate"])
        assert result.exit_code == 0

    def test_unknown_event(self, patched_repo):
        settings = {"hooks": {"FakeEvent": [{"hooks": [{"type": "command", "command": "echo bad"}]}]}}
        (patched_repo / ".claude" / "settings.json").write_text(json.dumps(settings))
        result = runner.invoke(app, ["hooks", "validate"])
        assert result.exit_code == 1
        assert "unknown hook event" in result.output

    def test_unknown_event_jsonl(self, patched_repo):
        settings = {"hooks": {"FakeEvent": [{"hooks": [{"type": "command", "command": "echo bad"}]}]}}
        (patched_repo / ".claude" / "settings.json").write_text(json.dumps(settings))
        result = runner.invoke(app, ["hooks", "validate", "--format", "jsonl"])
        assert result.exit_code == 1
        records = [json.loads(line) for line in result.output.strip().splitlines()]
        assert records[0]["type"] == "error"
        assert records[0]["source"] == "settings.json"
        assert "unknown hook event" in records[0]["message"]
        assert records[-1]["type"] == "summary"
        assert records[-1]["ok"] is False

    def test_unknown_handler_type(self, patched_repo):
        settings = {"hooks": {"PostToolUse": [{"hooks": [{"type": "invalid", "command": "echo bad"}]}]}}
        (patched_repo / ".claude" / "settings.json").write_text(json.dumps(settings))
        result = runner.invoke(app, ["hooks", "validate"])
        assert result.exit_code == 1
        assert "unknown handler type" in result.output

    def test_empty_command(self, patched_repo):
        settings = {"hooks": {"PostToolUse": [{"hooks": [{"type": "command", "command": ""}]}]}}
        (patched_repo / ".claude" / "settings.json").write_text(json.dumps(settings))
        result = runner.invoke(app, ["hooks", "validate"])
        assert result.exit_code == 1
        assert "empty command" in result.output

    def test_valid_shorthand_hooks(self, patched_repo):
        """Shorthand format passes validation."""
        skill_dir = patched_repo / "skills" / "short-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: short-skill\ndescription: Test\nhooks:\n"
            "  PreToolUse:\n    - matcher: Edit\n"
            "      command: echo ok\n"
            "---\n\n# Short\n\nBody.\n"
        )
        result = runner.invoke(app, ["hooks", "validate"])
        assert result.exit_code == 0

    def test_cursor_harness_accepts_flat_project_hooks(self, patched_repo):
        cursor_dir = patched_repo / ".cursor"
        cursor_dir.mkdir()
        (cursor_dir / "hooks.json").write_text(
            json.dumps({
                "version": 1,
                "hooks": {
                    "preToolUse": [
                        {
                            "command": '"$CURSOR_PROJECT_DIR/hooks/run-wagents-hook" demo --harness cursor',
                            "matcher": "Bash",
                            "timeout": 5,
                        }
                    ]
                },
            }),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["hooks", "validate", "--harness", "cursor"])

        assert result.exit_code == 0
        assert "All hooks valid" in result.output

    def test_cursor_harness_rejects_nested_project_hooks(self, patched_repo):
        cursor_dir = patched_repo / ".cursor"
        cursor_dir.mkdir()
        (cursor_dir / "hooks.json").write_text(
            json.dumps({
                "version": 1,
                "hooks": {
                    "preToolUse": [
                        {
                            "matcher": "Bash",
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "python3 ${workspaceFolder}/hooks/wagents-hook.py demo",
                                }
                            ],
                        }
                    ]
                },
            }),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["hooks", "validate", "--harness", "cursor"])

        assert result.exit_code == 1
        assert "Cursor hook entries must be flat" in result.output
        assert "Cursor hook entry command is required" in result.output

    def test_cursor_harness_rejects_workspacefolder_commands(self, patched_repo):
        cursor_dir = patched_repo / ".cursor"
        cursor_dir.mkdir()
        (cursor_dir / "hooks.json").write_text(
            json.dumps({
                "version": 1,
                "hooks": {
                    "preToolUse": [
                        {
                            "command": "python3 ${workspaceFolder}/hooks/wagents-hook.py demo",
                            "matcher": "Bash",
                        }
                    ]
                },
            }),
            encoding="utf-8",
        )

        result = runner.invoke(app, ["hooks", "validate", "--harness", "cursor"])

        assert result.exit_code == 1
        assert "$CURSOR_PROJECT_DIR" in result.output

    def test_hooks_validate_real_repo(self):
        """Running hooks validate against the real repo should pass."""
        result = runner.invoke(app, ["hooks", "validate"])
        assert result.exit_code == 0, f"hooks validate failed:\n{result.output}"
        assert "All hooks valid" in result.output


class TestKnownEvents:
    """Verify KNOWN_HOOK_EVENTS completeness."""

    def test_event_count(self):
        assert len(KNOWN_HOOK_EVENTS) == 25

    def test_key_events_present(self):
        for event in [
            "SessionStart",
            "PreToolUse",
            "PostToolUse",
            "Stop",
            "SessionEnd",
        ]:
            assert event in KNOWN_HOOK_EVENTS


class TestSkillCreatorVerify:
    """Regression tests for the skill-creator deterministic hook verifier."""

    def test_stop_guard_skips_recursive_validation(self, monkeypatch):
        monkeypatch.setattr(sys, "stdin", type("In", (), {"read": lambda self: '{"stop_hook_active": true}'})())
        monkeypatch.setattr(
            skill_creator_verify.subprocess,
            "run",
            lambda *args, **kwargs: pytest.fail("recursive stop guard should not run subprocesses"),
        )

        assert skill_creator_verify.main(["stop"]) == 0

    def test_post_tool_use_skill_file_runs_validate_and_hooks(self, monkeypatch):
        commands = []
        monkeypatch.setattr(
            sys,
            "stdin",
            type(
                "In",
                (),
                {"read": lambda self: '{"tool_input": {"file_path": "skills/demo/SKILL.md"}}'},
            )(),
        )

        def fake_run(command, **kwargs):
            commands.append(command)
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        monkeypatch.setattr(skill_creator_verify.subprocess, "run", fake_run)

        assert skill_creator_verify.main(["post-tool-use"]) == 0
        assert any(cmd[-1].endswith("validate_skill.py") for cmd in commands)
        assert any(cmd[-1].endswith("validate_hooks.py") for cmd in commands)

    def test_stop_dirty_eval_runs_eval_validate(self, monkeypatch):
        commands = []
        monkeypatch.setattr(sys, "stdin", type("In", (), {"read": lambda self: "{}"})())

        def fake_run(command, **kwargs):
            commands.append(command)
            if command[:2] == ["git", "status"]:
                return type(
                    "Result",
                    (),
                    {
                        "returncode": 0,
                        "stdout": " M skills/demo/evals/evals.json\n",
                        "stderr": "",
                    },
                )()
            return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

        monkeypatch.setattr(skill_creator_verify.subprocess, "run", fake_run)

        assert skill_creator_verify.main(["stop"]) == 0
        assert any(cmd[-1].endswith("validate_evals.py") for cmd in commands)


class TestValidateIncludesHooks:
    """Verify wagents validate also checks hooks."""

    def test_validate_catches_bad_hook_event(self, patched_repo):
        settings = {"hooks": {"BadEvent": [{"hooks": [{"type": "command", "command": "echo x"}]}]}}
        (patched_repo / ".claude" / "settings.json").write_text(json.dumps(settings))
        result = runner.invoke(app, ["validate"])
        assert result.exit_code == 1
        assert "unknown hook event" in result.output

    def test_validate_catches_bad_skill_hook_event(self, patched_repo):
        """Validate also checks hook events inside skill frontmatter."""
        skill_dir = patched_repo / "skills" / "bad-hooks"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: bad-hooks\ndescription: Test\nhooks:\n"
            "  NotARealEvent:\n    - hooks:\n"
            "        - type: command\n          command: echo x\n"
            "---\n\n# Bad\n\nBody.\n"
        )
        result = runner.invoke(app, ["validate"])
        assert result.exit_code == 1
        assert "unknown hook event" in result.output
