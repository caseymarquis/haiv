```index
@aar-memory-persistence
After action report for memory persistence design task. Produced @memory-persistence-exploration
and @memory-persistence spec. Key decisions: role/state separation, single command interface,
underscore convention for organization.
```

# After Action Report: Memory Persistence Design

**Task:** Design memory persistence for long-running minds
**Mind:** Reed (Analyst)
**Date:** 2026-01-04

---

## Summary

Produced an exploration document and specification for memory persistence. The design separates shared roles from mind-specific state, with a simple startup flow using `mg start` and `mg wake` commands.

---

## Deliverables

| Document | Location |
|----------|----------|
| Exploration | `explorations/memory-persistence.md` (@memory-persistence-exploration) |
| Specification | `specs/memory-persistence.md` (@memory-persistence) |

---

## Key Decisions

### 1. Role vs Mind State Separation
- **Roles** are shareable blueprints in `__assets__/roles/`
- **Mind state** is per-mind in `users/{user}/state/minds/{mind}/`
- This enables role reuse across minds and projects

### 2. Single Command Interface
- `mg start {mind} [--tmux]` handles all launch scenarios
- `--tmux` flag determines current terminal vs new window
- Same command works for cold start and context refresh

### 3. Underscore Convention for Organization
- Mind names cannot start with underscore
- `_` prefix directories are organizational (`_new/`, `_archived/`, etc.)
- Allows scaling to hundreds of minds with flexible organization

### 4. One Path for All Minds
- Every mind gets a folder, even short-lived workers
- Folders are cheap, simplifies mental model
- No friction if ephemeral mind needs to persist later

### 5. Deferred Complexity
- Save/distill mechanisms deferred (manual for now)
- Automatic compaction detection deferred (needs status line integration)

---

## Artifacts Updated

- `temp-roles/analyst.md` - Added spec frontmatter format (index block with @ref-id, toml metadata, changelog)

---

## Open Items

- Implementation of `mg start`, `mg wake`, `mg mine` commands
- Actual folder structure creation for existing minds (Wren, etc.)
- Template for `current-focus.md` state capture

---

## Blockers Encountered

None.
