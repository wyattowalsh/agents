"""Regression tests for skills/skill-creator/scripts/audit.py."""

import sys
import textwrap
from pathlib import Path

# Insert the script directory into sys.path so we can import directly.
sys.path.insert(0, str(Path(__file__).parent.parent / "skills" / "skill-creator" / "scripts"))

from audit import PATTERN_NAMES, audit_skill, format_table


def _write_skill(tmp_path: Path, name: str, body: str, *, frontmatter: str | None = None) -> Path:
    """Create a minimal skill fixture on disk and return its directory."""
    skill_dir = tmp_path / name
    skill_dir.mkdir()
    fm = (
        frontmatter
        or f"""\
    ---
    name: {name}
    description: Create focused skill docs. Use when auditing prompts. NOT for agents.
    ---
    """
    )
    (skill_dir / "SKILL.md").write_text(
        textwrap.dedent(fm).strip() + "\n\n" + textwrap.dedent(body).strip() + "\n",
        encoding="utf-8",
    )
    return skill_dir


def test_pattern_detection_avoids_keyword_false_positives(tmp_path: Path):
    skill_dir = _write_skill(
        tmp_path,
        "keyword-noise",
        """
        # Keyword Noise

        ## Dispatch

        | $ARGUMENTS | Action |
        |------------|--------|
        | `lint` | Review text |
        | Empty | Show help |

        ## Notes

        This write-up mentions a fluid type scale, a generic classification note,
        prose-only vocabulary, and a team journal that helps save time.

        ## Critical Rules

        1. Always validate the final artifact
        2. Never modify unrelated files
        3. Keep the body concise
        """,
    )

    result = audit_skill(str(skill_dir))

    assert result["bonus"] == 0
    assert result["max"] == 100
    assert "canonical-vocabulary" not in result["patterns_found"]
    assert "classification-gating" not in result["patterns_found"]
    assert "scaling-strategy" not in result["patterns_found"]
    assert "state-management" not in result["patterns_found"]


def test_pattern_detection_requires_structural_evidence(tmp_path: Path):
    skill_dir = _write_skill(
        tmp_path,
        "structured-audit",
        """
        # Structured Audit

        ## Dispatch

        | $ARGUMENTS | Action |
        |------------|--------|
        | `create <name>` | Create |
        | `improve <name>` | Improve |
        | `audit <name>` | Audit |
        | Empty | Show help |

        ### Auto-Detection Heuristic

        1. Existing skill path -> Improve
        2. Explicit audit request -> Audit
        3. Otherwise -> Create

        ## Scaling Strategy

        | Scope | Strategy |
        |-------|----------|
        | 1-2 files | Inline review |
        | 3-5 files | Parallel subagents |
        | 6+ files | Batch by directory |

        ## State Management

        - Journal directory: `~/.{gemini|copilot|codex|claude}/structured-audit/`
        - Resume with `resume <name>`
        - Override with `--state-dir`

        ## Hooks

        Stop hooks run validation before the agent exits.

        ## Critical Rules

        1. Always validate before exit
        2. Always ask for clarification on ambiguous targets
        3. Never overwrite unrelated changes
        4. Always keep mode labels stable
        5. Never skip the final validation pass

        **Canonical terms** (use these exactly throughout):
        - Modes: "Create", "Improve", "Audit"
        - Status: "Ready", "Blocked"
        """,
        frontmatter="""\
        ---
        name: structured-audit
        description: Create or classify skill work. Use when triaging skill requests. NOT for agents.
        hooks:
          Stop:
            - matcher: Bash
              hooks:
                - command: "uv run wagents validate"
        ---
        """,
    )

    result = audit_skill(str(skill_dir))

    assert result["bonus"] == 0
    assert result["max"] == 100
    assert "canonical-vocabulary" in result["patterns_found"]
    assert _dimension(result, "canonical-vocabulary")["score"] >= 4
    assert "classification-gating" in result["patterns_found"]
    assert "scaling-strategy" in result["patterns_found"]
    assert "state-management" in result["patterns_found"]
    assert "stop-hooks" in result["patterns_found"]


def test_pattern_catalog_reports_status_buckets_and_dimension_contract(tmp_path: Path):
    skill_dir = _write_skill(
        tmp_path,
        "background-helper",
        """
        # Background Helper

        ## Critical Rules

        1. Always stay read-only
        2. Never modify unrelated files
        3. Keep outputs concise
        4. Always validate assumptions
        5. Never invent missing context
        """,
        frontmatter="""\
        ---
        name: background-helper
        description: Analyze existing skill text. Use when reviewing internal helpers. NOT for agents.
        user-invocable: false
        ---
        """,
    )

    result = audit_skill(str(skill_dir))
    catalog_total = (
        len(result["patterns_found"]) + len(result["patterns_suggested"]) + len(result["patterns_not_applicable"])
    )

    assert len(result["dimensions"]) == 13
    assert catalog_total == len(PATTERN_NAMES) == 14
    assert "dispatch-table" in result["patterns_not_applicable"]
    assert _dimension(result, "evaluation-coverage")["score"] == 0
    assert _dimension(result, "validation-contract")["score"] >= 4


