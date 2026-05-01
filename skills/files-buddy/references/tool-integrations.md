# Tool Integrations Reference

CLI interfaces for tools that files-buddy delegates to. Each entry covers purpose, key commands, output format, and dry-run behavior.

## Install Commands

```bash
# Homebrew (macOS/Linux)
brew install fd fclones rmlint dust erdtree ouch zstd b3sum detox convmv gomi rclone pueue bat git-delta watchexec

# Python
pip install organize-tool rich

# Go
go install github.com/ayoisaiah/f2/v2/cmd/f2@latest

# Rust
cargo install czkawka_cli
```

Optional free/OSS helpers: dupeGuru (GUI duplicate review), Video Duplicate Finder (similar videos), `imagededup` (Python image similarity), `jdupes`, `rdfind`, `duff`, Docker/Colima/OrbStack CLIs, `tmutil`, Xcode `xcrun`, `brctl`, and `fileproviderctl`.

## Tool Reference

### File Finding

| Tool | Purpose | Key Commands | Dry-Run |
|------|---------|-------------|---------|
| **fd** | Fast `find` replacement | `fd -e jpg` (by ext), `fd -t f --size +100m` (large files), `fd --changed-within 1w` (recent), `fd -t d -e ''` (empty dirs) | N/A (read-only) |

fd output is one path per line. Use `fd --format '{}'` for custom templates or `fd -0` for null-delimited output (safe for filenames with spaces).

### Deduplication

| Tool | Purpose | Key Commands | Dry-Run | Output Format |
|------|---------|-------------|---------|---------------|
| **fclones** | Fast duplicate finder | `fclones group <path>`, `fclones remove`, `fclones link`, `fclones dedupe` | `fclones remove --dry-run < dups.txt` | `--format json` |
| **rmlint** | Lint + dedup | `rmlint <path>`, `rmlint -T duplicates,emptyfiles,emptydirs` | Generates `rmlint.sh` (review before running) | `-o json:<file>` |
| **czkawka_cli** | Multi-mode cleaner and media similarity | `czkawka_cli dup -d /path`, `czkawka_cli image -d /path`, `czkawka_cli video -d /path`, `czkawka_cli music -d /path` | Report mode only; no delete method unless approved | stdout / JSON flags where supported |
| **dupeGuru** | GUI duplicate and fuzzy media review | Launch/import paths, export results | Review-only GUI | App export |
| **Video Duplicate Finder** | Specialist similar-video review | GUI/project report | Review-only | App export |
| **imagededup** | Python image near-duplicate clustering | library/scripted reports | Read-only report | JSON/custom |

**czkawka_cli modes:** `dup`, `empty-folders`, `empty-files`, `big`, `temp`, `image`, `video`, `music`, `symlinks`, `broken`, `ext`. Use delete options only after explicit approved plan.

**rmlint lint types for `-T`:** `duplicates`, `emptyfiles`, `emptydirs`, `nonstripped`, `badids`, `badlinks`

### Organization

| Tool | Purpose | Key Commands | Dry-Run |
|------|---------|-------------|---------|
| **organize-tool** | Rule-based file organizer | `organize run`, `organize sim` | `organize sim` (simulate) |
| **watchexec** | File watcher | `watchexec -e jpg,png -- organize run config.yml` | N/A (trigger-based) |

organize-tool uses YAML config (`~/.config/organize/config.yml`):
```yaml
rules:
  - locations: ~/Downloads
    filters:
      - extension: [jpg, png, gif]
      - lastmodified: {days: 30}
    actions:
      - move: ~/Pictures/{extension}/
```

### Rename

| Tool | Purpose | Key Commands | Dry-Run | Undo |
|------|---------|-------------|---------|------|
| **f2** | Batch rename | `f2 -f 'pat' -r 'rep'` | Default (dry-run unless `-x`) | `f2 -u` |

**f2 variables:** EXIF `{xt.make}`, `{xt.model}`, `{xt.date}` | ID3 `{id3.artist}`, `{id3.title}`, `{id3.album}` | Built-in `{.ext}`, `{nr}`, `{p}` (parent dir)

Conflict resolution: `--fix-conflicts-pattern` auto-appends `(1)`, `(2)`, etc.

### Disk Analysis

| Tool | Purpose | Key Commands | Output Format |
|------|---------|-------------|---------------|
| **dust** | Disk usage treemap | `dust`, `dust -F` (files only), `dust -t` (by type) | `-j` for JSON |
| **erdtree** | Directory tree + sizes | `erd -l -s rsize` (long, sort by real size) | `--layout flat` or pipe to JSON |

### macOS Storage and Cache Inventory

| Tool | Purpose | Safe Command | Mutating Command Requires Approval |
|------|---------|--------------|------------------------------------|
| **tmutil** | Time Machine local snapshots | `tmutil listlocalsnapshots /` | Snapshot deletion |
| **docker** | Container/images/cache usage | `docker system df -v` | `docker system prune` / volume prune |
| **xcrun simctl** | Xcode simulator inventory | `xcrun simctl list devices`, `xcrun simctl list runtimes` | deleting unavailable simulators |
| **brctl** | iCloud status/materialize/evict | `brctl status`, `brctl quota` | `download`, `evict` |
| **fileproviderctl** | File Provider materialize/evict | provider status/list where available | `materialize`, `evict` |
| **lsof** | Process references | `lsof +D <path>` on small scopes | N/A |

### Safe Delete

| Tool | Purpose | Key Commands | Restore |
|------|---------|-------------|---------|
| **gomi** | Trash CLI (XDG spec) | `gomi file`, `gomi -r dir/` | `gomi --restore` (interactive picker) |

