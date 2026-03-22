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

### TUI data model redesign (2026-03-22)

Completed with Casey. Major architectural changes:

**Architecture:** Three-layer data flow — raw data (gathered from external sources) → assembly (pure functions, raw→DTO) → widget rendering (DTOs only). Each layer has clear ownership.

**Key decisions made:**
- `TuiModel` holds only raw data sections (`SessionsRaw`, `GitRaw`, `ActiveMindRaw`), not display concerns
- `write_raw()` replaces the old mutator-based `write()` — callers pass section kwargs, server replaces non-None sections wholesale
- No version checking on writes — dirty set tracks what changed, drained atomically by the poll loop
- `TuiModelSection` base class eliminated — sections are plain dataclasses, versioning is server-internal via `Atom<set[str]>`
- `ConcurrencyError` removed entirely — independent writers can never conflict
- DTOs and assembly functions co-located in each widget file (widget at top, DTO/assembly below)
- `HudSection` and `ErrorsSection` removed from the model — HUD assembles from raw sessions + active mind

**TODO:** Widget dependency injection — widgets currently reach through `self.app` for store/terminal/paths/client. Should declare dependencies explicitly for type safety and testability. This is the remaining source of type errors in haiv-tui.

**TODO:** Type-safe signal subscriptions — use reflection on `TuiModel` fields to generate signal names rather than raw strings. Considered during redesign, deferred.

**TODO:** Publishing mechanism — TUI will publish derived state (e.g. active mind) for consumption by `hv` commands. Remote clients push raw data in; the TUI decides what to publish out. Design sketch: single function on the Textual thread that polls assembled data and publishes cheaply.

## Things to Remember

- Use `hv sessions` for live state, not notes
- `flatpak run org.wezfurlong.wezterm` is the wezterm command
- `hv tui debug` shows WezTerm pane layout
