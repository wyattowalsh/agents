# shadcn/ui Patterns

> Targets shadcn CLI 3.x with Radix UI unified package. Verify exact APIs via Context7 before relying on bundled specs.

CLI commands, component architecture, registry system, RTL support, theming, and Radix primitive mapping.

---

## 1. CLI Commands

All commands use `npx shadcn@latest <command>`. The CLI reads `components.json` for project configuration.

| Command | Syntax | Purpose |
|---------|--------|---------|
| `init` | `shadcn init [components...] [-d] [-f] [-y] [--rtl]` | Initialize project, generate `components.json`, optionally install components |
| `add` | `shadcn add [components...] [-y] [-o] [-p <path>]` | Install components, blocks, themes, or registry items into project |
| `diff` | `shadcn diff [component]` | Compare local components against registry for upstream updates |
| `list` | `shadcn list` | List all available components from configured registry |
| `build` | `shadcn build` | Build a custom registry from local definitions |
| `migrate rtl` | `shadcn migrate rtl [path\|glob]` | Transform components to use logical CSS properties for RTL |

Install from remote registries with namespaced syntax: `npx shadcn add @<registry>/<component>`.

### `components.json` Configuration

```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "new-york",
  "rsc": true,
  "tsx": true,
  "rtl": false,
  "tailwind": {
    "config": "",
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true
  },
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "iconLibrary": "lucide"
}
```

| Key | Purpose |
|-----|---------|
| `style` | Visual preset (`default`, `new-york`, or custom) |
| `rsc` | Enable React Server Components support |
| `rtl` | Enable RTL logical class transformation on install |
| `tailwind.config` | Path to `tailwind.config.js` (leave blank for Tailwind v4 CSS-first) |
| `tailwind.cssVariables` | Use CSS custom properties (`true`) or Tailwind utility classes (`false`) |
| `aliases.ui` | Where the CLI places UI component files |

---

## 2. Component Architecture

**Copy-paste model:** Components live in YOUR project (`src/components/ui/`), not `node_modules`. The CLI copies source files directly into your codebase. Full ownership, no version lock-in, no abstraction penalty, git-tracked.

**Radix accessibility layer:** Interactive components wrap Radix UI primitives providing behavior (focus trapping, keyboard nav, open/close state), accessibility (ARIA roles, attributes), and DOM structure (portals, composition) with zero styling. shadcn/ui adds Tailwind classes, CSS variable references, and variant props via `class-variance-authority` (cva).

**Customization:** Edit component files directly. Add variants by extending cva definitions:

```tsx
const buttonVariants = cva(
  "inline-flex items-center justify-center rounded-md text-sm font-medium",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent",
        ghost: "hover:bg-accent hover:text-accent-foreground",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
)
```

---

## 3. Registry System

A registry is a distribution endpoint serving JSON definitions of components. The CLI fetches metadata, dependencies, and source files.

**Structure:** Serve `registry.json` at the root URL with item definitions. Each item has a `registry-item.json` conforming to `https://ui.shadcn.com/schema/registry-item.json`.

```json
{
  "name": "my-registry",
  "homepage": "https://my-registry.example.com",
  "items": [
    { "name": "fancy-card", "type": "registry:ui" },
    { "name": "data-grid", "type": "registry:ui" }
  ]
}
```

**Remote registries:** Reference items by URL in `registryDependencies`. The CLI resolves remote dependencies automatically:

```json
{ "registryDependencies": ["button", "https://example.com/r/custom-widget.json"] }
```

**Namespaced components:** `npx shadcn add @acme/fancy-table` installs from community registries.

