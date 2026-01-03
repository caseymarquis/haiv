```toml
# Spec Metadata (placeholder format - will be refined)
version = "1.0.0"
status = "ready"  # draft | ready | implementing | implemented | deprecated

[history]
created = 2025-12-27
created_by = { user = "casey" }
updated = 2025-12-28
updated_by = { user = "casey" }

[implementation]
version = "0.0.0"  # version currently in code
branch = ""        # branch where implementation lives
commit = ""        # last commit implementing this spec

[coordination]
owner = "casey"           # who owns this spec
reviewers = []            # who should review changes
blocks = []               # what's waiting on this
blocked_by = []           # what this is waiting on
related = ["mg-init-checklist.md"]

[location]
current = "minds/specs/documents/mg-init-spec.md"
future = "mg-core/specs/mg-init.md"
```

# mg init - Specification

---

## Change Log

| Date | Change |
|------|--------|
| 2025-12-28 | Updated to match test suite: added `--empty` flag, fresh empty creates main worktree by default |
| 2025-12-27 | Initial spec created |

---

## Purpose

Set up the mind-games structure, either as a peer to an existing repo or fresh in the current directory.

---

## Modes

| Context | Behavior |
|---------|----------|
| In a git repo | Create peer `project-mg/` alongside (non-destructive) |
| Not in a repo, empty dir | Create mg structure in current directory |
| Not in a repo, non-empty dir | Require `--force`; move contents into worktree |

---

## Directory Structure

mg-state is the root. Code worktrees are children.

```
project-mg/                    # IS mg-state (orphan branch)
├── .git/                      # bare repo data
├── .claude/                   # Claude Code config
├── CLAUDE.md                  # describes mg system
├── mg.toml                    # mg configuration
├── src/mg_project/            # project-level commands, etc.
├── users/casey/state/minds/   # where minds live
└── worktrees/
    ├── main/                  # code worktree
    └── feature-x/             # code worktree
```

**Rationale:**
- Control plane at top level - where humans and AIs start
- `cd project-mg` → immediately in useful context
- Claude instances initialize here, navigate to `worktrees/` for code
- `worktrees/` not hidden - first-class concept, only exists on orphan branch

---

## Flags

### `--force`

Override safety checks:
- **Peer mode:** Proceed despite dirty working tree (warns about what won't be in clone)
- **Fresh non-empty:** Required to move existing files into worktree

### `--branch <name>`

Specify which branch to create worktree for:
- **Peer mode:** Override current branch (default: current branch)
- **Fresh mode:** Which branch to create (default: main)

### `--empty`

Skip worktree creation (fresh mode only):
- Creates mg structure without any code worktree
- Useful when you want to add worktrees manually later

### `--quiet`

Suppress educational output for automation scenarios.

---

## Behavior: Peer Mode (in a git repo)

### Prerequisites
- Must have remote configured (error with guidance if not)
- Must have clean working tree (error if dirty, unless --force)

### Steps
1. Find repo root (walk up from current directory)
2. Get remote URL (origin)
3. Create `../project-mg/` with bare clone from remote
4. Create `worktrees/` directory
5. Create mg-state orphan branch (root of project-mg/)
6. Create worktree for current branch (or --branch if specified)
7. Print success message with next steps

### Errors
- Working tree is dirty → error (use --force to override)
- No remote configured → error with guidance
- Peer directory already exists → error

---

## Behavior: Fresh Mode (not in a git repo)

### Empty Directory

1. `git init` with bare repo structure
2. Create mg-state orphan branch (root)
3. Create `worktrees/` directory
4. Create worktree for main branch (or `--branch` if specified; skip if `--empty`)
5. Create README.md and initial commit in worktree
6. Print success + next steps

### Non-Empty Directory (requires --force)

1. `git init` with bare repo structure
2. Create mg-state orphan branch (root)
3. Create `worktrees/<branch>/` (default: main)
4. Move existing files into `worktrees/<branch>/`
5. Commit moved files on that branch
6. Print success + next steps

### Errors
- Non-empty without --force → error

---

## Output Philosophy

Per the vision doc's "Educate, don't obscure" principle:

- Print underlying git commands as they run
- Explain what we're accomplishing and why
- Empower users to understand worktrees and git internals
- Use `--quiet` for automation scenarios

---

## Related

- **Checklist:** `mg-init-checklist.md` (working document with test scenarios)
- **Vision:** `mind-games-vision-exploration.md`
- **Next phase:** `mg worktree add/remove/list` (Phase 0.2)
