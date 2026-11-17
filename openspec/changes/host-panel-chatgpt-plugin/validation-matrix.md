# Validation Matrix

Commands below describe acceptance checks. A command is not a passing result until its execution is recorded.

| Surface | Command or observation | Required result |
| --- | --- | --- |
| Python environment | `uv sync --locked --group dev` | Owning lockfile resolves without dependency changes |
| Exporter and tests | `uv run ruff check scripts/build_host_panel_plugin.py tests/test_host_panel_plugin.py` | No lint errors |
| Exporter formatting | `uv run ruff format --check scripts/build_host_panel_plugin.py tests/test_host_panel_plugin.py` | No formatting drift |
| Exporter typing | `uv run ty check scripts/build_host_panel_plugin.py tests/test_host_panel_plugin.py` | No errors in the changed Python surfaces |
| Exporter behavior | `uv run pytest tests/test_host_panel_plugin.py -q` | Exact source bytes, narrow inclusion, valid release identity, link closure, path safeguards, and deterministic archives |
| Canonical skill | `uv run python skills/host-panel/scripts/check.py` | Skill, eval, portability, and audit checks succeed, or concrete existing blockers are reported |
| Eval structure | `uv run wagents eval validate --format json` | Valid JSON scenarios; this is not a behavioral model evaluation |
| Eval adequacy | `uv run wagents eval adequacy --skill host-panel --format json` | Structural coverage is reported without claiming empirical reliability |
| Repository assets | `uv run wagents validate` | Required asset validation passes or unrelated failures are identified |
| OpenSpec | `uv run wagents openspec validate` | Change documents satisfy the owning workflow, or tooling/network blocker is reported |
| Generated docs | Owning authoring sync, then `uv run wagents docs generate --no-installed --check` | Affected generated surfaces match canonical source |
| README | `uv run wagents readme --check` | Description changes are represented in generated README |
| Whitespace | `git diff --check` | No whitespace errors |
| Release artifact | `uv run python scripts/build_host_panel_plugin.py --out ../host-panel-0.1.0.zip --release-version 0.1.0` | New archive outside the repo, content digests, and no source mutation |
| Chat runtime | Fresh session with installed candidate | Observed discovery, invocation, reference loading, contextual request handling, and truthful execution description |
| Other modes | Separate observed invocation in each claimed mode | Evidence for that mode; no inferred universal availability |

## Known Baseline Limits

At the pinned baseline, generic plugin-builder documentation and distribution tests do not fully match the tracked implementation. This change does not repair those unrelated surfaces or treat them as proof of Chat compatibility. Runtime product availability remains separate from package validity.

## Execution Record

On 2026-11-17, in the repository's uv-managed Python 3.13 environment:

- `uv sync --locked --group dev` completed successfully in the parent workstream. No dependency or lockfile change was needed for the exporter.
- `uv run --no-sync ruff check scripts/build_host_panel_plugin.py tests/test_host_panel_plugin.py` passed.
- `uv run --no-sync ruff format --check scripts/build_host_panel_plugin.py tests/test_host_panel_plugin.py` passed.
- `uv run --no-sync ty check scripts/build_host_panel_plugin.py tests/test_host_panel_plugin.py` passed after the existing sparse checkout's referenced source directories were materialized.
- `uv run --no-sync pytest tests/test_host_panel_plugin.py -q` passed: 33 cases.
- Scoped strict OpenSpec validation through `wagents.openspec.run_openspec(["validate", "host-panel-chatgpt-plugin", "--strict", "--json"], ...)` passed with one valid change and no issues. The change includes explicit added-requirements scenarios; no `skip_specs` exemption is used.

### Canonical skill and controlled behavior

- The skill creator's `quick_validate.py`, the owning skill validator, and eval validator passed. The existing `scripts/check.py` completed successfully, including a portable package dry run with all seven reference paths resolved.
- `wagents eval validate --format json` passed repository-wide. The host-panel manifest contains 32 behavior specifications, retaining the original 15 case IDs. This is not a claim of 32 executed behavioral passes.
- `wagents eval adequacy --skill host-panel --format json` reported R1/E4 structural coverage. The older rubric-based skill audit scored 61/100, in part because it expects a `$ARGUMENTS` dispatch and shell validation commands inside the runtime skill. Those client-specific features were not reintroduced to raise a heuristic score.
- Two controlled conversations in fresh native subagent contexts produced three observed responses: a compact contextual Oxford panel; a six-perspective Socratic opening without actual delegation; and an immediate end-panel response. Verbatim outputs and limitations are recorded in `skills/host-panel/evals/runs/2026-11-17-chat-baseline.json`. These trials used a constrained profile, not an installed ChatGPT plugin UI.

### Generated documentation

- The host authoring MDX and public catalog page match a second generation by the owning functions. The README check reports `up_to_date: true`.
- The generated host page passes strict docs lint with zero errors and zero warnings. Its seven relative reference links occur inside the source-disclosure fence, not as active web links.
- Both host-panel catalog rows match generator output. All 3,650 non-host row occurrences and the external-only browser index were preserved. Full regeneration would change 231 unrelated baseline entries, so that drift was not included.
- A full Astro build and rendered UI checks were not run in this partial checkout. No new visual component was introduced.

### Release and private save

- Built release `0.1.0`: nine archive files, 27,344 bytes. The archive includes one portable manifest, the canonical skill, and seven Markdown references. No scripts, evals, app, MCP, product restriction, or tool dependency ships.
- Source input SHA-256: `892fce67320826ac78e5392118b209670060fc0f3c5f06e9e358498f98603e0f`.
- Archive SHA-256: `310455200fb3cfc9df3eb2ce0dfd6afd3c792a76c21d1899a47f6d48aed14a0d`.
- The private account save succeeded. Readback matched all eight Markdown files byte for byte. The service added the account author email to the portable manifest and generated `.codex-plugin/plugin.json`; identity, version, skill-discovery path, and interface metadata agree. No runtime dependency was introduced.
- Installed discovery and invocation in a fresh Chat session, iPhone, Work, and Codex remain unobserved. There is no claim of universal mode availability or measured decision-quality improvement.

### Repository-wide limits

- `wagents validate --format json` remains blocked by the existing missing `wagents.mcphub.things_contract` import. That module is absent from the pinned tracked source and is outside this change.
- Full strict OpenSpec validation evaluated 53 items: 45 valid, 8 invalid. `host-panel-chatgpt-plugin` is valid with no issues. Unrelated invalid items are `activate-candidate-corpus-runtime-jul2026`, `cursor-harness`, `docs-instructions`, `fleet-hooks-promotion`, `fleet-skill-projection-assurance`, `integrate-mcphub-control-plane`, `public-release-prod-readiness`, and `replace-supathings-with-things-plus-plus`.
- No unrelated source, validator, or requirement was changed to make a global check pass.
