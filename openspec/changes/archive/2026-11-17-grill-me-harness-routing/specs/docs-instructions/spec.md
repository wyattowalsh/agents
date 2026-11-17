# Docs Instructions Delta

## MODIFIED Requirements

### Requirement: Clarification Gate depth routing

The canonical instruction source SHALL classify assumptions into codebase-resolvable, user-pivotal, independent-choice, and low-stakes-defaultable classes and route user-pivotal plan or design uncertainty to the `/grill-me` interview protocol.

#### Scenario: User-pivotal scope fork

- **GIVEN** an agent faces interdependent scope or approach uncertainty before planning or implementation
- **WHEN** the uncertainty is not answerable from the codebase
- **AND** user judgment would materially change scope, approach, or success criteria
- **THEN** the agent SHALL invoke `/grill-me` (one question at a time with recommended answers)
- **AND** SHALL NOT guess or proceed with batched MCQ alone.

#### Scenario: Independent enum choice

- **GIVEN** an agent faces 1–3 independent choices with clear trade-offs
- **WHEN** the choices are not interdependent
- **THEN** the agent SHALL use batched numbered multiple-choice questions per Clarification Gate
- **AND** SHALL NOT start a full grill-me session.

#### Scenario: Codex or omitted skill body

- **GIVEN** the `/grill-me` skill body is not loaded
- **WHEN** user-pivotal uncertainty requires deep clarification
- **THEN** the agent SHALL follow the embedded grill-me protocol in `instructions/global.md`.

#### Scenario: Mid-wave subtask-pivotal fork

- **GIVEN** orchestrated work is in progress
- **WHEN** a subtask hits uncertainty classified as `subtask-pivotal`
- **THEN** the parent SHALL invoke scoped `/grill-me` on that branch only
- **AND** SHALL NOT skip as a micro-reversible mid-task question
- **AND** SHALL NOT let the subagent guess through the fork.

#### Scenario: blocked-user-pivotal handoff

- **GIVEN** a subagent returns `blocked-user-pivotal` per orchestrator uncertainty handoff
- **WHEN** the parent reconciles the wave
- **THEN** the parent SHALL re-enter the Uncertainty Gate
- **AND** SHALL run scoped `/grill-me` before re-dispatching the affected lane.

#### Scenario: Tier-T with pivotal uncertainty

- **GIVEN** a bounded leaf is otherwise Tier-T eligible
- **WHEN** the leaf has unresolved user-pivotal or subtask-pivotal uncertainty
- **THEN** the parent SHALL NOT dispatch Tier-T
- **AND** SHALL resolve the uncertainty via scoped `/grill-me` first.