def test_progressive_disclosure_detects_script_backed_layered_guidance(tmp_path: Path):
    skill_dir = _write_skill(
        tmp_path,
        "script-backed-helper",
        """
        # Script Backed Helper

        ## Dispatch

        | $ARGUMENTS | Action |
        |------------|--------|
        | `run` | Execute helper |
        | `audit` | Review output |
        | `status` | Show current state |
        | `resume` | Continue prior work |
        | Empty | Show help |

        ## Progressive Disclosure

        Frontmatter for discovery, body for dispatch, references loaded on demand,
        and scripts/templates for execution. Do not load all at once; read files as indicated.

        ## Critical Rules

        1. Always keep instructions concise
        2. Never modify unrelated files
        3. Always validate assumptions
        4. Never skip the dispatch table
        5. Always use the helper script for execution
        """,
    )
    scripts_dir = skill_dir / "scripts"
    scripts_dir.mkdir()
    (scripts_dir / "helper.py").write_text("print('ok')\n", encoding="utf-8")

    result = audit_skill(str(skill_dir))

    assert "scripts" in result["patterns_found"]
    assert "progressive-disclosure" in result["patterns_found"]


def _dimension(result: dict, dim_id: str) -> dict:
    """Return a dimension by id from an audit result."""
    return next(dim for dim in result["dimensions"] if dim["id"] == dim_id)


def test_evaluation_and_validation_dimensions_score_real_contracts(tmp_path: Path):
    skill_dir = _write_skill(
        tmp_path,
        "contracted-skill",
        """
        # Contracted Skill

        ## Dispatch

        | $ARGUMENTS | Action |
        |------------|--------|
        | `audit <path>` | Audit |
        | Natural language request | Audit |
        | Invalid path | Refuse |
        | Empty | Show help |

        ## Validation

        Run `uv run wagents validate`, `uv run wagents eval validate`,
        `uv run python skills/contracted-skill/scripts/audit.py skills/<name>/`,
        and `uv run wagents package contracted-skill --dry-run`.
        These commands must pass before declaring the skill complete.

        ## Critical Rules

        1. Always validate before exit
        2. Never skip eval validation
        3. Always audit the skill path
        4. Never package without dry-run
        5. Always report zero errors
        """,
        frontmatter="""\
        ---
        name: contracted-skill
        description: Audit contracted skill work. Use when checking skill quality. NOT for agents.
        license: MIT
        metadata:
          author: tester
          version: "1.0.0"
        ---
        """,
    )
    evals_dir = skill_dir / "evals"
    evals_dir.mkdir()
    (evals_dir / "evals.json").write_text(
        textwrap.dedent(
            """\
            {
              "skill_name": "contracted-skill",
              "evals": [
                {
                  "id": "explicit-invocation",
                  "prompt": "/contracted-skill audit skills/foo",
                  "expected_output": "Dispatches explicit invocation to Audit.",
                  "assertions": ["Agent routes explicit invocation to Audit."]
                },
                {
                  "id": "implicit-trigger",
                  "prompt": "Check this skill quality",
                  "expected_output": "Treats natural-language trigger as Audit.",
                  "assertions": ["Agent recognizes implicit trigger."]
                },
                {
                  "id": "negative-control",
                  "prompt": "Create an agent",
                  "expected_output": "Does not trigger contracted-skill.",
                  "assertions": ["Agent does not trigger on negative control."]
                },
                {
                  "id": "scope-refusal",
                  "prompt": "/contracted-skill invalid path",
                  "expected_output": "Refuses malformed invalid input.",
                  "assertions": ["Agent refuses malformed input."]
                }
              ]
            }
            """
        ),
        encoding="utf-8",
    )

    result = audit_skill(str(skill_dir))

    assert result["max"] == 100
    assert result["bonus"] == 0
    assert _dimension(result, "evaluation-coverage")["score"] == 10
    assert _dimension(result, "validation-contract")["score"] >= 9


def test_audit_table_never_reports_legacy_103_scale(tmp_path: Path):
    skill_dir = _write_skill(
        tmp_path,
        "vocab-skill",
        """
        # Vocab Skill

        ## Dispatch

        | $ARGUMENTS | Action |
        |------------|--------|
        | `audit` | Audit |
        | Empty | Show help |

        ## Critical Rules

        1. Always validate output
        2. Never skip checks
        3. Always report findings
        4. Never invent context
        5. Always keep terms stable

        **Canonical terms** (use these exactly throughout):
        - Modes: "Audit", "Help", "Refuse"
        - Status: "Ready", "Blocked"
        """,
    )

    result = audit_skill(str(skill_dir))
    table = format_table([result])

    assert result["max"] == 100
    assert result["score"] <= 100
    assert "/" + "103" not in table
    assert "/100" in table
