# hooks-deny-transport Spec Delta

## ADDED Requirements

### Requirement: Deny Cursor attribution trailers on git commit
The system SHALL deny shell `git commit` commands that embed Cursor agent attribution trailers including `Co-authored-by` with Cursor, `Made-with: Cursor`, and `Generated-by`/`Signed-off-by` with Cursor.

#### Scenario: Co-authored-by Cursor denied
- **WHEN** an agent issues `git commit` with a `Co-authored-by` trailer naming Cursor
- **THEN** the git-commit-push-guard policy denies the command with a never-sign reason

#### Scenario: Clean commit allowed
- **WHEN** an agent issues `git commit -m "fix: x"` without attribution trailers
- **THEN** the policy does not deny solely for attribution
