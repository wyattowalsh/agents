# Redirection Boundaries

Use this reference when Python is present but may not be the dominant
workstream.

## Route Away When

| Situation | Better Fit |
|-----------|------------|
| Shell scripts, Makefiles, or portable shell behavior are primary | `shell-conventions` |
| JS/TS files, Node package management, or `package.json` are primary | `javascript-conventions` |
| CI workflow architecture or pipeline design is primary | `devops-engineer` |
| Python is incidental inside a larger domain-specific task | The domain skill plus Python conventions only for the Python-owned seam |

## Mixed-Language Handling

1. If Python files are primary and shell or JS/TS is incidental, keep this skill active for the Python-owned surface only.
2. If Python is incidental and another language or pipeline surface dominates, do not force Python conventions onto the entire task.
3. When both surfaces matter, apply each conventions skill only to its owned files and commands.

## Empty / Help Routing

If the user asks for general project-tooling help and the repo is polyglot:

- summarize Python hard requirements briefly
- say when `shell-conventions` or `javascript-conventions` should take over
- avoid presenting Python defaults as repo-wide law for every language
