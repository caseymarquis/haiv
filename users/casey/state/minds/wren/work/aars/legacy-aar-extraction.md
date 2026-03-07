# Legacy AAR Extraction: Open Items & Proposals

Items extracted from 17 AARs in `temp-aar/`. Historical context and completed work omitted.

---

## Open: TUI session refresh goes stale

`sessions_refresh` only runs once at TUI startup (`app.on_mount`). After that, git stats (ahead/behind/changed files) never update. As minds commit, push, or edit files, the display goes stale.

**Proposed fix:** Add a file watcher (watchdog, already a dependency) on the worktrees directory. Debounce changes and re-trigger `sessions_refresh` with git stats. Filter noise (.venv, __pycache__, etc.) to avoid excessive refreshes.

**Key files:**
- `haiv/src/haiv/wrappers/git.py` — `BranchStats.format()` for display
- `haiv-tui/src/haiv_tui/widgets/sessions.py` — uses `BranchStats.format()` for labels
- `haiv-core/src/haiv_core/commands/sessions/_index_.py` — CLI output with git stats

## Proposal: `hv doc create`

Structured document creation command with `rename` and `fix` commands for maintenance. Part of a broader document discipline vision: minds create documents via `hv doc create` which ensures consistent structure, and companion commands handle lifecycle.

This came out of the file indexing analysis, which recommended a hybrid approach: files with ` ```index ` blocks (containing `@ref-id`s and metadata) remain source of truth, with SQLite as a gitignored generated cache for queries. The document commands would ensure minds produce well-structured, indexable documents rather than ad-hoc files.

Related indexing commands that were designed but not built:
- `hv index rebuild` — regenerate cache from files
- `hv index find` — lookup by @ref-id
- `hv index check` — validate refs, find duplicates
- `hv index refs` — show reference graph
- `hv index search` — full-text search
- `hv index query` — raw SQL for power users
