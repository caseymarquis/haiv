# AAR: Build relay infrastructure for cross-venv command execution

## Summary

Pivoted from relay infrastructure to a full package rename (mg → haiv). The rename surfaced during design discussion when we discovered the `mg` package name collides with an existing PyPI package, and Casey wanted to improve the project identity regardless. The relay work remains unbuilt but the rename was a necessary prerequisite — building relay on names about to change would have been wasted effort.

### Deliverables

- **Package rename**: mg → haiv, mg-core → haiv-core, mg-cli → haiv-cli, mg-tui → haiv-tui, mg_project → haiv_project, mg_user → haiv_user
- **CLI command**: mg → hv
- **Control plane branch**: mg-state → haiv-hq (content updated, git branch rename pending)
- **Cleanup**: Removed tmux wrapper, fix command, and dead code. Fixed pre-existing type errors. Added pytest-xdist to all package dev deps.
- **Tooling**: Built and used rename-paths.py (regex-based git mv, longest-path-first), removed after use.

## Key Decisions

- **haiv as the name**: Human/AI + hive. Short, not taken on PyPI, good metaphor for collaborative minds.
- **hv as the CLI command**: Short to type, not taken on Linux or Windows.
- **haiv-hq for control plane branch**: Avoids ambiguity with the `haiv` package. Clear meaning.
- **haiv_project / haiv_user (not hv_)**: Consistency with the haiv namespace won over brevity.
- **"mind" stays as the agent term**: The "hive mind" association becomes a feature when HAI (Human/AI) is the foundation.
- **Relay design decisions** (discussed but not implemented): Always relay non-core commands (no venv comparison optimization). Use sys.prefix to detect current venv. Pass target venv path for comparison to prevent recursive relaunching.

## Open Items

- **Relay infrastructure is unbuilt**: IPC abstraction, haiv.relay module, and CLI relay dispatch are all unstarted. This is the next task for whoever picks it up.
- **`hv` command not installable yet**: Pixel branch needs to merge to main, then `hv dev install --branch main` can bootstrap it. The old `mg` wrapper works temporarily.
- **Git branch not yet renamed**: The branch is still called `mg-state` in git. Content says `haiv-hq`. Renaming the branch requires coordination.
- **haiv_hook_handlers on mg-state**: Directory renamed but internal code may still reference `mg_hook_handlers` patterns — worth a grep after merge.

## Commits and Files Changed

Pixel branch:
- 0bcc241 rename mg → haiv across all package internals (138 files)
- 9106529 rename mg → haiv: file/directory renames, fixes, and cleanup (176 files)
- 7ce39e7 remove rename-paths.py utility

mg-state:
- 14f8260 rename mg → haiv across mg-state (88 files)
- 749764b rename remaining mg references in filenames (role files, hook handlers)
