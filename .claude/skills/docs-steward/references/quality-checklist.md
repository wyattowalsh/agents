# Documentation Quality Checklist

Use this checklist to score and improve generated documentation pages.
Every enhancement subagent should read this file before modifying content.

---

## Scoring Dimensions

Rate each dimension 1-5. A page scoring 3+ on all dimensions is
acceptable. Target 4+ for high-traffic pages (index, popular skills).

### 1. Description Quality (1-5)

| Score | Criteria |
|-------|----------|
| 1 | Missing or placeholder ("TODO", "Skill instructions go here") |
| 2 | Generic one-liner that could apply to any asset |
| 3 | Accurate but dry — states what it does without context or motivation |
| 4 | Specific and useful — explains what, when, and why to use it |
| 5 | Compelling — immediately communicates value, reads naturally, distinctive |

**Check**:
- Does the description explain what the asset does?
- Does it explain when and why to use it?
- Is it specific to this asset (not copy-paste generic)?
- Is it under 160 characters for SEO meta description purposes?
- Does the expanded body description add detail beyond the frontmatter summary?

### 2. Usage Examples (1-5)

| Score | Criteria |
|-------|----------|
| 1 | No usage information at all |
| 2 | Mentions invocation but no concrete example |
| 3 | One basic example showing primary invocation |
| 4 | Multiple examples covering main use cases with explanation |
| 5 | Comprehensive examples with edge cases, argument patterns, expected output |

**Check**:
- For skills: does it show `/skill-name` invocation and argument patterns?
- For skills: does it show each dispatch mode with an example?
- For agents: does it show how to reference or spawn the agent?
- For MCP servers: does it show connection configuration?
- Are code blocks properly formatted with language hints?
- Do examples include brief explanation of what they do?

### 3. Visual Elements (1-5)

| Score | Criteria |
|-------|----------|
| 1 | Plain text wall, no formatting beyond basic markdown |
| 2 | Headers and lists but no Starlight components |
| 3 | One or two Starlight components used appropriately |
| 4 | Multiple components used where they genuinely improve comprehension |
| 5 | Rich, well-structured page with thoughtful component usage throughout |

**Check**:
- Are `Aside` callouts used for tips, warnings, and important notes?
- Are `Steps` used for sequential instructions?
- Are `Tabs` used where multiple variants exist (modes, configs, platforms)?
- Are `CardGrid` / `Card` used for feature overviews or related items?
- Are `Badge` used for status, version, or category indicators?
- Is `FileTree` used when showing directory structures?
- Are components imported at the top of the MDX file?
- Are components used where they add value, not just for decoration?

### 4. Cross-References (1-5)

| Score | Criteria |
|-------|----------|
| 1 | No links to other pages or assets |
| 2 | Links to one related page but misses obvious connections |
| 3 | Links to directly related assets (skills link to their MCP deps, etc.) |
| 4 | Links to related assets plus related concepts and usage patterns |
| 5 | Comprehensive link network — related assets, concepts, external docs |

**Check**:
- Does a skill page link to MCP servers it uses?
- Does an agent page link to skills it preloads?
- Does a skill page link to agents that use it?
- Are there links to external documentation for dependencies?
- Are `LinkCard` components used for prominent cross-references?
- Do links use descriptive text (not "click here")?

### 5. Structure (1-5)

| Score | Criteria |
|-------|----------|
| 1 | No headings, single block of text |
| 2 | Some headings but illogical hierarchy or missing sections |
| 3 | Correct heading hierarchy, reasonable section organization |
| 4 | Well-organized with logical flow, scannable, good use of whitespace |
| 5 | Optimal structure — easy to scan, find, and read; TOC is useful |

**Check**:
- Is there exactly one h1 (the page title, usually in frontmatter)?
- Do h2 and h3 headings form a logical hierarchy?
- Are sections ordered by importance or natural reading flow?
- Is the page scannable — can a reader find what they need quickly?
- Is there a brief intro before diving into details?
- Are long sections broken into subsections?

### 6. SEO and Discoverability (1-5)

| Score | Criteria |
|-------|----------|
| 1 | No frontmatter description, generic title |
| 2 | Has title and description but they are not search-optimized |
| 3 | Title and description are accurate and contain key terms |
| 4 | Optimized title, description, and headings with natural keyword usage |
| 5 | Full SEO: optimized meta, descriptive headings, structured content |

**Check**:
- Is the frontmatter `description` under 160 characters and descriptive?
- Does the title contain the asset name and type?
- Do headings use descriptive terms (not "Overview" alone)?
- Is content structured so search engines can extract useful snippets?

### 7. Accessibility (1-5)

| Score | Criteria |
|-------|----------|
| 1 | Images without alt text, links without context |
| 2 | Some alt text and link labels but inconsistent |
| 3 | All images have alt text, links are descriptive |
| 4 | Good contrast awareness, semantic markup, no reliance on color alone |
| 5 | Fully accessible — tested structure, clear navigation, inclusive language |

**Check**:
- Do all images have meaningful alt text?
- Are links descriptive (not "here" or raw URLs)?
- Is information conveyed through text, not just color or icons?
- Are code blocks labeled with language for screen readers?
- Is the heading hierarchy navigable?

---

## Overall Score

Sum all dimension scores. Maximum is 35.

| Total | Rating | Action |
|-------|--------|--------|
| 28-35 | Excellent | No changes needed |
| 21-27 | Good | Minor improvements optional |
| 14-20 | Acceptable | Enhance weak dimensions |
| 7-13 | Poor | Needs substantial enhancement |
| < 7 | Critical | Page is essentially placeholder; full rewrite |

---

## Enhancement Priority

When enhancing multiple pages, prioritize:

1. Pages scoring "Critical" or "Poor" overall
2. Pages for assets that changed most recently
3. High-traffic pages (index, popular skills, getting started)
4. Pages with low Description Quality (most visible to users)
5. Pages with low Usage Examples (most impactful for users)

---

## Common Enhancement Patterns

### Expanding a Placeholder Description

Before:
```
TODO — What this skill does and when to use it
```

After:
```
Analyze code for security vulnerabilities, performance issues, and design
flaws using research-validated multi-level review. Use when you need a
thorough, evidence-backed code review — not a quick style check.
```

### Adding Usage Examples

Before:
```
## Usage
Run the skill.
```

After:
```
## Usage

Review changes from the current session:
\`\`\`
/honest-review
\`\`\`

Review a specific file:
\`\`\`
/honest-review src/auth/login.py
\`\`\`

Full codebase audit:
\`\`\`
/honest-review audit
\`\`\`
```

### Adding an Aside Callout

When there is an important caveat or tip, wrap it:

```mdx
import { Aside } from '@astrojs/starlight/components';

<Aside type="tip">
  Run `/docs-steward maintain` periodically to catch stale pages
  and broken links before they accumulate.
</Aside>
```

### Adding Cross-References

When assets are related, link them:

```mdx
import { LinkCard, CardGrid } from '@astrojs/starlight/components';

## Related

<CardGrid>
  <LinkCard title="Honest Review" href="/skills/honest-review/" description="Research-driven code review" />
  <LinkCard title="MCP Creator" href="/skills/mcp-creator/" description="Create new MCP servers" />
</CardGrid>
```
