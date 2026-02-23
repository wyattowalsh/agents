# Vite 6 Setup & Configuration

> Targets Vite 6.x + React + TypeScript. Verify via Context7 if behavior differs.

## 1. Project Setup

```bash
npm create vite@latest my-app -- --template react-ts
cd my-app && npm install
```

Produces: `src/{App.tsx, main.tsx, vite-env.d.ts}`, `public/`, `index.html`, `vite.config.ts`, `tsconfig.json`. Node.js 18, 20, or 22+ required.

## 2. Vite Configuration

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': '/src' } },
})
```

Use `@vitejs/plugin-react-swc` over `@vitejs/plugin-react` for faster transforms.

## 3. CSS Handling

**Tailwind v4** — first-party Vite plugin, no PostCSS config needed:

```bash
npm install tailwindcss @tailwindcss/vite
```

```ts
import tailwindcss from '@tailwindcss/vite'
export default defineConfig({ plugins: [react(), tailwindcss()] })
```

```css
/* src/styles/globals.css — this single import is the entire setup */
@import "tailwindcss";
```

No `tailwind.config.js`. Configure tokens in `@theme {}` directly in CSS.

**Lightning CSS** — alternative to PostCSS for non-Tailwind projects:

```ts
export default defineConfig({
  css: { transformer: 'lightningcss', lightningcss: { drafts: { customMedia: true } } },
  build: { cssMinify: 'lightningcss' },
})
```

**CSS Modules** — rename to `*.module.css`. Vite handles them automatically.

## 4. Asset Optimization

**SVG as React components** via `vite-plugin-svgr`:

```bash
npm install -D vite-plugin-svgr
```

```ts
import svgr from 'vite-plugin-svgr'
export default defineConfig({ plugins: [react(), svgr()] })
```

Import: `import Logo from './logo.svg?react'`

**Fonts** — place in `src/assets/fonts/`, reference via `@font-face`. Vite inlines assets under 4 KB (`assetsInlineLimit`).

**Public directory** — `public/` files are copied as-is to `dist/`. Use for `favicon.ico`, `robots.txt`, OG images.

## 5. Environment Variables

**CRITICAL: Never prefix secrets with `VITE_`.** Those values are statically replaced into client JS and visible to anyone in the browser bundle.

| Prefix | Client-exposed? | Use for |
|--------|----------------|---------|
| `VITE_` | Yes | Public API URLs, feature flags, analytics IDs |
| None | No | DB credentials, API secrets, signing keys |

Files: `.env` (committed), `.env.local` (gitignored), `.env.production`, `.env.production.local`.

Access: `import.meta.env.VITE_API_URL`. Add types in `src/vite-env.d.ts`:

```ts
interface ImportMetaEnv { readonly VITE_API_URL: string }
```

## 6. Path Aliases

Keep `vite.config.ts` and `tsconfig.json` in sync — both must declare the alias:

```ts
// vite.config.ts
resolve: { alias: { '@': '/src' } }
```

```json
// tsconfig.json (or tsconfig.app.json)
{ "compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["src/*"] } } }
```

If one is missing, imports resolve at runtime but fail type-checking (or vice versa).

## 7. Environment API (Experimental)

Experimental in Vite 6, targeted at framework authors. Lets a single dev server run code across multiple environments (browser, SSR, edge workers) concurrently. Stabilization planned for Vite 7.

Do not use directly in application code. Framework plugins (Remix, Nuxt, Vike) consume it internally. Choose a framework if you need edge runtime support.

## 8. Performance

**Pre-bundling** — Vite converts CJS/UMD deps to ESM on first run. Override:

```ts
optimizeDeps: { include: ['large-cjs-dep'], exclude: ['already-esm-dep'] }
```

**HMR** — works out of the box with the React plugin. Avoid large barrel exports — they degrade HMR speed. Add `import.meta.hot.accept()` boundaries if updates fail to propagate.

**Build optimization** — split vendor chunks and set modern targets:

```ts
build: {
  target: 'esnext', // omit for Baseline Widely Available (~2.5yr-old browsers)
  rollupOptions: {
    output: { manualChunks: { vendor: ['react', 'react-dom'] } },
  },
}
```
