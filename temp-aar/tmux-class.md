# After Action Report: Tmux Class

**Task:** Create a Tmux wrapper class for mg
**Date:** 2026-01-05

---

## Summary

Built a `Tmux` class similar to the existing `Git` class - a thin subprocess wrapper that standardizes tmux operations and is easy to mock in tests. Key feature: auto-creates the session on first use, so callers don't need to manage session lifecycle. Added `mg tmux` command for humans to attach to the mg session from a regular terminal.

---

## Deliverables

| Item | Location |
|------|----------|
| TmuxError class | `mg/src/mg/errors.py` |
| Tmux class | `mg/src/mg/tmux.py` |
| Tmux tests | `mg/tests/test_tmux.py` |
| mg tmux command | `mg-core/src/mg_core/commands/tmux.py` |
| Commits | `3ddcbcd`, `50af397` on `worktrees/main` |

---

## Design Decisions

### 1. mg_root Parameter
Session name derived from `mg_root.name` (directory name). Callers don't need to know the naming convention - just pass the repo root.

### 2. Auto-Create Sessions
`run()` calls `create_session_if_needed()` before executing. All operation methods use `run()`, so sessions are created lazily on first use.

### 3. _run() vs run() Split
- `_run()` - internal, no auto-create (for session management methods)
- `run()` - public, auto-creates session first

This avoids infinite recursion: `run()` → `create_session_if_needed()` → `has_session()` → `_run()` (not `run()`).

### 4. attach() with Guards
Uses `os.execvp()` to replace Python process with tmux. Guards prevent calling from:
- Claude Code (`CLAUDECODE` env var)
- Inside tmux (`TMUX` env var)

Raises `CommandError` for clean error messages through mg's error handling.

---

## Methods Implemented

| Method | Purpose |
|--------|---------|
| `session` (property) | Derived session name |
| `_run()` | Internal command runner |
| `run()` | Public runner with auto-create |
| `has_session()` | Check if session exists |
| `create_session_if_needed()` | Idempotent session creation |
| `list_windows()` | List windows with custom format |
| `capture_pane()` | Read pane content with line range |
| `send_keys()` | Send input to pane |
| `attach()` | Replace process with tmux attach |

---

## Tests

| Test Class | Count | Coverage |
|------------|-------|----------|
| `TestTmuxInit` | 2 | Session name derivation |
| `TestTmuxRun` | 2 | Command building, error handling |
| `TestCreateSessionIfNeeded` | 2 | Create/skip logic |
| `TestHasSession` | 2 | Exists/missing detection |
| `TestListWindows` | 3 | Parsing, format, empty |
| `TestCapturPane` | 3 | Target, line range |
| `TestSendKeys` | 4 | Enter, target, quote escaping |
| `TestAttach` | 3 | Claude Code guard, tmux guard, exec |

Total: 21 tests passing.

---

## Manual Testing Performed

1. Created test session via `create_session_if_needed()`
2. Listed windows - returned `['0:bash']`
3. Sent keys - `echo hello from tmux test`
4. Captured pane - saw command and output
5. Verified attach guard blocks from Claude Code
6. Cleaned up test session

---

## Open Items

- `mg tmux` command has no tests (simple passthrough, tested via Tmux class tests)
- No Windows support (tmux is Unix-only, `os.execvp()` behaves differently)
