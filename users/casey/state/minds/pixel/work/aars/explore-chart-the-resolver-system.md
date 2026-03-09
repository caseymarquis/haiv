# AAR: explore: chart the resolver system

## Summary

Explored the resolver system end-to-end and charted it for the atlas. The resolver system transforms raw string values (like `"pulse"`) into domain objects (like a `Mind`) during command context building. It operates in three layers: infrastructure (discovery and composition), concrete resolvers (thin bridges to domain helpers), and consumer (`build_ctx()` in args.py).

### Deliverables

- Journey: `atlas/journeys/the-resolver-system/` — 5 entries (research log + 4 exploration entries)
- Map update: `atlas/maps/haiv-lib.md` — added "The Translators" section covering resolver infrastructure and consumer
- Map update: `atlas/maps/haiv-core.md` — added "The Interpreters" section, moved resolvers from Uncharted
- Quest board: Completed The Resolver Mystery, updated The Context Factory description

## Key Decisions

- Explored top-down (infrastructure → concrete resolvers → consumer) rather than bottom-up. This worked well — seeing the contract first made the implementations immediately legible.
- Renamed journey entries from bare `002.md` to descriptive `002-the-infrastructure.md` for consistency with existing journeys in eras.
- Left `helpers/minds.py` and the `Mind` class unexplored — that's Pixel's territory in the `how-commands-talk-to-minds` journey. Noted the connection without duplicating.
- Updated The Context Factory quest rather than completing it — I explored the resolver dispatch side of `args.py` but the full flag parsing and context assembly deserves its own dive.

## Open Items

- The Context Factory quest is still open. The resolver side is charted, but `build_ctx()` does more (flag parsing, Paths construction) that nobody has explored yet.
- No code was written — this was pure exploration. Nothing to test or verify beyond the documentation itself.

## Commits and Files Changed

- a623173 add journey: the-resolver-system (pulse)
  Key files: `atlas/journeys/the-resolver-system/` (5 files), `atlas/maps/haiv-lib.md`, `atlas/maps/haiv-core.md`, `atlas/quests.md`
