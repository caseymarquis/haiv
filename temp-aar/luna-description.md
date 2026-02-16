# AAR: mg Hook Description, Source Tracking, and Trust Guard

## What was implemented

### Description parameter (original assignment)

**`mg/src/mg/mg_hooks.py`** (public API):
- `MgHookHandler` protocol: added `_mg_hook_description: str` and `_mg_hook_source: str`
- `mg_hook()`: added required keyword-only `description` parameter, stamps `_mg_hook_description`
- Updated docstring examples

**`mg/src/mg/_infrastructure/mg_hooks.py`** (infrastructure):
- `MgHookRegistry` typed with `MgHookHandler` instead of `Callable`
- `emit()`: prints `"{description} ({relative_source})"` before each handler runs
- `emit()`: raises `RuntimeError` if handler is missing `_mg_hook_description` or `_mg_hook_source` (refuses to run tampered handlers)

**`src/mg_project/mg_hook_handlers/sync_packages.py`** (mg-state):
- Added `description="Syncing packages"` to `@mg_hook`
- Removed manual `ctx.print()` (system handles visibility now)

### Scope expansions (discussed with Casey during session)

**Source tracking**: `_mg_hook_source` stamped on handlers during `configure_mg_hooks()` with the absolute file path. At emit time, relativized via `ctx.paths.root` for display. This tells both minds and humans exactly where a hook lives.

**Trusted package guard**: `_TRUSTED_HOOK_PACKAGES = {"mg_core", "mg_project", "mg_user"}` — hardcoded set checked in `configure_mg_hooks()`. Any package root not in this set raises `RuntimeError`. This ensures third-party packages (when they arrive) cannot silently run hooks without an explicit trust mechanism being designed first.

**Strict handler validation**: `emit()` refuses to run any handler missing the required protocol attributes. No fallbacks, no `getattr` defaults — if it's been tampered with, it doesn't run.

## Test results

- 875 total tests passing (658 mg + 199 mg-core + 18 mg-cli)
- 48 hook tests (up from 39), including:
  - Description stamping, source stamping
  - Emit prints description + relative source path
  - Rejects handlers missing description, source, or both
  - Rejects untrusted packages, even mixed with trusted ones
- mg type check: clean
- mg-core type check: 1 pre-existing error (walk_up stub)
