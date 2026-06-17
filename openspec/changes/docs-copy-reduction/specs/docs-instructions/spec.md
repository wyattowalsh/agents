## MODIFIED Requirements

### Docs page density

Generated skill, agent, and MCP catalog pages SHALL default to `summary` density unless `docs-density: standard` is set in source frontmatter.

Summary density SHALL:

- omit duplicated inline sections when full source disclosure exists in collapsed details
- move metadata tables into collapsed details blocks
- emit compact provenance one-liners instead of source Asides
- cap research prose sections

### Docs verbosity lint

The `wagents docs lint` command SHALL scan committed MDX under `docs/src/content/docs/` for forbidden boilerplate, duplicate headings above/below SKILL disclosures, and soft line caps.

CI SHALL run `wagents docs lint` in warn mode (non-blocking) after `wagents docs generate`.

A committed baseline manifest at `planning/manifests/docs-verbosity-baseline.json` SHALL record per-page line counts for regression comparison.
