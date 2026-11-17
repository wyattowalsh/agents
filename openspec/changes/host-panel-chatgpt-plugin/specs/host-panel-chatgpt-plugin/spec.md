## ADDED Requirements

### Requirement: Canonical narrow plugin projection

The exporter SHALL derive the plugin from the versionless metadata template, canonical `skills/host-panel/SKILL.md`, and flat `references/*.md` files only. It SHALL preserve Markdown bytes and inject release version only into archived root `plugin.json`.

#### Scenario: Export a release

- **WHEN** valid canonical inputs and a valid SemVer release identity are supplied
- **THEN** the archive contains the manifest and canonical Markdown files, without parser scripts, evaluations, other skills, MCP settings, apps, dependencies, or policy configuration
- **AND** the template and canonical instruction files remain unchanged

### Requirement: Natural and contextual invocation

The skill SHALL accept an unambiguous natural-language or current-conversation panel request while retaining the documented slash invocation where the runtime supports it. It SHALL request clarification only when topic or scope is materially unresolved.

#### Scenario: Panel a preceding proposal

- **WHEN** the user requests a panel on an unambiguous proposal in the current conversation
- **THEN** the skill uses that proposal without demanding quotation marks or inventing another topic

### Requirement: Truthful execution description

The skill SHALL identify single-context perspectives as simulated perspectives. It SHALL claim separate peer-blind initial calls only when actual tools performed those calls with peer outputs withheld. Separate calls SHALL NOT be described as statistical independence or multiple model providers without supporting runtime evidence.

#### Scenario: No worker capability

- **WHEN** the host can load the skill but has no separate-worker tool
- **THEN** it can conduct a panel as single-context perspective simulation without claiming spawned agents or independent judgments

### Requirement: Claim-level evidence and supported synthesis

The skill SHALL distinguish supported factual claims, inferences, value judgments, and evidence gaps. It SHALL preserve source lineage and report mixed coverage without implying that an inspected source validates the whole panel.

#### Scenario: Added evidence changes a crux

- **WHEN** a new source changes support for a material claim
- **THEN** the panel identifies the affected claim and updates its synthesis explicitly while preserving unresolved gaps

### Requirement: Preserve legitimate formats and convergence checks

The skill SHALL retain roundtable, Oxford, and Socratic formats with distinct phases. It SHALL reject false balance and empirical claims about real human opinion from simulated participants. It SHALL test convergence against evidence and omitted assumptions without manufacturing dissent.

#### Scenario: Supported agreement

- **WHEN** the perspectives converge and the strongest relevant counterevidence does not overturn their supported conclusion
- **THEN** the synthesis may retain that agreement without adding a fictional opposing position

### Requirement: User control over panel progression

The skill SHALL complete normal panels with synthesis while honoring explicit pause, stop, and end instructions. A pause SHALL preserve conversational state without advancing the panel, and an explicit stop SHALL NOT force an additional phase or unwanted synthesis.

#### Scenario: User pauses an interactive panel

- **WHEN** the user asks to pause before the next phase
- **THEN** the skill stops advancing and retains the current topic, phase, claims, and cruxes for a possible later resumption

### Requirement: Deterministic and bounded archive output

The exporter SHALL reject existing outputs, output paths within the source repository, source or output symlinks, invalid release identity, unsafe member names, and local Markdown links that escape or target missing package members. Identical input bytes and release identity SHALL produce identical archive bytes in the same runtime.

#### Scenario: Attempt to overwrite an archive

- **WHEN** the requested output already exists
- **THEN** the exporter fails without replacing or modifying that output

#### Scenario: Missing local reference

- **WHEN** a Markdown link names a local file that is not included in the narrow package
- **THEN** the exporter fails before creating the output archive
