# Immediate Plan

## Current State

- Code changes complete and merged to main
- Tests pass, type checking passes
- `mg become wren` verified working
- `mg minds stage` creates correct structure

## Remaining Fixes (on main branch)

### Already edited (uncommitted):
1. `mg-core/src/mg_core/commands/minds/new.py` - docstring and output message
2. `mg-core/src/mg_core/__assets__/minds/references.toml.j2` - comment text

### Still need to fix:
3. `mg-core/src/mg_core/__assets__/init/CLAUDE.md.j2` - lines 83-108 "Your Home" section
   - Update folder structure diagram (startup/ → work/, home/, references.toml at root)
   - Update explanatory text below diagram
   - Remove references to docs/ at top level (now work/docs/)

4. `mine.py` docstring line 3 - "startup context path" → "work directory path" (minor)

### Then:
5. Commit all fixes on main
6. Run tests to verify nothing broke
7. Clean up testmind: `rm -rf users/casey/state/minds/_new/testmind`
8. Update AAR if needed

## Files Changed Summary

Main commit (84b32be):
- mg/src/mg/paths.py
- mg/src/mg/helpers/minds.py
- mg-core/src/mg_core/commands/become/_mind_.py
- mg-core/src/mg_core/commands/mine.py
- mg-core/src/mg_core/resolvers/mind.py
- All associated tests

Follow-up fixes (uncommitted):
- mg-core/src/mg_core/commands/minds/new.py
- mg-core/src/mg_core/__assets__/minds/references.toml.j2
- mg-core/src/mg_core/__assets__/init/CLAUDE.md.j2 (TODO)
