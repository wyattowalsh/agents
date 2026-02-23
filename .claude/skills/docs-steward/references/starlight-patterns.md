# Starlight Component Patterns

Reference for using Starlight components in MDX documentation pages.
Read this file before enhancing any generated MDX content.

All components are imported from `@astrojs/starlight/components`.

---

## Import Convention

Import all needed components in a single import statement at the top
of the MDX file, after the frontmatter closing `---`:

```mdx
---
title: Page Title
description: Page description.
---

import { Aside, Badge, Card, CardGrid, LinkCard, Steps, Tabs, TabItem, FileTree, Code } from '@astrojs/starlight/components';
```

Import only the components you actually use on the page. Do not import
unused components.

---

## Aside

Callout boxes for supplementary information.

### Syntax

```mdx
<Aside type="note">
  Default informational callout.
</Aside>

<Aside type="tip" title="Custom Title">
  Helpful suggestion with a custom heading.
</Aside>

<Aside type="caution">
  Something to be careful about.
</Aside>

<Aside type="danger">
  Critical warning — something that can cause data loss or breakage.
</Aside>
```

### Types

| Type | Use When |
|------|----------|
| `note` | Supplementary information the reader should know |
| `tip` | Helpful suggestion that improves the experience |
| `caution` | Something that could cause unexpected behavior |
| `danger` | Something that can cause data loss, security issues, or breakage |

### When to Use

- Important caveats about a skill or agent behavior
- Compatibility warnings (e.g., "Requires Node 20+")
- Tips for getting better results
- Warnings about destructive operations

### Common Mistakes

- Overusing Aside — more than 3 per page dilutes their impact
- Using `danger` for minor issues (reserve for genuinely dangerous operations)
- Putting primary content in Aside instead of supplementary content
- Missing the closing tag (JSX requires explicit closing)

---

## Badge

Inline status or category indicators.

### Syntax

```mdx
<Badge text="New" variant="tip" />
<Badge text="Deprecated" variant="caution" />
<Badge text="v2.0" variant="note" />
<Badge text="Required" variant="danger" />
<Badge text="Stable" variant="success" />
<Badge text="MIT" variant="default" />
```

### Variants

| Variant | Use When |
|---------|----------|
| `note` | Neutral metadata (version numbers, categories) |
| `tip` | Positive status (new, recommended, featured) |
| `caution` | Warning status (deprecated, experimental, beta) |
| `danger` | Critical status (breaking change, security) |
| `success` | Confirmation (stable, tested, verified) |
| `default` | Generic labels (license, platform) |

### When to Use

- Version indicators next to headings
- Status labels (experimental, stable, deprecated)
- Category tags in overview pages
- License or platform indicators

### Common Mistakes

- Using Badge for long text (keep under 20 characters)
- Using too many variants on one page (pick 2-3 max)
- Placing Badge inside headings (put them after the heading text)

---

## Card and CardGrid

Feature cards arranged in a responsive grid.

### Syntax

```mdx
<CardGrid>
  <Card title="Fast" icon="rocket">
    Built for speed with parallel processing.
  </Card>
  <Card title="Reliable" icon="approve-check">
    Every finding validated with research evidence.
  </Card>
</CardGrid>
```

### Props

- `Card`:
  - `title` (required): Card heading
  - `icon` (optional): Starlight icon name
- `CardGrid`:
  - `stagger` (optional): Offset cards for visual variety

### When to Use

- Feature overviews on landing or index pages
- Comparing multiple options or modes
- Grouping related capabilities
- Asset category overviews

### Common Mistakes

- Using Card for navigation (use LinkCard instead)
- Too many cards in one grid (4-6 is ideal; 8+ becomes a wall)
- Card descriptions that are too long (keep to 1-2 sentences)
- Missing the `title` prop

---

## LinkCard

Clickable card that navigates to another page.

### Syntax

```mdx
<CardGrid>
  <LinkCard
    title="Honest Review"
    href="/skills/honest-review/"
    description="Research-driven code review at multiple abstraction levels."
  />
  <LinkCard
    title="Add Badges"
    href="/skills/add-badges/"
    description="Detect tech stack and generate shields.io badges."
  />
</CardGrid>
```

### Props

- `title` (required): Link text / card heading
- `href` (required): Destination URL (use relative paths for internal links)
- `description` (optional): Brief description below the title

### When to Use

- Cross-references to related skills, agents, or MCP servers
- "See also" sections
- Navigation hubs and index pages
- Prominent links that deserve more visual weight than inline links

### Common Mistakes

- Using absolute URLs for internal links (use relative `/skills/name/`)
- Missing trailing slash on internal links
- Description that duplicates the title
- Using LinkCard for external links without indicating they leave the site

---

## Steps

Numbered step-by-step instructions.

### Syntax

```mdx
<Steps>

1. Install dependencies

   ```bash
   pnpm install
   ```

2. Generate content pages

   ```bash
   uv run wagents docs generate
   ```

3. Start the dev server

   ```bash
   cd docs && pnpm dev
   ```

</Steps>
```

### When to Use

- Installation instructions
- Setup guides
- Sequential workflows (build, test, deploy)
- Any ordered process with distinct steps

### Common Mistakes

- Using Steps for unordered lists (use regular lists instead)
- Steps without blank lines between them (required for MDX parsing)
- Missing the blank line after the opening `<Steps>` tag

---

