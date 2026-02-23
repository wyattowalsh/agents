# CI Integration Guide

Run honest-review in CI pipelines for automated code review on pull requests.

## Contents

- [GitHub Actions](#github-actions)
- [Exit Codes](#exit-codes)
- [Inline PR Comments](#inline-pr-comments)
- [Configuration](#configuration)

## GitHub Actions

Basic workflow that runs honest-review on every PR:

```yaml
name: Code Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0 # Full history for git diff
      - name: Run honest-review
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          claude --skill honest-review "PR ${{ github.event.pull_request.number }}"
```

## Exit Codes

When running in CI, use exit codes to control pipeline flow:

| Exit Code | Meaning                   | Pipeline Action                |
| --------- | ------------------------- | ------------------------------ |
| 0         | No P0/P1 or S0 findings   | Pass                           |
| 1         | P1 or S0 findings present | Warn (non-blocking by default) |
| 2         | P0 findings present       | Fail (block merge)             |

Configure blocking behavior in the workflow:

```yaml
- name: Check review results
  run: |
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 2 ]; then
      echo "::error::Critical findings detected — merge blocked"
      exit 1
    elif [ $EXIT_CODE -eq 1 ]; then
      echo "::warning::Significant findings detected — review recommended"
    fi
```

## Inline PR Comments

Post findings as inline PR comments using the GitHub CLI:

```bash
# Post a review comment on a specific file and line
gh api repos/{owner}/{repo}/pulls/{pr}/comments \
  --method POST \
  -f body="**HR-S-001** [P1, Confidence: 0.85] Missing input validation\n\nEvidence: OWASP A03:2021\nFix: Add validation middleware" \
  -f commit_id="$(git rev-parse HEAD)" \
  -f path="src/api/users.py" \
  -F line=45 \
  -f side="RIGHT"
```

For batch posting, pipe findings through `scripts/finding-formatter.py` and iterate over the JSON output.

## Configuration

Environment variables for CI tuning:

| Variable                     | Default   | Description                                 |
| ---------------------------- | --------- | ------------------------------------------- |
| `HONEST_REVIEW_MODE`         | `session` | Force `session` or `audit` mode             |
| `HONEST_REVIEW_SEVERITY`     | `P1`      | Minimum severity to report (P0, P1, P2, P3) |
| `HONEST_REVIEW_CONFIDENCE`   | `0.7`     | Minimum confidence threshold                |
| `HONEST_REVIEW_MAX_FINDINGS` | `15`      | Cap on reported findings                    |
| `HONEST_REVIEW_EXIT_ON`      | `P0`      | Severity that triggers non-zero exit        |
| `HONEST_REVIEW_FORMAT`       | `text`    | Output format: `text`, `sarif`, `json`      |

These can be parsed by a wrapper script around the skill invocation to customize review behavior in CI.

## SARIF Upload

When `HONEST_REVIEW_FORMAT=sarif`, pipe output to GitHub Code Scanning:

```yaml
- name: Upload SARIF
  if: always()
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
    category: honest-review
```

Or upload manually via `scripts/sarif-uploader.py`. See `references/sarif-output.md` for full SARIF format spec.

## GitHub Check Runs

Create detailed check runs with inline annotations for richer PR feedback:

```bash
# Create a check run with annotations
gh api repos/{owner}/{repo}/check-runs \
  --method POST \
  -f name="honest-review" \
  -f head_sha="$(git rev-parse HEAD)" \
  -f status="completed" \
  -f conclusion="action_required" \
  -f "output[title]=Honest Review: 3 findings" \
  -f "output[summary]=P0: 1, P1: 2, P2: 0" \
  --input annotations.json
```

Check runs provide collapsible annotations in the PR Files tab — richer than PR comments for large reviews.
