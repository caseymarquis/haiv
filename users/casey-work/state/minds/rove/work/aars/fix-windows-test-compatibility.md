# AAR: fix: Windows test compatibility

## Summary

Fixed all Windows test failures across haiv-core, haiv-lib, and haiv-cli. Starting state: 10 failures + 105 errors. Ending state: 0 failures, 0 errors, 1 intentional skip.

### Deliverables

- **Git.run() refactor** (delegated to ember): Changed from `shell=True` string to `shell=False` list args across 78 call sites. Eliminated 105 errors caused by cmd.exe not recognizing single-quote string delimiters.
- **Path display normalization**: Added `Path.as_posix()` to all user-facing path output in production code — become, mine, pop, stage, help, haiv_hooks, identity.
- **Test environment fixes**: Fixed 5 test assumptions about Unix environment.
- **Role doc update**: Added cross-platform guidance (`.as_posix()` for display paths) to `haiv-python-dev.md`.

## Key Decisions

- **`shell=False` with list args over fixing quoting** — Rather than patching quoting conventions, eliminated the shell entirely. Follows the existing WezTerm wrapper pattern. More secure, faster, and cross-platform by nature.
- **`.as_posix()` in production code, not test workarounds** — Path display should be consistent regardless of platform. Forward slashes work everywhere and are more readable.
- **Single `skipif` for AF_UNIX test** — Unix domain sockets don't exist on Windows, and Windows named pipes don't leave stale files. The stale socket recovery scenario is genuinely untestable on Windows.
- **Preserve PATH in `clear=True` tests** — Tests that cleared env to remove a single variable (HV_SESSION, TERM_PROGRAM) were accidentally wiping PATH, breaking subprocess calls. Fixed by copying env and removing only the target variable.

## Open Items

- Linux verification needed — all changes are cross-platform by design, but should be confirmed on Linux CI.
- The `hv pop` and `hv help` commands still show backslash paths when run from main worktree (pre-merge). Will resolve once nova's changes merge.

## Commits and Files Changed

- e711643 fix: refactor Git.run() from shell string to list args (ember)
  Key files: git.py, init.py, pop.py, stage.py + all test files with git.run() calls
- 76a3e2b fix: Windows test compatibility across all packages
  Key files: become/_mind_.py, mine.py, pop.py, stage.py, help.py, haiv_hooks.py, identity.py, test_minds_stage.py, test_paths.py, test_terminal_manager.py, test_tui_server.py, test_command_sources.py
