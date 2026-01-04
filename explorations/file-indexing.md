```index
@file-indexing-exploration
Exploration of file indexing strategies for mg. Compares pure file-based approach
with hybrid file + SQLite cache. Recommends SQLite as gitignored generated index.
```

# File Indexing Exploration

**Type:** Exploration Document
**Author:** Reed
**Date:** 2026-01-04

---

## Problem Statement

mg needs to cross-reference documents using @ref-ids and enable discovery across a growing knowledge base. The core tension:

- Claude works natively with files on disk
- Files don't support efficient queries
- We want both: file simplicity + query power

---

## Proposed Approach: Hybrid File + SQLite

**Files remain source of truth.** SQLite is a generated cache, gitignored, rebuilt on demand.

```
users/{user}/state/
├── minds/
│   └── ...
├── .index.db          # gitignored, generated
└── .gitignore         # contains: .index.db
```

### Key Principles

1. **Files are authoritative** - SQLite is derived, never edited directly
2. **Always serve from disk** - queries locate files, content comes from disk
3. **Rebuild on demand** - `mg index rebuild` scans and regenerates
4. **Per-instance** - each clone has its own .index.db, no sync conflicts

---

## What Gets Indexed

### Document Metadata

From ```index blocks:

| Field | Source | Example |
|-------|--------|---------|
| ref_id | First line starting with @ | `@memory-persistence` |
| summary | Remaining lines | "Memory persistence for..." |
| file_path | File location | `temp-reed/memory-persistence-spec.md` |

### Document Properties

From ```toml blocks (specs):

| Field | Source | Example |
|-------|--------|---------|
| version_specced | toml field | `0.1.2` |
| version_implemented | toml field | `none` |

### Full Content (Optional)

For search capabilities, could store full file contents:

| Field | Source |
|-------|--------|
| content | Entire file text |
| content_hash | SHA256 of content |

The hash enables quick staleness detection without re-reading files.

---

## mg Commands

### mg index rebuild

Scans all indexed files, regenerates .index.db.

```
$ mg index rebuild
Scanning...
  Found 47 indexed documents
  Found 3 duplicate @ref-ids (error)
  - @memory-persistence: temp-reed/spec.md, docs/old-spec.md
Rebuild failed: resolve duplicates first
```

```
$ mg index rebuild
Scanning...
  Found 47 indexed documents
  0 errors
Index rebuilt: .index.db (142KB)
```

### mg index find

Query by @ref-id:

```
$ mg index find @memory-persistence
temp-reed/memory-persistence-spec.md
```

### mg index search

Full-text search (if content indexed):

```
$ mg index search "compaction"
temp-reed/memory-persistence-exploration.md:17: ...lose context during compaction...
temp-reed/memory-persistence-spec.md:29: ...after compaction or fresh starts...
```

### mg index query

Raw SQL for power users:

```
$ mg index query "SELECT ref_id, file_path FROM documents WHERE version_implemented = 'none'"
@memory-persistence | temp-reed/memory-persistence-spec.md
@file-indexing      | temp-reed/file-indexing-spec.md
```

### mg index check

Validation without full rebuild:

```
$ mg index check
Checking for duplicate @ref-ids... OK
Checking for broken @references...
  @old-doc referenced in temp-reed/notes.md but not found
1 warning
```

### mg index refs

Show what references a document and what it references:

```
$ mg index refs @memory-persistence
Referenced by:
  - @aar-memory-persistence (temp-aar/memory-persistence-design.md)
  - @memory-persistence-exploration (temp-reed/memory-persistence-exploration.md)

References:
  (none)
```

---

## Schema Sketch

```sql
CREATE TABLE documents (
    id INTEGER PRIMARY KEY,
    ref_id TEXT UNIQUE,
    file_path TEXT UNIQUE NOT NULL,
    summary TEXT,
    content TEXT,
    content_hash TEXT,
    indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE properties (
    document_id INTEGER REFERENCES documents(id),
    key TEXT NOT NULL,
    value TEXT,
    PRIMARY KEY (document_id, key)
);

CREATE TABLE references (
    source_id INTEGER REFERENCES documents(id),
    target_ref_id TEXT NOT NULL,
    context TEXT,  -- surrounding text for debugging
    PRIMARY KEY (source_id, target_ref_id)
);

CREATE INDEX idx_ref_id ON documents(ref_id);
CREATE INDEX idx_properties ON properties(key, value);
CREATE VIRTUAL TABLE content_fts USING fts5(content, content='documents', content_rowid='id');
```

---

## Workflow Integration

### On Fresh Clone

```
$ git clone ...
$ mg index rebuild   # generates local .index.db
```

### Before Querying

If .index.db is missing or stale:
```
$ mg index find @something
Index not found. Run `mg index rebuild` first.
```

Or auto-rebuild if fast enough.

### After File Changes

Index becomes stale. Options:
1. **Manual rebuild** - user runs `mg index rebuild`
2. **Lazy invalidation** - check content_hash on query, rebuild if stale
3. **Watch mode** - `mg index watch` rebuilds on file changes (overkill?)

Recommendation: Start with manual rebuild. Add lazy invalidation if friction emerges.

---

## Comparison: Pure Files vs Hybrid

| Aspect | Pure Files | Hybrid (Files + SQLite) |
|--------|------------|-------------------------|
| Query @ref-id | Grep all files | O(1) lookup |
| Full-text search | Grep (slow at scale) | FTS5 (fast) |
| Find broken refs | Parse all files | Single query |
| Schema queries | Impossible | SQL |
| Git diffs | All meaningful | .index.db ignored |
| Setup | Zero | `mg index rebuild` |
| Staleness | N/A | Possible |
| Corruption risk | Per-file | Regenerate from files |

---

## Why Not Just SQLite?

Could make SQLite the source of truth. Why not?

1. **Claude friction** - Claude reads files natively; querying SQLite requires tooling
2. **Git unfriendly** - Binary blob, no meaningful diffs, merge conflicts
3. **Opacity** - Can't browse knowledge base in any text editor
4. **Lock-in** - Dependent on mg tooling to access your own data

The hybrid approach gives query power without sacrificing file-native simplicity.

---

## Open Questions

1. **Scope of indexing** - All markdown? Only files with ```index blocks? Configurable?

2. **Auto-rebuild triggers** - Should `mg wake` check index freshness? Or always manual?

3. **Content indexing** - Full content enables search but increases .index.db size. Worth it?

4. **Cross-user indexing** - Does each user have their own index, or one shared index? (Probably per-user, in `users/{user}/state/.index.db`)

5. **Worktree indexing** - Should code in worktrees be indexed too? Different schema needs?

6. **Document discipline** - How do we ensure all minds create properly structured documents? This is a big project:
   - `mg doc create --name` as the canonical way to create documents (generates ```index block, @ref-id, proper location)
   - `mg doc rename` to rename documents and update all @references
   - `mg doc fix` to find dead links and attempt resolution
   - Training/enforcement so minds don't just create files directly
   - Migration path for existing unstructured documents

---

## Recommendation

Start simple:
1. Index only files with ```index blocks
2. Store metadata only (no full content initially)
3. Manual rebuild via `mg index rebuild`
4. Core commands: `find`, `check`, `refs`

Add complexity as friction emerges:
- Full content + FTS if search becomes important
- Auto-rebuild if manual becomes annoying
- Extended schema for code indexing if needed

The key insight: **SQLite as cache, not source of truth.** If .index.db gets corrupted or lost, `mg index rebuild` regenerates it from files. Zero risk to actual data.
