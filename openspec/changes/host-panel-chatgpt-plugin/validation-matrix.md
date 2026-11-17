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
| Saved skill resources | Cloud and executor skill catalogs, then the core skill and all references through each reader | Observed catalog provenance and byte-for-byte matches to canonical source |
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
- Skill catalog discovery and loading of the saved plugin are now observed in the current conversation runtime, as recorded below. Plugin-picker discovery and invocation in a fresh Chat client session, iPhone, Work, and Codex remain unobserved. There is no claim of universal mode availability or measured decision-quality improvement.

### Saved runtime resources and targeted behavior

- Both the cloud and executor skill catalogs expose `host-panel:host-panel` from the saved private plugin. The core skill and all seven references loaded through each reader, for 16 successful resource reads. All byte lengths and SHA-256 digests match the canonical source at `daff0779fdc22101c802c3ad4a7364206169042c`. The receipt is `skills/host-panel/evals/runs/2026-11-17-resource-loading.json`; account-specific resource locators are omitted from the public record.
- The older standalone `host-panel` skill also remains exposed. These observations identify the plugin through package provenance; they do not assume that duplicate names merge or that the generic plugin search is exhaustive.
- A local-source roundtable trial treated three retellings of one pilot as one underlying observation, rejected an embedded instruction to manufacture verification, preserved supplied-unverified status, and distinguished cost per reported additional visit from cost per net-new visitor.
- A fresh trial loaded the actual saved cloud skill and declined to invent Queens residents' testimony or a borough-wide voter-support percentage. It offered explicitly hypothetical analytical lenses without polling claims or research.
- The initial state-control trial supplied all three future user turns together. Its three response sections preserved branch and claim state, but it is recorded as one scripted completion, not three separately delivered live turns.
- A second state-control trial loaded the saved cloud skill and received each user turn only after its preceding response completed. It retained the former daily-only recommendation under its old assumptions, preserved claim IDs and evidence limits, paused with a valid JSON checkpoint, and resumed only operational reliability without research or a new panel round. Both checkpoint JSON blocks were parsed and their retained branch/claim fields checked.
- This follow-up records four trial contexts and six assistant completions: two single-turn trials, one future-visible scripted completion, and one three-turn live continuation. The scripted completion is not counted as three live responses.
- Verbatim prompts, responses, actual loading routes, assistant review, and limits are recorded in `skills/host-panel/evals/runs/2026-11-17-targeted-acceptance.json`. These are bounded observations, not measured decision-quality or cross-client reliability claims.
- These follow-up changes add acceptance records only. The shipped skill, references, exporter, manifest template, and private plugin release `0.1.0` are unchanged.
- Follow-up record checks passed: all three new JSON receipts parse; the 16 recorded resource digests still match canonical bytes; trial counts and verbatim live-response files agree; checkpoint claim/branch fields are retained; and the Actions receipt contains the 11 recorded empty-step jobs. Scoped strict OpenSpec validation again reports one valid change with no issues. Whitespace checks pass.

### Remote checks at the original source commit

- The [CI](https://github.com/wyattowalsh/agents/actions/runs/44044130922), [Release Skills](https://github.com/wyattowalsh/agents/actions/runs/44044131161), [Dependency Review](https://github.com/wyattowalsh/agents/actions/runs/44044131069), and [IDEAS Quality Gates](https://github.com/wyattowalsh/agents/actions/runs/44044131741) runs for `daff0779fdc22101c802c3ad4a7364206169042c` failed before job execution. All 11 failed jobs displayed: "The job was not started because your account is locked due to a billing issue." Their API step arrays were empty. Two other jobs were skipped.
- This is an observed account-level blocker. It provides no evidence of a Host Panel code failure and no assurance that CI would pass after the blocker is resolved. No account changes or manual CI reruns were performed. Run IDs, job IDs, exact annotations, observation routes, and limits are preserved in `evidence/2026-11-17-actions-blockers.json`.

### Repository-wide limits

- `wagents validate --format json` remains blocked by the existing missing `wagents.mcphub.things_contract` import. That module is absent from the pinned tracked source and is outside this change.
- Full strict OpenSpec validation evaluated 53 items: 45 valid, 8 invalid. `host-panel-chatgpt-plugin` is valid with no issues. Unrelated invalid items are `activate-candidate-corpus-runtime-jul2026`, `cursor-harness`, `docs-instructions`, `fleet-hooks-promotion`, `fleet-skill-projection-assurance`, `integrate-mcphub-control-plane`, `public-release-prod-readiness`, and `replace-supathings-with-things-plus-plus`.
- No unrelated source, validator, or requirement was changed to make a global check pass.