**Custom registry creation:** Use the [registry template](https://github.com/shadcn-ui/registry-template), define `registry.json`, serve item JSON files, build with `npx shadcn@latest build`.

---

## 4. RTL Support

The CLI transforms classes **at install time**, converting physical positioning to logical equivalents. Zero runtime overhead for LTR-only projects.

- **New projects:** `npx shadcn@latest init --rtl` or set `"rtl": true` in `components.json`
- **Existing projects:** `npx shadcn@latest migrate rtl`

### Physical-to-Logical Class Conversions

| Physical | Logical | Physical | Logical |
|----------|---------|----------|---------|
| `left-*` | `start-*` | `right-*` | `end-*` |
| `ml-*` | `ms-*` | `mr-*` | `me-*` |
| `pl-*` | `ps-*` | `pr-*` | `pe-*` |
| `text-left` | `text-start` | `text-right` | `text-end` |
| `rounded-l-*` | `rounded-s-*` | `rounded-r-*` | `rounded-e-*` |
| `border-l-*` | `border-s-*` | `border-r-*` | `border-e-*` |
| `slide-in-from-left` | `slide-in-from-start` | `slide-in-from-right` | `slide-in-from-end` |

Directional icons (chevrons, arrows) get `rtl:rotate-180` added automatically.

---

## 5. Common Component Patterns

### Forms: react-hook-form + zod + shadcn Field

```tsx
import { zodResolver } from "@hookform/resolvers/zod"
import { Controller, useForm } from "react-hook-form"
import * as z from "zod"

const schema = z.object({ title: z.string().min(3).max(64) })

export function MyForm() {
  const form = useForm<z.infer<typeof schema>>({
    resolver: zodResolver(schema),
    defaultValues: { title: "" },
  })
  return (
    <form onSubmit={form.handleSubmit(onSubmit)}>
      <Controller name="title" control={form.control}
        render={({ field, fieldState }) => (
          <Field data-invalid={fieldState.invalid}>
            <FieldLabel>Title</FieldLabel>
            <Input {...field} aria-invalid={fieldState.invalid} />
            {fieldState.invalid && <FieldError errors={[fieldState.error]} />}
          </Field>
        )} />
    </form>
  )
}
```

### Data Tables: TanStack Table + shadcn Table

```tsx
const table = useReactTable({
  data, columns,
  getCoreRowModel: getCoreRowModel(),
  getSortedRowModel: getSortedRowModel(),
  getPaginationRowModel: getPaginationRowModel(),
  onSortingChange: setSorting,
  state: { sorting },
})
```

Wrap output in `<Table>`, `<TableHeader>`, `<TableBody>`, `<TableRow>`, `<TableCell>`.

### Dialogs, Dropdowns, Popovers, Tooltips

| Component | Use for | Key behaviors |
|-----------|---------|--------------|
| `Dialog` | Confirmations, forms, detail views | Focus trap, Escape-to-close, overlay dismiss |
| `DropdownMenu` | Action menus | Arrow keys, type-ahead, Enter/Space, submenus |
| `Popover` | Interactive content (filters, forms) | Collision-aware positioning, stays open |
| `Tooltip` | Non-interactive hints | Delay, `aria-describedby`, hover/focus triggered |

---

## 6. Radix UI Primitive Mapping

| UI Pattern | Radix Primitive | shadcn Component | Key Behavior |
|-----------|----------------|-----------------|--------------|
| Modal | `Dialog` | `Dialog` | Focus trap, portal, overlay dismiss |
| Confirm dialog | `AlertDialog` | `AlertDialog` | Blocks interaction, requires action |
| Dropdown | `DropdownMenu` | `DropdownMenu` | Keyboard nav, type-ahead, submenus |
| Context menu | `ContextMenu` | `ContextMenu` | Right-click trigger |
| Select | `Select` | `Select` | Listbox semantics, type-ahead |
| Popover | `Popover` | `Popover` | Collision-aware positioning |
| Tooltip | `Tooltip` | `Tooltip` | Delay, non-interactive |
| Tabs | `Tabs` | `Tabs` | Arrow key nav, ARIA tablist |
| Accordion | `Accordion` | `Accordion` | Single/multiple expand |
| Toggle | `Toggle` | `Toggle` | Pressed state, ARIA toggle |
| Toggle group | `ToggleGroup` | `ToggleGroup` | Single/multiple selection, roving focus |
| Checkbox | `Checkbox` | `Checkbox` | Tri-state, indeterminate |
| Radio group | `RadioGroup` | `RadioGroup` | Arrow key roving, single selection |
| Switch | `Switch` | `Switch` | On/off, ARIA switch role |
| Slider | `Slider` | `Slider` | Range, step, keyboard arrows |
| Menubar | `Menubar` | `Menubar` | Desktop-style menu traversal |
| Navigation | `NavigationMenu` | `NavigationMenu` | Accessible nav with submenus |
| Progress | `Progress` | `Progress` | ARIA progressbar |
| Scroll area | `ScrollArea` | `ScrollArea` | Custom scrollbars, cross-platform |
| Collapsible | `Collapsible` | `Collapsible` | Expand/collapse, ARIA expanded |
| Hover card | `HoverCard` | `HoverCard` | Pointer-triggered preview |

Components **not** built on Radix (pure Tailwind + HTML): `Button`, `Badge`, `Card`, `Input`, `Textarea`, `Label`, `Table`, `Avatar`, `Skeleton`, `Alert`, `Separator`, `Calendar`, `Carousel`.

---

## 7. Theming

### Variable Convention

Each semantic token uses `--<name>` for background and `--<name>-foreground` for text. Components reference these via Tailwind: `bg-primary` maps to `var(--primary)`, `text-primary-foreground` maps to `var(--primary-foreground)`.

### Core Theme Tokens

| Token | Purpose |
|-------|---------|
| `--background` / `--foreground` | Page background and default text |
| `--card` / `--card-foreground` | Card surfaces |
| `--popover` / `--popover-foreground` | Popover/dropdown surfaces |
| `--primary` / `--primary-foreground` | Primary actions |
| `--secondary` / `--secondary-foreground` | Secondary actions |
| `--muted` / `--muted-foreground` | Subdued surfaces and helper text |
| `--accent` / `--accent-foreground` | Hover states and emphasis |
| `--destructive` / `--destructive-foreground` | Destructive actions |
| `--border` | Default border color |
| `--input` | Form input borders |
| `--ring` | Focus ring color |
| `--radius` | Default border radius |
| `--chart-1` through `--chart-5` | Data visualization palette |
| `--sidebar-*` | Sidebar-specific overrides |

### Color Format and Dark Mode

Colors use `oklch` (perceptually uniform). Dark overrides go in the `.dark` selector:

```css
:root {
  --primary: oklch(0.21 0.006 285.885);
  --primary-foreground: oklch(0.985 0 0);
  --border: oklch(0.92 0.004 286.32);
}
.dark {
  --primary: oklch(0.922 0 0);
  --primary-foreground: oklch(0.205 0 0);
  --border: oklch(1 0 0 / 10%);
}
```

Register the dark variant in Tailwind v4: `@custom-variant dark (&:where(.dark, .dark *));`

Toggle with `next-themes` or any class-based theme switcher. Edit CSS variables in your global CSS -- all components update automatically. Use the [shadcn themes tool](https://ui.shadcn.com/themes) to generate variable sets visually.
