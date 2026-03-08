# AAR: Build a tool to help index the haiv codebase

## Summary

Built `hv chart` — a haiv-core command that briefs minds on how to navigate and extend a shared atlas of the codebase. Instead of an automated indexer, we created a human/mind-driven exploration system where minds journal their way through the code and leave maps for those who follow.

### Deliverables

- `hv chart` command: Supports optional `--goal` flag. Outputs atlas location, navigation advice (maps → quests → journals → explore), charting rules, and reward descriptions. Creates atlas directory structure on first run.
- Atlas structure: `atlas/welcome.md` (how it works), `quests.md` (quest board), `journeys/` (exploration narratives), `maps/` (distilled reference docs), `journeys/eras/` (archived old-style journeys).
- First map: `atlas/maps/haiv-lib.md` — tree overview of haiv-lib with four named landmarks.
- Three journeys: building-the-chart-command (4 entries), testing-the-chart-command (3 entries), the-routing-table (4 entries).
- Reward system: Landmark, Trade Route, Compass, Inbeeyana Combs. Rewards earn naming rights on maps.
- Title system: Nominated (not self-assigned). Dragon Slayer reserved.
- Mystery system: Flag contradictions between atlas and code for future investigation.
- 8 tests, all passing. Full haiv-core suite (213 tests) clean.

## Key Decisions

- **Atlas over automated index**: Casey steered toward exploration-as-documentation rather than programmatic indexing. The atlas grows through genuine curiosity, not scraping.
- **Two layers — journeys and maps**: Journeys are historical and immutable (how understanding was built). Maps are living reference docs (what we know now). Separates discovery from knowledge.
- **Entry 001 is a research log**: Before exploring, document what you searched for in the atlas and what was missing. This creates feedback on the atlas itself.
- **Forward pointers**: Every entry ends with "where are you going next?" — creates a trail through the journey.
- **Rewards earn nicknames**: Completing quests lets you name things on maps. This gives exploration lasting creative impact and makes maps have personality.
- **Mysteries over corrections**: When something in the atlas doesn't match reality, post a mystery to the quest board. Don't silently fix — the investigation itself has value.
- **Maps use tree + headers, not tables**: A tree at the top shows the territory at a glance; headers below provide detail. Functional names first, nicknames second.
- **Search precedence discovery**: While completing The Routing Table quest, found that CLI search order is user → project → core (highest precedence first), which is the opposite of the conceptual layering described in CLAUDE.md.

## Open Items

- Atlas content lives on haiv-hq branch, command lives in luna worktree — both need to land.
- Three open quests: The Port City (Landmark), The Resolver Mystery (Compass), The Context Factory (Trade Route).
- One open mystery: The Fifth Package (Inbeeyana Combs).
- Early journey entries (001-003 of "building-the-chart-command") predate current journaling style — candidates for first era archive.
- The CLAUDE.md says command resolution is "haiv_core → haiv_project → haiv_user" but actual search precedence is user → project → core. This could confuse future minds. Consider clarifying.

## Commits and Files Changed

- 79412e0 feat: add hv chart command for atlas-based codebase exploration
  Key files: `haiv-core/src/haiv_core/commands/chart.py`, `haiv-core/tests/test_chart.py`

Atlas files (on haiv-hq, uncommitted):
- `atlas/welcome.md`, `atlas/quests.md`, `atlas/maps/haiv-lib.md`
- `atlas/journeys/building-the-chart-command/` (4 entries)
- `atlas/journeys/testing-the-chart-command/` (3 entries)
- `atlas/journeys/the-routing-table/` (4 entries)
