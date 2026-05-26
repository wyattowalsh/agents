# Presets

Presets reduce option overload. Start with the smallest preset that satisfies the request and add explicit overrides.

## Defaults

| Preset         | Use when                                                          |
| -------------- | ----------------------------------------------------------------- |
| `minimal`      | The user wants a tiny baseline                                    |
| `recommended`  | The user gives a broad “start a project” request                  |
| `python-api`   | API/backend keywords appear                                       |
| `web-app`      | Next.js, React, frontend, SaaS, dashboard, or app keywords appear |
| `docs-lite`    | Docs requested without product/API docs requirements              |
| `docs-product` | Product docs, SDK docs, OpenAPI, or rich MDX requirements appear  |
| `monorepo`     | Multiple apps/packages or workspace orchestration appears         |
| `max-free`     | User explicitly asks for comprehensive setup                      |

`max-free` is blueprint-only by default. Apply modules one at a time.
