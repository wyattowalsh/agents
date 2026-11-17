## Tasks

1. [x] Confirm branch, dirty state, AGENTS instructions, eval inventory, and skill discovery roots.
2. [x] Create OpenSpec change artifacts for `consolidate-review-skill`.
3. [x] Add `skills/review/SKILL.md` with portable frontmatter, dispatch table, output contract, harness policy, and reference/script index.
4. [x] Add review references for finding contracts, specialist lenses, simplification lens, source/provenance lens, research validation, judge reconciliation, self-verification, output formats, SARIF, conventional comments, auto-fix, dependency context, and supply-chain security.
5. [x] Add review helper scripts and `scripts/check.py`.
6. [x] Add `skills/review/evals/evals.json` covering session/scoped/PR/audit, simplify, source/provenance, specialist lenses, output formats, history/delta/learnings, approval-gated fixes, harness portability, and negative controls.
7. [x] Delete `honest-review`, `simplify`, and `external-skill-auditor` as skills and remove installable/catalog surfaces for them.
8. [x] Update `code-reviewer` and `security-auditor` to delegate to `/review` while remaining read-only.
9. [x] Update source instruction references and adjacent skill redirects from legacy names to `/review` where appropriate.
10. [x] Add `docs/src/skill-research/review.md` with local inventory, GitHub/source-list research, trust risks, duplicate clusters, and synthesis outcomes.
11. [x] Run custom authoring sync and regenerate docs/catalog/README surfaces.
12. [x] Run OpenSpec, skill/package/eval/docs validation.
13. [x] Run per-harness sync dry-runs for Claude Code, Codex, OpenCode, Grok, Cursor, and Gemini CLI; run Grok doctor if available.
14. [x] Run stale-reference audit and classify remaining hits.
15. [x] Run final hygiene (`git diff --check`, `git status --short --branch`).
