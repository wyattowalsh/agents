# Protected Paths Reference

Path safety rules for file organization operations. Two tiers: hard-blocked (never touch) and escalated-confirmation (override with explicit naming).

---

## Hard-Blocked Paths (No Override)

These paths are unconditionally excluded from all file operations. No flag, confirmation, or user request can override this.

### macOS

- `/` — filesystem root
- `/System` — kernel extensions, core frameworks
- `/Library` — system-wide app support, launch daemons
- `/usr` — system binaries and libraries
- `/bin`, `/sbin` — essential system commands
- `/var` — system logs, caches, databases
- `/etc` — system configuration
- `/private` — backing store for /etc, /var, /tmp
- `/Applications` — system apps only (e.g., Safari.app, Finder.app)

### Linux

- `/` — filesystem root
- `/boot` — bootloader, kernel images
- `/dev` — device files
- `/proc` — kernel and process info (virtual)
- `/sys` — kernel device tree (virtual)
- `/run` — runtime variable data
- `/usr` — system binaries and libraries
- `/bin`, `/sbin` — essential system commands
- `/var` — system logs, spools, caches
- `/etc` — system configuration
- `/lib`, `/lib64` — shared libraries

### Universal

- `.git/` directories — always excluded, even with `--include-hidden`
- `.git/modules/` — submodule internals, always excluded

---

## Escalated-Confirmation Paths (Override with Explicit Naming)

These paths require the user to name them explicitly in their request. Generic commands like "organize my home directory" do not touch these.

| Path | Reason | Override |
|------|--------|---------|
| `~/.ssh` | SSH keys, authorized_keys | User must say "organize my .ssh directory" |
| `~/.gnupg` | GPG keys and trust database | Explicit path naming required |
| `~/.aws` | AWS credentials and config | Explicit path naming required |
| `~/.config` | Application configurations | Explicit path naming required |
| `~/.kube` | Kubernetes configs | Explicit path naming required |
| `~/.local/share/keyrings` | System keyrings | Explicit path naming required |
| Any directory containing `.env` | Environment secrets | Warning + confirmation |
| `.gitignore` | Git tracking rules | Warning before move |
| `.gitmodules` | Submodule definitions | Warning before move |

---

## Path Validation Algorithm

Every path argument passes through this pipeline before any operation executes.

```
1. Expand ~ to $HOME
2. Resolve all symlinks: os.path.realpath(path)
3. Resolve . and .. components
4. Check against hard-blocked list using resolved ancestor / exact-segment checks
5. Check against escalated list using resolved ancestor / exact-segment checks
6. Verify path is within scope-pinned directory using `Path.relative_to()` or `os.path.commonpath()`
7. Check for symlink cycles (max 40 hops)
```

If any step fails, the operation is rejected with a diagnostic message. Never use plain string prefix matching for path containment or blocklist checks.

---

## Scope Pinning

The scope boundary is the directory the user explicitly referenced.

- "Organize my downloads" — scope = `~/Downloads` only
- "Clean up my home" — does NOT touch escalated paths unless explicitly named
- All resolved paths must remain within the scope boundary
- Traversal above the scope boundary (via `..` or symlinks) is rejected

---

## .git/ Exclusion Rules

- `.git/` — always excluded from all operations
- `.git/modules/` — submodule internals, always excluded
- `.gitignore` — warn before moving (breaks git tracking behavior)
- `.gitmodules` — warn before moving (breaks submodule references)
- Git-tracked files — require explicit confirmation before moving

---

## Override Protocol

Applies to escalated-confirmation paths only. Hard-blocked paths have no override.

1. User must explicitly name the path in their request
2. Display full preview with resolved (real) paths
3. Show warning banner: "This operation affects [path], which is security-sensitive"
4. Require explicit "yes" confirmation before proceeding
5. Log the override decision for audit trail
