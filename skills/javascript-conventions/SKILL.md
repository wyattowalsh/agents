---
name: javascript-conventions
description: >-
  JavaScript/Node.js tooling conventions. Use pnpm for all package management
  (not npm or yarn, unless a project explicitly requires them).
user-invocable: false
license: MIT
metadata:
  author: wyattowalsh
  version: "1.0.0"
---

# JavaScript/Node.js Conventions

Apply these conventions when working on JavaScript or Node.js files or projects.

## Package Management

- **Use `pnpm`** for all Node.js package management
- Do not use `npm` or `yarn` unless the project explicitly requires them (e.g., existing lockfile, CI configuration)
- Commands: `pnpm install`, `pnpm add <pkg>`, `pnpm run <script>`, `pnpm exec <cmd>`
