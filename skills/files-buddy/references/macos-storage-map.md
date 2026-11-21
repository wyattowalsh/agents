# macOS Storage Map

Use this as the canonical `all-local` inventory map. Default to read-only scans and
label each surface with action class, savings potential, dependencies, and repercussions.

## Surface Matrix

| Surface | Discovery | Savings potential | Action class | Repercussions |
|---------|-----------|-------------------|--------------|---------------|
| Home folders | `~/Desktop`, `~/Documents`, `~/Downloads`, `~/Movies`, `~/Music`, `~/Pictures` | High | cleanup/offload/archive/dedupe | User-visible files; require clear keeper and restore path |
| Cloud roots | `~/Library/Mobile Documents/com~apple~CloudDocs`, `~/Library/CloudStorage/*` | High local, possible cloud quota | offload/review | Deletion syncs globally; placeholder materialization can consume local disk |
| External volumes | `/Volumes/*` excluding system volumes | Variable | audit/review | Slow or removable media; do not assume availability between preview and execution |
| Xcode | `~/Library/Developer/Xcode/DerivedData`, `Archives`, `iOS DeviceSupport`, `CoreSimulator` | High | cache-prune/app-native | Rebuilds, simulator re-downloads, archive loss if not exported |
| Docker/Colima/OrbStack/Podman | Docker contexts, VM disk images, volumes | High | report/dry-run prune | Containers/images/volumes may be needed; volumes can contain data |
| Node/package managers | `node_modules`, `~/.npm`, `~/Library/pnpm`, `~/.yarn`, `~/.cache/yarn` | High | cache-prune/rebuild | Reinstall time, offline cache loss, workspace dependency breakage |
| Python | `.venv`, `~/.cache/uv`, `~/.cache/pip`, Poetry, pyenv builds | Medium/high | cache-prune/rebuild | Reinstall/build time; compiled wheels may be expensive |
| Rust/Go/Java | `~/.cargo`, `~/go/pkg/mod`, Gradle/Maven caches | Medium/high | cache-prune/rebuild | Re-download/recompile; offline builds fail |
| AI/model caches | `~/.cache/huggingface`, `~/.ollama`, `~/Library/Application Support/LM Studio`, `~/.cache/torch`, Diffusers/Transformers/ComfyUI | Very high | offload/review | Large redownloads, model paths in apps, quantization uniqueness |
| Photos/Music/TV libraries | `~/Pictures/*.photoslibrary`, `~/Music/Music`, `~/Movies/TV` | High | report-only/app-native | App databases; direct file deletion can corrupt libraries |
| Mail/Messages | `~/Library/Mail`, `~/Library/Messages` | Medium/high | report-only/app-native | Search indexes, attachments, legal/history value |
| Backups | `~/Library/Application Support/MobileSync/Backup`, Time Machine local snapshots | High | report-only/app-native | Device restore loss; `tmutil` often needs privileges |
| VMs | UTM, Parallels, VMware, VirtualBox, Docker disk images | High | review/archive | Snapshot chains and app metadata; direct deletion can break VM |

## Read-Only Commands

| Need | Command |
|------|---------|
| Top-level usage | Version-qualified `dust -j <path>` (one root node, formatted sizes); metadata scanner for byte accounting |
| Large files | `fd -0 -t f --size +1g . "$scope"` |
| Old files | `fd -0 -t f --changed-before 1y . "$scope"` |
| APFS snapshots | `tmutil listlocalsnapshots /` |
| Docker usage | `docker system df --format json` or `docker system df -v` |
| Cloud list | Bounded `rclone lsjson remote:path` for an explicitly chosen configured remote; omit content hashes by default |
| Xcode simulators | `xcrun simctl list devices` and `xcrun simctl list runtimes` |

The fd expression is the pattern and the following argument is the search root.
Choose and report hidden/ignore rules explicitly; default fd output excludes some
hidden/ignored paths. NUL-delimited names require a NUL-aware consumer. Do not
pipe output into mutation commands. Command outputs are evidence of occupancy,
not proof of reclaimable physical bytes or permission to prune.

## Action Classes

- **Trash candidate:** exact selected files after dependency review and approval;
  Trash retains bytes until removal and is not implemented as a generic cleanup fallback.
- **Exact duplicate:** content-identical duplicates with keeper evidence.
- **Similar media review:** perceptual matches only; user chooses.
- **Archive:** cold user files where restore path and archive integrity are clear.
- **Offload:** cold files kept in cloud/remote/archive while freeing local bytes.
- **Cache review:** owner-native cleanup proposal with evidence of rebuild cost and
  dependencies; the helper does not execute arbitrary prune commands.
- **Report-only:** app-managed libraries, snapshots, VM internals, and protected stores.

## Do Not Proceed If

- The path is hard-blocked or crosses the scope pin.
- A cloud operation could delete synced data instead of freeing only local bytes.
- The recommendation claims actionable recovery without a verified restore path.
- The dependency owner cannot be identified for app-managed or cache data.
- Preview evidence is missing/stale, or any mapped input differs from the approved plan.
