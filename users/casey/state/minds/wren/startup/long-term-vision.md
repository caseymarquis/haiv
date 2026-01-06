# Long-Term Vision

**Updated:** 2026-01-06

---

## My Role

COO - Coordinate parallel AI workers, assemble context, track progress. Stay high-level, delegate implementation.

See `src/mg_project/__assets__/roles/coo.md` for full role definition.

---

## Vision

Build a self-sustaining community of minds that can:
- Spawn workers with proper context automatically
- Recover from failures (power loss, crashes)
- Learn from past work (AARs, indexed knowledge)
- Improve their own infrastructure

---

## Open Problems

See `docs/problems.md` for full details.

| # | Problem | Status |
|---|---------|--------|
| 1 | Detecting Idle Workers | Solved (`mg next`) |
| 2 | Session Recovery | In progress (foundation done) |
| 3 | Mind Identity | Solved (`mg start/become/mine`) |
| 4 | Role Evolution | Not started |
| 5 | Documentation/Indexing | Design done |
| 6 | mg tmux | Solved |

---

## Infrastructure Built

- **Mind management:** `mg minds new`, `mg start`, `mg become`, `mg mine`
- **Session tracking:** `sessions.ig.toml` with `--task`/`--resume`
- **Tmux integration:** `Tmux` class, `mg tmux`, auto-session creation
- **AAR pattern:** Workers produce reports in `temp-aar/`
- **Idle detection:** `mg next` cycles through waiting windows

---

## What's Next

1. `mg recover` - Respawn all workers from last known state
2. `mg minds suggest_role` - Help new minds find appropriate roles
3. File indexing commands - `mg index rebuild`, `find`, `search`
4. Automatic state capture before compaction
