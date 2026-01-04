```index
@aar-file-indexing
After action report for file indexing analysis. Produced @file-indexing-exploration.
Recommends hybrid approach: files as source of truth, SQLite as gitignored generated cache.
```

# After Action Report: File Indexing Analysis

**Task:** Critical analysis of file indexing approach
**Mind:** Reed (Analyst)
**Date:** 2026-01-04

---

## Summary

Analyzed the proposed file-based indexing approach (```index blocks with @ref-ids). Explored trade-offs versus SQLite and existing solutions. Recommended a hybrid approach: files remain source of truth, SQLite as a generated cache for query capabilities.

---

## Deliverables

| Document | Location |
|----------|----------|
| Exploration | `explorations/file-indexing.md` (@file-indexing-exploration) |

---

## Key Decisions

### 1. Hybrid Approach
- Files with ```index blocks remain source of truth
- SQLite (.index.db) is gitignored, generated per-instance
- Queries use SQLite, content always served from disk

### 2. Core mg Commands
- `mg index rebuild` - regenerate from files
- `mg index find` - lookup by @ref-id
- `mg index check` - validate refs, find duplicates
- `mg index refs` - show reference graph
- `mg index search` - full-text search (optional)
- `mg index query` - raw SQL for power users

### 3. Start Simple
- Index only files with ```index blocks
- Metadata only initially (no full content)
- Manual rebuild, add automation if friction emerges

---

## Trade-offs Accepted

**Chose file-native over query-first**
- Claude reads files directly, no translation layer
- Git diffs remain meaningful
- SQLite corruption is recoverable (just rebuild)

**Chose manual rebuild over auto-sync**
- Simpler implementation
- Explicit is better than magic
- Can add lazy invalidation later if needed

---

## Open Items

- Scope of indexing (all markdown vs only ```index files)
- Cross-user vs per-user index location
- Whether to index worktree code
- Document discipline: ensuring minds create structured documents via `mg doc create`, with `rename` and `fix` commands for maintenance (big project)

---

## Blockers Encountered

None.
