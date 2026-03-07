# History and Debugging

Conflict resolution patterns, code archaeology techniques, and bisect workflows.

## Contents

1. [Conflict Resolution](#conflict-resolution)
2. [Code Archaeology](#code-archaeology)
3. [Git Bisect](#git-bisect)

---

## Conflict Resolution

### Reading Conflict Markers

```
<<<<<<< HEAD (ours)
  code from current branch
=======
  code from incoming branch
>>>>>>> feature-branch (theirs)
```

- **Ours** (above `=======`): the branch you are merging INTO
- **Theirs** (below `=======`): the branch being merged

### Resolution Strategies

| Strategy | When to Use |
|----------|-------------|
| Keep ours | Their change is obsolete or wrong |
| Keep theirs | Our change was a stopgap, their version is better |
| Merge both | Both sides added different valid content |
| Rewrite | Neither side is correct as-is; combine intent from both |

### Resolution Process

1. **Understand context**: `git log --merge -p -- <file>` shows the diverging commits
2. **Identify intent**: What was each side trying to accomplish?
3. **Check dependencies**: Does the resolution affect other files?
4. **Resolve**: Edit the file, remove all conflict markers
5. **Verify**: Run tests, check that both intents are preserved
6. **Stage**: `git add <file>`
7. **Continue**: `git merge --continue` or `git rebase --continue`

### Common Conflict Patterns

**Adjacent edits**: Both sides edited nearby lines. Usually merge both.

**Divergent refactors**: One side renamed, other side modified. Apply the modification to the renamed version.

**Dependency conflicts** (package-lock.json, yarn.lock): Regenerate the lockfile.
```bash
# For npm
rm package-lock.json && npm install
# For yarn
rm yarn.lock && yarn install
# For pnpm
rm pnpm-lock.yaml && pnpm install
```

**Schema conflicts** (migrations): Renumber the conflicting migration or create a merge migration.

---

## Code Archaeology

### Why Code Exists

Use these commands in order of specificity:

**Line-level attribution:**
```bash
git blame <file>                    # Who last changed each line
git blame -L 10,20 <file>          # Blame specific line range
git blame -w <file>                # Ignore whitespace changes
git blame -M <file>                # Detect moved lines
git blame -C <file>                # Detect copied lines from other files
```

**File history:**
```bash
git log --follow --oneline -- <file>         # Full history (follows renames)
git log --follow --diff-filter=A -- <file>   # When was this file created?
git log --follow -p -- <file>                # History with diffs
git log --follow --format='%h %ai %an: %s' -- <file>  # Compact with dates
```

**Function-level history:**
```bash
git log -L :<function>:<file>                # History of a specific function
git log -p --all -S '<string>'               # Pickaxe: when was string added/removed
git log -p --all -G '<regex>'                # Grep: when did regex match change
```

**Cross-file analysis:**
```bash
git log --all --oneline -- <file1> <file2>   # Commits touching both files
git shortlog -sn -- <file>                   # Who contributes most to this file
```

### Building a Narrative

When presenting archaeology findings, structure as:

1. **Origin**: When created, by whom, original commit message
2. **Key modifications**: Major changes in chronological order
3. **Current state**: Who last touched it, when, why
4. **Related files**: Other files that commonly change together
5. **Assessment**: Is this code actively maintained? Stable? Drifting?

---

## Git Bisect

### Manual Bisect

```bash
git bisect start
git bisect bad <bad-commit>        # Where the bug exists (default: HEAD)
git bisect good <good-commit>      # Where the bug did not exist
# Git checks out a middle commit
# Test manually, then:
git bisect good                    # This commit is fine
# or
git bisect bad                     # This commit has the bug
# Repeat until git identifies the first bad commit
git bisect reset                   # Return to original state
```

### Automated Bisect

```bash
git bisect start <bad> <good>
git bisect run <test-command>
# test-command exit 0 = good, exit 1-124/126-127 = bad, exit 125 = skip
git bisect reset
```

**Common test commands:**
```bash
git bisect run python -m pytest tests/test_parser.py
git bisect run npm test
git bisect run make test
git bisect run bash -c 'grep -q "expected_string" output.txt'
```

### Bisect Tips

- **Narrow the range**: The tighter good..bad, the fewer steps needed
- **Skip untestable commits**: `git bisect skip` for broken builds
- **Log your progress**: `git bisect log` shows the bisect history
- **Replay a session**: `git bisect replay <log-file>`
- **Visualize**: `git bisect visualize` opens gitk on remaining commits
- **Steps estimate**: Binary search = ~log2(commits) steps. 1000 commits ~ 10 steps.

### After Finding the Commit

1. Read the full commit: `git show <hash>`
2. Check the commit message for context and linked issues
3. Look at the parent commit: `git show <hash>^` for before-state
4. Check if there were related commits: `git log --oneline <hash>~5..<hash>+5`
5. Investigate: was this an intentional change with unintended side effects, or an outright mistake?
