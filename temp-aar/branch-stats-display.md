# After Action Report: Git Branch Stats in TUI Sessions Widget

**Date:** 2026-02-14
**Task:** Debug git branch stats not showing in TUI sessions widget

---

## Summary

Branch stats (ahead/behind/changed files) were implemented but appeared invisible in the TUI. The root cause was a rendering clarity issue — the original display showed only a small `✓` at the end of long labels, making stats easy to miss. We improved the display and extracted shared formatting logic.

## What We Did

1. **Diagnosed the problem** — Confirmed data pipeline (Git → sessions_refresh → server → freeze → store → widget) works correctly end-to-end. Built a Textual sandbox app proving the rendering infrastructure is sound.

2. **Improved stats display** — Changed from showing only non-zero values (lone `✓` for clean branches) to always showing `↑N ↓N ✓/~N`. Added `(no branch)` for sessions without branch tracking.

3. **Extracted shared formatting** — Added `BranchStats.format()` method so the TUI widget and `mg sessions` CLI command share the same display logic.

4. **Added stats to `mg sessions`** — The CLI command now computes and displays git stats, matching the TUI output.

## What's Left

### Session refresh is stale after initial load

`sessions_refresh` only runs once at TUI startup (`app.on_mount`). After that, git stats never update. As minds commit, push, or edit files, the display goes stale.

**Proposed fix:** Add a file watcher (watchdog, already a dependency) on the worktrees directory. Debounce changes and re-trigger `sessions_refresh` with git stats. Filter noise (.venv, __pycache__, etc.) to avoid excessive refreshes.

### Silent exception swallowing in sessions_refresh

```python
try:
    stats = git.branch_stats(s.branch, s.base_branch)
except Exception:
    pass
```

This makes debugging harder. Should at minimum log to the TUI's internal error sink.

### `mind_launch` doesn't pass git for refresh

`action_launch_session` in the widget calls `mind_launch` without `git=`, so launching a mind re-runs `sessions_refresh` without stats, briefly resetting them to defaults until the next refresh.

## Key Files

| File | Change |
|------|--------|
| `mg/src/mg/wrappers/git.py` | Added `BranchStats.format()` |
| `mg-tui/src/mg_tui/widgets/sessions.py` | Uses `BranchStats.format()` for labels |
| `mg-core/src/mg_core/commands/sessions/_index_.py` | Added git stats to CLI output |
