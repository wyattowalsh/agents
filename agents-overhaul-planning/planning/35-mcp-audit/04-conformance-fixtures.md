# MCP Conformance Fixtures

## Fixture categories

```text
tests/fixtures/mcp/
  valid-stdio-npx.json
  valid-stdio-uvx.json
  valid-streamable-http.json
  invalid-absolute-path.json
  invalid-latest-in-validated-profile.json
  invalid-secret-in-args.json
  duplicate-search-providers.json
  reasoning-mcp-replacement-required.json
```

## Expected checks

- schema validation;
- install style classification;
- transport classification;
- auth model classification;
- support tier compatibility;
- replacement decision required;
- scan result required for promotion;
- docs link required for user-facing setup.