## Tabs and TabItem

Tabbed content panels for switching between variants.

### Syntax

```mdx
<Tabs>
  <TabItem label="Claude Code">
    ```bash
    /docs-steward sync
    ```
  </TabItem>
  <TabItem label="CLI">
    ```bash
    uv run wagents docs generate
    ```
  </TabItem>
</Tabs>
```

### Props

- `TabItem`:
  - `label` (required): Tab button text
  - `icon` (optional): Starlight icon name

### When to Use

- Configuration for different environments or agents
- Code examples in different languages
- Platform-specific instructions
- Multiple invocation methods for the same task

### Common Mistakes

- Tabs with only one TabItem (just use regular content)
- Tab labels that are too long (keep under 20 characters)
- Missing the `label` prop on TabItem

---

## FileTree

Visual directory structure representation.

### Syntax

```mdx
<FileTree>

- skills/
  - docs-steward/
    - SKILL.md
    - references/
      - quality-checklist.md
      - starlight-patterns.md
  - honest-review/
    - SKILL.md
    - references/
- agents/
- mcp/

</FileTree>
```

### Conventions

- Use `-` for list items (not `*` or numbered)
- Directories end with `/`
- Files have no trailing slash
- Indent with 2 spaces per level
- Add a blank line after `<FileTree>` opening tag

### When to Use

- Showing project or directory structure
- Explaining where files live in the repository
- Installation or setup guides showing expected file layout

### Common Mistakes

- Using numbered lists (FileTree expects unordered `-` lists)
- Forgetting the trailing `/` on directories
- No blank line after the opening tag

---

## Code

Enhanced code blocks with titles and line highlighting.

### Syntax

````mdx
<Code code={`const greeting = "hello";
console.log(greeting);`} lang="js" title="example.js" />
````

For simple code blocks, use standard markdown fenced code blocks instead:

````mdx
```bash title="Install dependencies"
pnpm install
```
````

### Props

- `code` (required): The code string
- `lang` (required): Language identifier for syntax highlighting
- `title` (optional): Filename or label shown above the block
- `mark` (optional): Line numbers or ranges to highlight

### When to Use

- Code snippets that need a filename header
- Dynamic code content assembled from variables
- Highlighted line ranges for teaching
- For simple static code, prefer regular fenced code blocks

### Common Mistakes

- Using `Code` component for simple snippets (use fenced blocks)
- Missing the `lang` prop (no syntax highlighting without it)

---

## Patterns from Recent Enhancement Work

### CardGrid with External Links (Supported Agents)

```mdx
import { CardGrid, LinkCard } from '@astrojs/starlight/components';

## Supported Agents

<CardGrid>
  <LinkCard
    title="Claude Code"
    href="https://docs.anthropic.com/en/docs/claude-code"
    description="Full native support via CLAUDE.md"
  />
  <LinkCard
    title="Gemini CLI"
    href="https://github.com/google-gemini/gemini-cli"
    description="Supported via GEMINI.md bridge file"
  />
</CardGrid>
```

### Aside with Ecosystem Link (Onboarding)

```mdx
import { Aside } from '@astrojs/starlight/components';

<Aside type="tip" title="Install from agentskills.io">
  Browse and install skills from the [agentskills.io](https://agentskills.io) marketplace:
  `npx skills add agentskills.io/skill-name -y`
</Aside>
```

### Steps with External Links (How it Works)

```mdx
import { Steps } from '@astrojs/starlight/components';

<Steps>

1. **Create your asset**

   Use the CLI to scaffold: `wagents new skill my-skill`
   See the [AGENTS.md spec](/guides/agents-md/) for format details.

2. **Generate docs**

   Run `uv run wagents docs generate` to produce MDX pages.
   The [wagents CLI reference](/cli/) documents all options.

3. **Enhance and publish**

   Run `/docs-steward enhance` to improve content quality.

</Steps>
```

### Badge Row for Metadata

```mdx
import { Badge } from '@astrojs/starlight/components';

<Badge text="v2.0" variant="note" />
<Badge text="MIT" variant="default" />
<Badge text="Stable" variant="success" />
<Badge text="Claude Code" variant="tip" />
```

CSS in `custom.css` auto-layouts badge rows with flexbox when badges
are direct children of a paragraph.

### Convention Skills Blockquote

For auto-invoke skills that are hidden from the `/` menu, add a
blockquote after the catalog card wrapper:

```mdx
<div class="catalog-skill">
  <LinkCard title="python-conventions" href="/skills/python-conventions/" description="Python tooling conventions" />
</div>

> Auto-invoke only — loaded automatically when working on Python files.
```

CSS styles `catalog-skill + blockquote` with smaller italic text.

---

## General MDX Patterns

### Escaping Special Characters

MDX treats `{`, `}`, `<`, `>` as JSX. In prose, escape them:

```mdx
Use `{'{'}` to open a block in JSX.
```

Or wrap in backticks:

```mdx
The `<Aside>` component renders a callout.
```

### Combining Components

Components nest naturally. Put Tabs or Aside inside Steps, CardGrid
inside TabItem, etc. Ensure blank lines around each nested component
tag for correct MDX parsing.

### Component Spacing

Always include blank lines around component tags in MDX:

```mdx
Some text.

<Aside type="tip">
  Content inside the aside.
</Aside>

More text after.
```

Without blank lines, MDX may not parse the component correctly.