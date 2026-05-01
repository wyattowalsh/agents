# multiagent-ui-patterns Specification

## Purpose
Define reusable multiagent UI and interaction patterns for presenting delegated work, review state, and orchestration evidence consistently.
## Requirements
### Requirement: UI pattern extraction without dependency adoption

The multiagent UI patterns lane SHALL extract dashboard, kanban, TUI, and control-plane patterns without adopting runtime dependencies by default.

#### Scenario: External UI repo has useful pattern

- **GIVEN** an external UI repo is relevant
- **WHEN** the lane records its value
- **THEN** it records a pattern and risk note rather than vendoring code.
