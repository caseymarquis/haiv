# 001 — Setting Out

**Explorer:** Luna
**Date:** 2026-03-07
**Goal:** Build `hv chart` — a command that sends a mind exploring and journaling through the codebase.

---

## Why haiv-core?

I need to build a new `hv` command. CLAUDE.md says commands resolve `haiv_core → haiv_project → haiv_user`, where core is shared across all communities. A charting/exploration tool benefits everyone, so it belongs in core.

## The monorepo at `worktrees/main/`

Four haiv packages: `haiv/`, `haiv-cli/`, `haiv-core/`, `haiv-lib/`, `haiv-tui/`. I don't yet know the boundaries between them — what lives where and why. That's something the atlas should eventually capture, but right now I just need to find where commands are defined in haiv-core.

There are also `mg-*` directories — remnants of a recent rename (mg → haiv). They're probably not relevant but worth knowing they exist if you see stale references.

**Next:** I'm heading into `haiv-core/` to find existing commands and learn the pattern for building new ones.
