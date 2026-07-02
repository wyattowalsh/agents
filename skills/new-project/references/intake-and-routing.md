# Intake And Routing

Ask only high-impact questions that affect architecture or safety.

## Classification Signals

| Signal                                     | Route                          |
| ------------------------------------------ | ------------------------------ |
| Empty or vague new repo request            | `recommended` plan             |
| Existing files or current directory target | `bootstrap` or `audit` first   |
| Docs without app integration               | `docs-lite`                    |
| OpenAPI, SDK docs, Next app docs           | `docs-product`                 |
| Cloud, DNS, deploy, release                | planning only, explicit opt-in |
| Feature implementation                     | refuse or redirect             |
| Agent/MCP creation                         | refuse or redirect             |

## Ambiguity Gate

If target path, project type, package manager, docs stack, database primary, or deploy target is ambiguous, apply `instructions/global.md` Depth routing before mutation.

- **Independent enum** (one stack choice): short batched multiple-choice question.
- **User-pivotal plan** (vague goal or interdependent architecture prefs): suggest `/grill-me` before `plan` mode.
