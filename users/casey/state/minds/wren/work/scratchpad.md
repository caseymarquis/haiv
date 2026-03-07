# Scratchpad

Rough thinking, debugging notes, half-formed ideas.

---

## Current Session Notes

### Session close-out design (2026-02-12)

Key decisions made with Casey:
- **Always worktree, always commit first** — eliminates mode complexity
- **Worker merges directly** — human was there during work, review happened live
- **Base branch recorded at staging** — close-out always knows where to merge
- **Guided steps in `hv pop`** — checklist first, then `--merge` and `--session` as explicit steps

### Hooks system (2026-02-14)

Echo designed and implemented with Casey. Skeleton-first approach — echo laid out the API surface, then pixel filled in the implementations. Five levels of delegation depth worked smoothly.

### Spark's research findings (2026-02-14)

Claude Code hooks fully cover status detection — 6 lifecycle events map to our states (idle, approval, working, finished, session start/end). See `temp-aar/claude-hook-integration.md`. No pane scraping needed.

### Process refinements

- Welcome template now says "discuss first, no solo planning tools"
- Task descriptions: landscape and destination, not route
- Research deliverables go in `temp-aar/`, not `work/` (survives pop)
- `scaffold_mind` with `skip_existing` handles reused minds non-destructively

## Things to Remember

- Use `hv sessions` for live state, not notes
- `flatpak run org.wezfurlong.wezterm` is the wezterm command
- `hv tui debug` shows WezTerm pane layout
