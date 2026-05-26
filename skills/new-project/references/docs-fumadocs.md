# Fumadocs

Use Fumadocs for product/API docs when Starlight is insufficient.

Choose Fumadocs when the docs need Next.js app integration, rich MDX routing, OpenAPI pages, Twoslash TypeScript examples, or server-first/product docs behavior.

Default command skeleton:

```bash
pnpm create next-app@latest apps/docs --ts --eslint --app
pnpm --dir apps/docs add fumadocs-core fumadocs-ui fumadocs-mdx
pnpm --dir apps/docs next build
```

Add `fumadocs-openapi` only when an OpenAPI source exists. Add `fumadocs-twoslash` only for TypeScript-heavy docs.
