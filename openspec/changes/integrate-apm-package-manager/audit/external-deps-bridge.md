# EXT-PHASE1: Catalog Index Entries → apm.yml `dependencies.apm` Mapping (with --skill subsets)

**Phase**: EXT-PHASE1 (external/curated dependency bridge, docs + catalog only; no runtime change in Wave 5).
**Goal**: Document the mechanical + semantic mapping so that curated external skills (today expressed via `npx skills add` in `config/external-skills.md` and materialized in `docs/public/generated-registries/skills-catalog-index.json`) can be equivalently declared for consumers using Microsoft APM.

**Non-goal (this phase)**: Actually emit `apm.yml` from the repo, change `wagents skills sync`, or alter sync-manifest. This is a planning/bridge document. Implementation would follow in later waves after facade + doctor support.

## Source Artifacts (Current)
- Human source: `config/external-skills.md` — lists `npx skills add <sourceRoot> --skill <s1> --skill <s2> ... -y -g -a <harnesses>`
- Generated catalog: `docs/public/generated-registries/skills-catalog-index.json`
  - Each entry has:
    - `name`: skill slug (leaf)
    - `sourceRoot`: e.g. `"vercel-labs/agent-skills"` or `"coreyhaines31/marketingskills"`
    - `installSource`: same or git-ref form
    - `installCommand`: full npx string with multiple `--skill`
    - `selectorMode`: `"named"` | (others)
    - `sourceKind` / `sourceType`: `"curated-external"`
    - `targetAgents`: list of harness ids (antigravity, claude-code, ..., grok, opencode, ...)
    - `provenanceEvidence`, `trustTier`, `status` etc.
- Authoring mdx: `docs/src/authoring/skills/<slug>.mdx` (some are per-skill excerpts for catalog pages)

Individual entries often belong to *collections* from one sourceRoot (e.g. 6 marketing skills from one package).

## Target Form (APM)
From APM:
- `apm.yml` (shipped in consumer projects):
  ```yaml
  name: consumer-project
  version: 1.0.0
  dependencies:
    apm:
      - microsoft/apm-sample-package#v1.0.0
      - git: vercel-labs/agent-skills
        # persisted subset for skill-collection layout
        skills:
          - vercel-react-best-practices
          - vercel-composition-patterns
      # or shorthand when no subset (whole package or single-skill layout)
      - anthropics/skills/skills/frontend-design
    mcp: []
  ```
- CLI that populates it:
  ```
  apm install vercel-labs/agent-skills --skill vercel-react-best-practices --skill vercel-composition-patterns
  # results in the skills: list above; subsequent `apm install` is deterministic
  ```
- For single primitive: just the ref (APM treats as collection-of-1 or hybrid).
- `--skill '*'` resets to all.
- The `skills:` key under the dep item is the persisted `--skill` subset (see package-types for "Skill collection (skills/<name>/SKILL.md)").

APM also records in `apm.lock.yaml` under `skill_subset`.

## Mapping Rules (EXT-PHASE1)

### 1. Source Identifier
- Current: `sourceRoot` or first token after `npx skills add ` (e.g. `vercel-labs/agent-skills`, `PaulRBerg/agent-skills@d3f5540...`)
- APM form:
  - Prefer `owner/repo` (APM resolves default branch or tag).
  - Pin with `#ref` or `@marketplace` when the npx used a commit (e.g. `PaulRBerg/agent-skills@d3f5540ed2fc0fa07f802bd925e06b9387cbe90f` → `PaulRBerg/agent-skills#d3f5540ed2fc0fa07f802bd925e06b9387cbe90f` or git form).
  - Full git urls if non-github.
  - From catalog: use `installSource` or derive from `sourceUrl`.

### 2. Skill Subset (named selectors)
- When `selectorMode == "named"` and installCommand contains N `--skill X`:
  - Map to:
    ```yaml
    - git: <sourceRoot>
      skills:
        - X
        - Y
        ...
    ```
  - Example (from catalog + external-skills):
    npx ... vercel-labs/agent-skills --skill vercel-react-best-practices --skill vercel-composition-patterns ...
    →
    - git: vercel-labs/agent-skills
      skills:
        - vercel-react-best-practices
        - vercel-composition-patterns
- Single-skill installs (or whole-bundle) may omit `skills:` list or use one entry.
- Whole-bundle (no `--skill` or `--skill '*'`): plain string or git entry without `skills`.

