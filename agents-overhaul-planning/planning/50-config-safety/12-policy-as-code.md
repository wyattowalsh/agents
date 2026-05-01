# Policy as Code

## Objective

Turn safety and support-tier rules into executable checks.

## Candidate policy engines

- JSON Schema/Pydantic for structural validation.
- OPA/Rego or Cedar for more expressive policy checks if needed.
- Built-in Python policy layer for simple repo-local rules.

## Initial policies

```text
Deny validated MCP with @latest.
Deny validated MCP with absolute local command path.
Deny external skill without provenance.
Deny generated docs drift.
Deny README support claim exceeding harness registry tier.
Deny skill script with no dry-run when it mutates files.
Deny MCP HTTP transport without auth/origin review notes.
```

## Acceptance criteria

- Policies can run locally and in CI.
- Policy failures include remediation hints.
- Policy exceptions require owner, expiry, and rationale.
