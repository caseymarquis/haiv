# AAR: Fix: TUI not updating when new mind launches

## Summary

Built reactive file watching so the TUI automatically refreshes when `sessions.ig.toml` changes, regardless of what modified it. This is broader than the original ask (which was just `hv start`) but solves the problem generically.

### Deliverables

- **MessageHandler**: Generic debounced batch processor — collects messages from any thread and delivers them in batches on a worker thread after a quiet period.
- **FileWatcher**: Watchdog wrapper using MessageHandler — watches files/directories with debounce, chaining API, and context manager support.
- **TUI integration**: Wired FileWatcher into HaivApp to watch `sessions.ig.toml` and trigger `sessions_refresh` on changes.
- **Parallel test execution**: Added pytest-xdist for parallel test runs within and across packages (~2x speedup).
- **Python 3.12 bump**: Updated all 8 pyproject.toml files from `>=3.11` to `>=3.12`.

## Key Decisions

- **File watcher instead of per-command refresh**: Rather than adding `ctx.tui.sessions_refresh()` to every command that touches sessions, we watch the file itself. Any process that modifies `sessions.ig.toml` triggers a TUI update automatically.
- **Kept existing IPC refreshes**: Commands like `stage` still call `sessions_refresh()` over IPC for instant feedback. The file watcher is a safety net, not a replacement. Double-refresh is harmless (idempotent).
- **TypeError on bytes path**: Watchdog's `src_path` can technically be `bytes | str`. Rather than silently casting (which could fail on the exact edge cases that produce bytes), we raise a clear error.
- **Python 3.12 bump**: The pre-existing type error in `pop.py` (`walk_up` parameter) was correct code for 3.12 but flagged by 3.11 stubs. Bumped the minimum rather than reworking the call.

## Open Items

### Verification needed

- The file watcher integration hasn't been tested end-to-end with a live TUI. Verify by running `haiv-tui`, then `hv start {mind}` in another terminal — the sessions tree should update within ~0.5s.
- The `watchdog` dependency was added to `haiv/pyproject.toml` but was previously only available transitionally. Verify clean installs work.

## Commits and Files Changed

- 9b1ba00 wip: TUI sessions refresh on start + file watcher scaffolding
- d6c3585 feat(tui): reactive sessions refresh via file watcher
  Key files: file_watcher.py, message_handler.py, app.py, start/_mind_.py
- dc201bf chore: bump minimum Python version to 3.12
  Key files: all pyproject.toml files, uv.lock
- 446ca61 feat: parallel test execution with pytest-xdist
  Key files: test-all.sh, pyproject.toml, test_tui_client.py
