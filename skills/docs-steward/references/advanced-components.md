# Advanced Components

## 1. Usage Goal

Use this reference during `sync` and `enhance` modes to select framework-native patterns for diagrams, code examples, tables, embeds, and callouts.

Prefer components that improve comprehension. Do not add visual components only to make a page look richer.

## 2. Selection Rubric

Use the simplest component that preserves meaning:

1. If prose is enough, keep prose.
2. If sequence, dependency, or architecture relationships matter, use Mermaid with a text fallback.
3. If readers need commands or source examples, use language-labeled code blocks and keep commands copyable.
4. If readers compare options, use a table with short labels and explicit trade-offs.
5. If content is optional or lengthy, use tabs/details only when the framework supports accessible disclosure patterns.

## 3. Framework Pattern Matrix

| Framework | Mermaid | Codeblocks | Tables | Embeds | Safe Fallback |
|-----------|---------|------------|--------|--------|---------------|
| Astro + Starlight | Starlight Expressive Code + Mermaid integration if configured | Expressive Code with filename/title metadata | Markdown tables; Starlight cards for landing pages | Starlight cards, asides, file-tree components | Plain fenced code and markdown tables |
| Docusaurus | MDX Mermaid plugin or fenced Mermaid when enabled | Prism codeblocks with title metadata | Markdown/MDX tables | Admonitions, tabs, cards | Markdown admonitions and links |
| Fumadocs | MDX components from app docs layer | Shiki/Twoslash when project uses it | Markdown/MDX tables | Cards, Steps, Callout components | Plain markdown and heading hierarchy |
| Sphinx | `sphinxcontrib-mermaid` when present | `literalinclude`, code-block directives | list-table or CSV table directives | admonitions, panels, tabs if configured | reStructuredText code-block and simple tables |
| MkDocs | Material Mermaid support when enabled | pymdownx SuperFences and highlight | Markdown tables, attr lists | admonitions, tabs, cards | Standard markdown with links |

## 4. Diagram Rules

- Add Mermaid only when it clarifies relationships, sequencing, or flow.
- Keep diagrams small enough to read without horizontal scrolling.
- Provide adjacent prose that states the same decision or flow in plain language.
- Use stable labels from the page, codebase, or product vocabulary; do not invent new domain terms.
- Avoid diagrams for checklists, changelogs, or simple linear procedures.

## 5. Code Example Rules

- Always label language identifiers: `bash`, `json`, `yaml`, `python`, `ts`, `tsx`, `md`.
- Prefer commands that run from the documented working directory.
- Avoid hiding critical setup steps inside tabs or collapsed blocks.
- Include filenames when the framework has a native filename/title convention.
- Keep generated snippets source-grounded; if exact code is unavailable, say what must be verified.

## 6. Table Rules

- Use tables for comparison matrices, routing rules, command contracts, and support status.
- Keep cells short. Move long rationale below the table.
- Include negative boundaries in the same table when it prevents misuse.
- Avoid tables on narrow mobile layouts if each row needs paragraph-length content.

## 7. Callouts And Admonitions

- Use callouts for warnings, prerequisites, irreversible actions, and validation gates.
- Keep the callout type aligned with severity: note, tip, warning, danger.
- Do not stack more than two callouts in a row; convert the rest to prose or checklist items.
- Include the action a reader should take, not just a warning label.

## 8. Accessibility And Safety Baseline

- Every diagram needs plain-language context before or after it.
- Every embed needs a title and a text-link fallback.
- Code blocks need language labels and should remain copyable.
- Tabs must not be the only place critical instructions appear.
- Color must not be the only signal for status, diff, or severity.
- Generated docs must preserve heading order and avoid skipped heading levels.

## 9. Verification Checklist

Before finishing an enhancement:

1. Confirm each component is supported by the detected framework and configured plugins.
2. Confirm safe markdown fallbacks for unsupported frameworks.
3. Run the framework build or preview check when the page changed.
4. Scan for broken MDX/directive syntax introduced by components.
5. Confirm mobile readability for tables, cards, and diagrams where practical.
6. Confirm component additions did not fabricate product behavior or API details.

## 10. Anti-Patterns

- Decorative Mermaid diagrams that restate a two-step process.
- Tabs that hide the only working install command.
- Admonitions used as section headings.
- Framework-specific components in shared markdown without fallback.
- Copied examples with stale package names, ports, or file paths.
- Screenshots or embeds without textual equivalents.
