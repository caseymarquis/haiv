# Immediate Plan

## Active Delegations

- **arc** (session 5) — `feat(minds): autonomous mode, optional worktrees, session metadata`. Staged, welcome written. Design + implementation of autonomous launch, optional worktrees, and mode-aware tooling. May delegate sub-tasks.
- **drift** (session 7) — `fix: 1 failing test in haiv-core on Windows`. Staged, welcome written. Likely `test_task_flag_required` expecting old error string.
- **sage** (session 6) — `feat(atlas): fact extraction and review pipeline`. Staged, welcome written. Design + build extract → review → integrate pipeline for atlas. Request from leif (its-monorepo-hv) in `requests/fact-extraction-tool.md`.

## Completed

- **ember** (session 4) — `fix(minds stage): surface task vs welcome.md distinction`. Merged. One known test breakage (`test_task_flag_required`) deferred to nova's Windows test fix.
- **nova** (session 2) — `fix: Windows test compatibility`. Merged. 10 failures + 105 errors → 0. Git.run() refactored to shell=False, paths normalized with .as_posix(). Needs Linux verification.
- **drift** (session 3) — `feat(chart): project-local chart templates`. Merged. Project-local templates and example journeys.

## Committed to Main

- `6b2507c` — fix: surface AmbiguousIdentityError
- `e48df22` — hack: relaunch hv in project venv (temporary, needs proper solution)
- `a091fb3` — fix(minds stage): surface task vs welcome.md distinction in output (ember)
- `e711643` — fix: refactor Git.run() from shell string to list args (nova/ember)
- `76a3e2b` — fix: Windows test compatibility across all packages (nova)
- `f5c0260` — feat(chart): use project-local templates with copy-on-first-run (drift)
- `7bbc6a1` — feat: use project-local example journeys in hv chart (drift)

## Incoming Reference

- External project wishlist: `C:\_code_\its-monorepo-hv\users\casey\state\minds\ember\work\haiv-wishlist.md`
  - ~~`hv sessions <id>` detail view~~ — not yet delegated
  - ~~`hv minds stage` should explain task vs welcome.md distinction~~ — done (ember, session 4)
  - ~~`hv pop` AAR path should explain why it points elsewhere~~ — not yet delegated
  - Persistent async communication between minds — not yet delegated
  - ~~Control over journey example and templates~~ — done (drift, session 3)
  - `hv chart explore --clear` or debug command — not yet delegated

## Pending

- haiv-hq branch has uncommitted changes (casey-work user setup, haiv.toml wezterm change, uv.lock restructure) — not blocking worktree work but should be committed eventually