### 3. Harnesses / Targets
- Current: explicit `-a antigravity claude-code ... grok opencode` in every command (or per entry `targetAgents`).
- APM:
  - During `apm install` use `--target <name>` (one or more). Once any harness marker exists (`.github/`, `.claude/`, `.cursor/`, `.opencode/` etc.) APM auto-detects.
  - In `apm.yml` top level (optional):
    ```yaml
    targets:
      - copilot
      - claude
      # ...
    ```
  - Not all current targets have 1:1 APM names; mapping examples:
    | Catalog target     | APM --target / compile -t |
    |--------------------|---------------------------|
    | github-copilot     | copilot                   |
    | claude-code        | claude                    |
    | codex              | codex                     |
    | cursor             | cursor                    |
    | gemini-cli         | gemini                    |
    | opencode           | opencode                  |
    | antigravity        | (via claude? or custom)   |
    | grok               | (no first-class; falls back to repo sync + claude adapter skills) |
    | crush              | (no first-class)          |
  - **Grok/Crush note**: Catalog entries will continue recommending the npx + wagents path (or dual) for Grok/Crush consumers. APM install would cover the overlapping harnesses; Grok mirroring of installed skills remains a wagents concern.

### 4. Other Flags
- `-y` (yes) → non-interactive; APM install is non-interactive by default in scripts/CI.
- `-g` (global?) → irrelevant; APM is project-local by design (writes to consumer tree).
- Trust / curated: remains in catalog + external-skills.md + policy; APM has its own `apm-policy.yml` + `apm audit --ci` for governance (complementary, not replacement).

### 5. Example Roundtrip

Catalog entry excerpt (simplified):
```json
{
  "name": "vercel-react-best-practices",
  "sourceRoot": "vercel-labs/agent-skills",
  "installCommand": "npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices --skill vercel-composition-patterns --skill ... -y -g -a ...",
  "selectorMode": "named",
  ...
}
```

Corresponding consumer `apm.yml` fragment (EXT bridge):
```yaml
dependencies:
  apm:
    - git: vercel-labs/agent-skills
      skills:
        - vercel-react-best-practices
        - vercel-composition-patterns
        # ... (the other named ones from that source in the row)
```

Consumer runs:
```
apm install
# or explicitly:
apm install vercel-labs/agent-skills --skill vercel-react-best-practices --skill vercel-composition-patterns
```

APM writes the subset back into consumer's `apm.yml` on first `--skill` use.

## Special Cases
- **Pinned commits in npx** (e.g. `@d3f5540...`): translate to git ref pin. APM lockfile will further pin resolved commit + content hash.
- **Multi-source in one md block**: each `npx skills add` line is independent; one sourceRoot may appear in multiple catalog rows (different skill subsets or trust tiers).
- **"install-now-after-trust-gate"** vs always: this status stays in catalog metadata; APM consumer decides when to add the dep.
- **Local repo skills** (`skills/` at root of wyattowalsh/agents): **never** expressed as APM dep for self. This bundle uses its own `agent-bundle.json` + wagents. (See AGENTS.md.)
- **MCP from externals**: if a curated source later ships MCP, map to `dependencies.mcp` entries (separate from skills). Repo MCPHub stays authoritative for this bundle's MCP.
- **Plugins / full packages**: some sources are plugin collections → map to bare APM dep (APM handles plugin.json layout).

## Implementation Sketch (Future Phases)
1. Add `apm` equivalent examples in external-skills.md and/or mdx (non-breaking, dual).
2. Extend catalog generator (`wagents docs generate` or compose) to emit optional `apmInstall` or structured `apmDep` field on index entries.
3. `wagents apm` facade (thin wrapper) that can `apm install <catalog-entry> --skill ...` while applying repo policy/trust.
4. Optional: generate a sample `examples/apm.yml` or `apm/` recipe from the external list for adopters.
5. Doctor: detect `apm` + suggest for remotes; keep wagents path primary for Grok/Crush + MCPHub.
6. Validation: ensure catalog provenance still references audited npx (or add APM variant) commands.

## Verification (Current)
- `uv run wagents validate`
- Inspect: `jq '.allSkillIndex[] | select(.sourceRoot=="vercel-labs/agent-skills") | {name,sourceRoot,installCommand}' docs/public/generated-registries/skills-catalog-index.json | head`
- Cross-check against `config/external-skills.md`
- APM side: `apm --help`, `apm install --help` (once installed); see package-types for `skills:` persistence.

## Open Questions / Follow-ups
- Exact APM syntax for non-git (marketplace aliases like `foo@awesome-copilot`).
- How APM resolves "skills/" layout vs ".apm/" for the many third-party sources we list.
- Whether to track installed APM packages in repo drift or keep purely consumer-side.
- Grok/Crush bridging: perhaps via post-APM step that copies from `.agents/skills` into `~/.grok/skills` using existing wagents logic.

**Status**: Documented for Wave 5 analysis. Ready for EXT-PHASE1 catalog/docs updates.
