# AAR: Extract open items and proposals from legacy AARs

## Summary

Read all 17 AARs in `temp-aar/` and extracted forward-looking items. Of 13 open items and 4 proposals initially identified, only 2 survived review with Casey — most were already resolved, in progress, or no longer relevant.

## Key Decisions

- Omitted items from `memory-persistence-design` (hv start/wake/mine, folder structure) — confirmed implemented by later AARs
- Omitted `hv sessions` command — `branch-stats-display` AAR confirms it exists
- Kept full context for surviving items since source AARs will be deleted
- Claude Code hook integration (largest item) dropped — already in progress

## Open Items

None.

## Commits and Files Changed

- 7a3d93e extract: open items and proposals from 17 legacy AARs
  Key files: `users/casey/state/minds/wren/work/aars/legacy-aar-extraction.md`