Follows XDG Trash specification (`~/.local/share/Trash/`). Safe alternative to `rm`.

### Hashing

| Tool | Purpose | Key Commands | Verify |
|------|---------|-------------|--------|
| **b3sum** | BLAKE3 hash | `b3sum file`, `b3sum --num-threads N` | `b3sum --check hashfile` |

BLAKE3 is faster than SHA-256 on multi-core systems. Use `--num-threads 0` for max parallelism.

### Archives

| Tool | Purpose | Key Commands | Notes |
|------|---------|-------------|-------|
| **ouch** | Universal compress/decompress | `ouch compress src dst.tar.gz`, `ouch decompress arc.tar.gz`, `ouch list --tree arc.zip` | Auto-detects format from extension |
| **zstd** | Zstandard compression | `zstd file`, `zstd -d file.zst`, `zstd -T0 file` (all cores) | Levels: `-1` (fast) to `-22` (max), default `-3` |

### Filename Cleanup

| Tool | Purpose | Key Commands | Dry-Run |
|------|---------|-------------|---------|
| **detox** | Sanitize filenames | `detox file`, `detox -r dir/` | `detox -n` |
| **convmv** | Fix filename encoding | `convmv --nfc -r dir/` (NFC normalize) | Default (dry-run unless `--notest`) |

### Cloud

| Tool | Purpose | Key Commands | Output Format |
|------|---------|-------------|---------------|
| **rclone** | Cloud storage Swiss army knife | `rclone lsjson remote:path`, `rclone dedupe remote:path`, `rclone size remote:path`, `rclone mount remote:path /mnt` | `lsjson` returns JSON array |

Use `rclone --dry-run` on any mutating command. `rclone dedupe` supports `--dedupe-mode`: `interactive`, `skip`, `first`, `newest`, `oldest`, `largest`, `smallest`, `rename`, `list`. Prefer `list` and `rename` before destructive modes.

### Dashboard Build Source

| Tool | Purpose | Command |
|------|---------|---------|
| **Node/pnpm** | Optional dashboard source build | `pnpm install && pnpm build` inside a future dashboard source dir |
| **React** | Source component model | shadcn-style components documented in `dashboard-app.md` |
| **Tailwind CSS v4** | CSS-first design tokens | `@import "tailwindcss"` + `@theme` |
| **Recharts** | Source charts | Funnel, bar, pie, treemap, scatter; static template keeps accessible fallback |

### Batch Processing

| Tool | Purpose | Key Commands |
|------|---------|-------------|
| **pueue** | Task queue daemon | `pueue add -- command`, `pueue parallel N`, `pueue status`, `pueue log <id>` |

Start daemon with `pueued -d`. Group tasks with `pueue group add <name>` and `pueue add --group <name> -- cmd`.

### Preview

| Tool | Purpose | Key Commands |
|------|---------|-------------|
| **bat** | Syntax-highlighted file viewer | `bat file`, `bat --style=plain file` (no decorations), `bat -l json` (force language) |
| **delta** | Side-by-side diff viewer | `delta before.txt after.txt`, `delta --side-by-side` |

## Output Parsing

JSON schemas for tools that produce structured output.

### fclones group --format json

```json
{
  "stats": {
    "groups": 42,
    "redundant": 84,
    "redundant_bytes": 1048576
  },
  "groups": [
    {
      "file_len": 12345,
      "hash": "abc123...",
      "files": [
        {"path": "/absolute/path/to/file1.jpg"},
        {"path": "/absolute/path/to/file2.jpg"}
      ]
    }
  ]
}
```

### rmlint -o json:output.json

```json
[
  {
    "description": "rmlint json-dump of...",
    "total_files": 500,
    "total_lint_size": 2048000
  },
  {
    "type": "duplicate_file",
    "path": "/path/to/dup.jpg",
    "size": 10240,
    "hash": "deadbeef...",
    "is_original": false,
    "mtime": 1700000000
  },
  {
    "type": "emptyfile",
    "path": "/path/to/empty.txt",
    "size": 0
  }
]
```

Header object is first element; lint entries follow. `is_original: true` marks the keeper in each duplicate group.

### dust -j

```json
[
  {
    "name": "node_modules",
    "size": 524288000,
    "children": [
      {"name": "react", "size": 10485760},
      {"name": "webpack", "size": 52428800}
    ]
  }
]
```

### rclone lsjson remote:path

```json
[
  {
    "Path": "photos/IMG_001.jpg",
    "Name": "IMG_001.jpg",
    "Size": 2048000,
    "MimeType": "image/jpeg",
    "ModTime": "2024-01-15T10:30:00.000000000Z",
    "IsDir": false,
    "ID": "abc123"
  }
]
```

Use `--hash` to include checksums: adds `"Hashes": {"MD5": "...", "SHA-1": "..."}` per entry. Use `--recursive` for deep listing.

## Quick Dry-Run Reference

| Tool | Dry-Run Flag | Notes |
|------|-------------|-------|
| fd | N/A | Read-only |
| fclones | `--dry-run` | On `remove`/`link`/`dedupe` |
| rmlint | Review `rmlint.sh` | Does not auto-delete |
| czkawka_cli | `--delete-method none` | Report only |
| organize-tool | `organize sim` | Separate command |
| f2 | Default behavior | Add `-x` to execute |
| detox | `-n` | Preview mode |
| convmv | Default behavior | Add `--notest` to execute |
| rclone | `--dry-run` | On any mutating command |
| gomi | N/A | Moves to trash (restorable) |
| ouch | N/A | Prompts before overwrite |
| zstd | N/A | Refuses to overwrite by default |
