## Tracked Source Surfaces

| Surface | Change |
| --- | --- |
| `skills/design/SKILL.md` | Renamed and rewritten custom skill contract. |
| `skills/design/references/**` | Existing references moved; new conditional design references added. |
| `skills/design/scripts/**` | Scanner/check scripts moved and extended. |
| `skills/design/evals/**` | Eval manifests renamed from `/frontend-designer` to `/design`. |
| `skills/chrome-devtools*/**` | Folded into `/design` rendered-proof references and removed as active custom skills. |
| `skills/add-badges/`, `.agents/skills/add-badges`, global `shieldcn-badges` mirrors | Badge and ShieldCN workflows folded into `/design` Badge Surface; active wrappers removed or approval-gated for user-local mirrors. |
| `tests/test_design_scan.py` | Focused scanner tests renamed and expanded. |
| `docs/src/skill-research/design.md` | Canonical research and trust matrix for the upgrade. |
| `docs/src/skill-research/{add-badges,shieldcn-badges}.md` | Folded into `design.md` or removed as inactive research pages. |
| `docs/src/skill-research/{chrome-devtools*,baseline-ui,fixing-accessibility,fixing-metadata,design-taste-frontend,emil-design-eng,ui-ux-pro-max,web-design-guidelines,design-md,design-doc-mermaid,design-agent,design-task,react:components,reactcomponents,stitch-loop,stitchgenerate-design,stitch::generate-design,extract-design-system,tailwind-design-system,sleek-design-mobile-apps,shadcn,accessibility,building-native-ui,figma-code-connect,figma-generate-design,figma-implement-design,impeccable,ckm:*}.md` | Folded into `design.md` or removed as inactive research pages. |
| `docs/src/authoring/skills/design.mdx` | Catalog authoring source for custom skill row. |
| `docs/src/authoring/skills/{add-badges,shieldcn-badges}.mdx` | Folded badge rows removed from active catalog authoring. |
| `docs/src/authoring/skills/{chrome-devtools*,baseline-ui,fixing-accessibility,fixing-metadata,design-taste-frontend,emil-design-eng,ui-ux-pro-max,web-design-guidelines,design-md,design-doc-mermaid,design-agent,design-task,react:components,reactcomponents,stitch-loop,stitchgenerate-design,stitch::generate-design,extract-design-system,tailwind-design-system,sleek-design-mobile-apps,shadcn,accessibility,building-native-ui,figma-code-connect,figma-generate-design,figma-implement-design,impeccable,ckm:*}.mdx` | Folded rows removed from active catalog authoring. |
| `config/external-skills.md` | Legacy projection pruned so grouped install commands no longer select folded skills. |
| `wagents/docs.py` | Hardcoded custom catalog feature link updated if still present. |
| Related skill references/data | Handoff references updated from `frontend-designer` to `design`. |
| `openspec/changes/upgrade-design-skill/**` | Public-change control artifacts. |

## Generated Or Derived Surfaces

| Surface | Owner |
| --- | --- |
| `README.md` | `uv run wagents readme`. |
| `docs/src/content/docs/skills/catalog/custom/design.mdx` | `uv run wagents docs generate --no-installed`. |
| `docs/src/content/docs/skills/catalog/custom/add-badges.mdx` | Removed after docs generation if stale. |
| `docs/src/content/docs/skills/catalog/custom/chrome-devtools*.mdx` | Removed after docs generation if stale. |
| `docs/src/content/docs/skills/catalog/external/shieldcn-badges.mdx` | Removed after docs generation if stale. |
| `docs/src/content/docs/skills/catalog/external/{baseline-ui,fixing-accessibility,fixing-metadata,design-taste-frontend,emil-design-eng,ui-ux-pro-max,web-design-guidelines,design-md,design-doc-mermaid,design-agent,design-task,react:components,reactcomponents,stitch-loop,stitchgenerate-design,stitch::generate-design,extract-design-system,tailwind-design-system,sleek-design-mobile-apps,shadcn,accessibility,building-native-ui,figma-code-connect,figma-generate-design,figma-implement-design,impeccable,ckm:*}.mdx` | Removed after docs generation if stale. |
| `docs/src/content/docs/skill-research/design.mdx` | `uv run wagents docs generate --no-installed`. |
| `docs/src/content/docs/skill-research/{add-badges,shieldcn-badges}.mdx` | Removed after docs generation if stale. |
| `docs/src/content/docs/skill-research/{chrome-devtools*,baseline-ui,fixing-accessibility,fixing-metadata,design-taste-frontend,emil-design-eng,ui-ux-pro-max,web-design-guidelines,design-md,design-doc-mermaid,design-agent,design-task,react:components,reactcomponents,stitch-loop,stitchgenerate-design,stitch::generate-design,extract-design-system,tailwind-design-system,sleek-design-mobile-apps,shadcn,accessibility,building-native-ui,figma-code-connect,figma-generate-design,figma-implement-design,impeccable,ckm:*}.mdx` | Removed after docs generation if stale. |
| `docs/public/generated-registries/skills-catalog-index.json` | `uv run wagents docs generate --no-installed`. |
| `docs/public/generated-skill-indexes/install-scripts.json` | Docs/catalog generation. |
| `docs/src/generated-site-data.mjs` | Docs/catalog generation. |
| `docs/src/generated-skill-research-index.mjs` | Docs research generation. |
| `docs/src/generated-sidebar.mjs` | Docs generation. |

## Explicitly Avoided Surfaces

Do not commit local installed skill state, live harness install output, generated
downstream OpenSpec artifacts, vendored third-party skill copies, MCP registry
or harness config mutation, or unrelated review-consolidation changes.
