# SARIF Output Format

Generate SARIF v2.1 (Static Analysis Results Interchange Format) for CI tooling interop.
Use when `$ARGUMENTS` includes `--format sarif` or `REVIEW_FORMAT=sarif`.

## Contents

- [SARIF Mapping](#sarif-mapping)
- [Example Document](#example-document)
- [GitHub Code Scanning Upload](#github-code-scanning-upload)
- [VS Code Integration](#vs-code-integration)

## SARIF Mapping

| RV Finding Field                        | SARIF Field                              | Notes                                                  |
| --------------------------------------- | ---------------------------------------- | ------------------------------------------------------ |
| `id` (RV-S-001)                         | `results[].ruleId`                       | Rule ID for grouping                                   |
| `priority` (P0-P3)                      | `results[].level`                        | P0/S0→error, P1/S1→warning, P2+→note                   |
| `location` (file:line)                  | `results[].locations[].physicalLocation` | Split into `artifactLocation.uri` + `region.startLine` |
| `description`                           | `results[].message.text`                 | Plain text finding description                         |
| `confidence` (0.0-1.0)                  | `results[].rank`                         | Scaled 0-100 (confidence × 100)                        |
| `evidence`                              | `results[].message.markdown`             | Markdown with citations                                |
| `level` (Correctness/Design/Efficiency) | `results[].taxa[].name`                  | Custom taxonomy                                        |
| `fix`                                   | `results[].fixes[].description.text`     | Suggested remediation                                  |
| `effort` (S/M/L)                        | `results[].properties.effort`            | Property bag extension                                 |

**Level mapping:**

| RV Priority    | SARIF Level |
| -------------- | ----------- |
| P0, S0         | `error`     |
| P1, S1         | `warning`   |
| P2, S2, P3, S3 | `note`      |

## Example Document

```json
{
  "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/main/sarif-2.1/schema/sarif-schema-2.1.0.json",
  "version": "2.1.0",
  "runs": [
    {
      "tool": {
        "driver": {
          "name": "review",
          "version": "4.0",
          "informationUri": "https://github.com/wyattowalsh/agents",
          "rules": [
            {
              "id": "RV-S-001",
              "shortDescription": { "text": "Missing token expiry validation" },
              "defaultConfiguration": { "level": "error" },
              "properties": { "priority": "P0", "review-level": "Correctness" }
            }
          ]
        }
      },
      "results": [
        {
          "ruleId": "RV-S-001",
          "level": "error",
          "message": {
            "text": "Missing token expiry validation",
            "markdown": "**Evidence:** RFC 6749 Section 5.1 requires token expiry checks."
          },
          "locations": [
            {
              "physicalLocation": {
                "artifactLocation": { "uri": "src/auth.py" },
                "region": { "startLine": 45 }
              }
            }
          ],
          "rank": 85.0,
          "fixes": [
            {
              "description": {
                "text": "Add expiry validation before token acceptance"
              }
            }
          ],
          "properties": { "effort": "S", "confidence": 0.85 }
        }
      ]
    }
  ]
}
```

## GitHub Code Scanning Upload

Upload SARIF results to GitHub Code Scanning for inline PR annotations:

```bash
# Generate SARIF from findings JSON
cat findings.json | uv run python skills/review/scripts/finding-formatter.py --format sarif > results.sarif

# Validate locally via script
uv run python skills/review/scripts/sarif-uploader.py --input results.sarif

# Upload only after explicit publish approval
uv run python skills/review/scripts/sarif-uploader.py \
  --input results.sarif \
  --upload \
  --commit "$(git rev-parse HEAD)" \
  --ref "refs/heads/$(git branch --show-current)"
```

GitHub Actions integration — add after the review step:

```yaml
- name: Upload SARIF
  if: always()
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: results.sarif
    category: review
```

## VS Code Integration

SARIF files render natively in VS Code with the [SARIF Viewer extension](https://marketplace.visualstudio.com/items?itemName=MS-SarifVSCode.sarif-viewer). Findings appear as inline diagnostics with severity coloring.

Save `results.sarif` to the project root and open in VS Code — findings map to source locations automatically.

Cross-references: skills/review/scripts/finding-formatter.py (--format sarif), skills/review/scripts/sarif-uploader.py, references/ci-integration.md.
