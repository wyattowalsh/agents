# Affected Surfaces

## Canonical Sources

| Path | Purpose |
| --- | --- |
| `skills/host-panel/SKILL.md` | Chat invocation, capability-aware execution, evidence and interaction contract |
| `skills/host-panel/references/*.md` | Detailed grounding, formats, moderation, synthesis, and interaction rules |
| `skills/host-panel/evals/evals.json` | Retained scenarios plus Chat, evidence, continuation, and interruption cases |
| `skills/host-panel/evals/runs/2026-11-17-chat-baseline.json` | Observed controlled trial responses and explicit limits; not an installed-session benchmark |
| `config/plugins/host-panel.json` | Versionless portable plugin metadata; no MCP, app, dependency, or policy configuration |
| `scripts/build_host_panel_plugin.py` | Narrow, deterministic release ZIP exporter |
| `tests/test_host_panel_plugin.py` | Exporter behavior, source preservation, input/output boundaries, and reproducibility |
| `openspec/changes/host-panel-chatgpt-plugin/` | Change design, preservation mapping, tasks, requirement delta, and verification record |

## Generated And External Surfaces

| Surface | Treatment |
| --- | --- |
| `docs/src/authoring/skills/host-panel.mdx` | Refresh the generated custom-skill body using the repository's authoring sync |
| `docs/src/content/docs/skills/catalog/custom/host-panel.mdx` | Regenerate; do not hand-edit derived content |
| `docs/public/generated-registries/skills-catalog-index.json` and related catalog outputs | Regenerate only through the owning docs tool |
| `README.md` | Regenerate if the canonical skill description changes |
| A new ZIP outside the repository | Generated release artifact containing root `plugin.json` and only the canonical skill entrypoint plus flat Markdown references |
| Installed ChatGPT plugin and fresh Chat sessions | Separate runtime acceptance evidence; source tests do not establish installation or mode coverage |

## Preserved Surfaces

The existing `skills/host-panel/scripts/parse_args.py`, bundled toolkit, and source evaluation files remain repository assets; they are excluded from the narrow Chat plugin. Other skills, agent definitions, root bundle manifests, MCP settings, harness projections, and unrelated distribution tests are not changed to make this package pass.
