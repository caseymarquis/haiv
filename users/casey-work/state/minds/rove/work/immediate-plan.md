# Immediate Plan

## Active Delegations

- **nova** (session 2) — `fix: Windows test compatibility`. Staged, welcome written. Investigating path separator failures in test_become/test_mine and 88 errors in test_minds_stage/test_pop.
- **drift** (session 3) — `feat(chart): project-local chart templates`. Staged, welcome written. Moving chart templates to atlas/templates/ with copy-on-first-run.
- **ember** (session 4) — `fix(minds stage): surface task vs welcome.md distinction`. Staged, welcome written. Improving stage output to explain two-audience model.

## Committed to Main

- `6b2507c` — fix: surface AmbiguousIdentityError
- `e48df22` — hack: relaunch hv in project venv (temporary, needs proper solution)

## Incoming Reference

- External project wishlist: `C:\_code_\its-monorepo-hv\users\casey\state\minds\ember\work\haiv-wishlist.md`
  - ~~`hv sessions <id>` detail view~~ — not yet delegated
  - ~~`hv minds stage` should explain task vs welcome.md distinction~~ — delegated to ember (session 4)
  - ~~`hv pop` AAR path should explain why it points elsewhere~~ — not yet delegated
  - Persistent async communication between minds — not yet delegated
  - Control over journey example and templates — partially addressed by drift (session 3)
  - `hv chart explore --clear` or debug command — not yet delegated

## Pending

- haiv-hq branch has uncommitted changes (casey-work user setup, haiv.toml wezterm change, uv.lock restructure) — not blocking worktree work but should be committed eventually
