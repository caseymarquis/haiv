# AAR: refactor(atlas): reorganize atlas structure

## Summary

Reorganized `atlas/maps/` from a flat layout with ambiguous subdirectories into a Python-module-style nested structure. Each package is now a directory with an `overview.md`, and subtopics (commands, helpers) nest under their parent package. Updated all internal cross-references.

## Key Decisions

- Adopted `overview.md` as the entry point for each directory, analogous to Python's `__init__.py`. Small subtopics are sibling files; big subtopics are subdirectories with their own `overview.md`.
- Moved `commands/` under `haiv-core/` and `helpers/` under `haiv-lib/` to make ownership explicit — previously they floated at the top level with no clear parent.

## Open Items

None. This was a straightforward file reorganization with no code changes.

## Commits and Files Changed

- de3cd16 sync haiv-hq: reorganize atlas maps, new minds, journeys, and state updates
  Key files: all 9 files under `atlas/maps/` (moved + 3 cross-reference edits in haiv-core/overview.md, haiv-lib/overview.md, helpers/sessions.md)
