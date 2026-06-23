# Skills Lifecycle Delta

## MODIFIED Requirements

### Requirement: Skills-first lifecycle

The skills lifecycle lane SHALL treat Agent Skills as the default portable
capability model and require script conformance, provenance, security posture,
behavioral-evidence planning, runtime compatibility, and validation before
promotion.

#### Scenario: Skill-creator creates or improves a meaningful skill

- **GIVEN** `/skill-creator` is asked to create a new skill or materially
  improve an existing skill
- **WHEN** it prepares the implementation plan
- **THEN** it SHALL identify source evidence, trigger surface, eval plan,
  security posture, runtime matrix, and baseline
- **AND** it SHALL mark unsupported generic workflow content as
  `needs-evidence` rather than presenting it as grounded.

#### Scenario: Skill-creator evaluates behavioral claims

- **GIVEN** a skill change claims improved behavior, trigger quality, safety, or
  output quality
- **WHEN** `/skill-creator` plans verification
- **THEN** it SHALL define a with-skill versus without-skill baseline for new
  skills or old-skill versus new-skill baseline for existing skill changes
- **AND** it SHALL keep live behavioral eval execution opt-in and non-default.

#### Scenario: Skill-creator audits executable supply-chain surfaces

- **GIVEN** a skill contains scripts, hooks, templates, body substitutions,
  runtime-specific tool controls, remote sources, install commands, destructive
  writes, network behavior, or credential handling
- **WHEN** `/skill-creator audit <skill> --security` runs or equivalent
  security review is required
- **THEN** it SHALL inventory those surfaces, report risk tier and blockers, and
  refuse to install, execute, or modify the audited skill in security-audit mode
- **AND** blocking security-governance findings SHALL prevent release or
  endorsement until resolved or explicitly accepted by the maintainer.

#### Scenario: Skill-creator validates frontmatter command portability

- **GIVEN** a skill frontmatter command string references repo-root skill paths
  such as `skills/<name>/...`, workspace tokens such as `{repo_root}` or
  `${workspaceFolder}`, or machine-local absolute paths
- **WHEN** `/skill-creator package <skill> --dry-run` or the audit portability
  dimension evaluates the skill
- **THEN** the package check SHALL report `frontmatter_commands_portable` as a
  failure
- **AND** the audit portability dimension SHALL record a portability finding or
  reduced portability score.

#### Scenario: Skill-creator separates portable source from hook projection

- **GIVEN** a repo-managed hook command requires source-repository paths or a
  target harness settings surface
- **WHEN** the skill is prepared for portable packaging
- **THEN** the command SHALL live in runtime projection config rather than
  portable `SKILL.md` frontmatter
- **AND** the skill body MAY document the validation behavior and manual
  fallback without making the portable package depend on that hook command.

#### Scenario: Skill-creator plans parallel work

- **GIVEN** a repo-wide or multi-skill improvement is requested
- **WHEN** `/skill-creator` proposes parallel execution
- **THEN** each worker lane SHALL declare owned paths/resources, dependencies,
  locks, artifacts, validation commands, handoff criteria, and judge criteria
- **AND** same-file edits, generated docs, OpenSpec, hooks, validators, and
  public workflow/schema changes SHALL serialize behind an arbiter lane.
