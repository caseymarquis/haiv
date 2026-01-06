# After Action Report: Implement `mg minds new` Command

**Date:** 2026-01-06
**Task:** Create a command that scaffolds a new mind folder with proper structure

---

## Summary

Implemented `mg minds new [--name {mind}]` command that creates a new mind folder in `_new/` with startup templates. Extended the minds helper with validation, existence checking, name generation, and scaffolding functions.

## Implementation

### Helper Functions (mg_core/helpers/minds.py)

- `validate_mind_name(name)` - Validates lowercase, no underscore start, alphanumeric
- `mind_exists(name, minds_dir)` - Checks if mind already exists
- `generate_mind_name(existing)` - Uses Claude (haiku) to generate unique name
- `scaffold_mind(name, minds_dir, templates)` - Creates directory structure and files

### Extended MindPaths

Added properties for all startup files:
- `welcome_file`, `immediate_plan_file`, `long_term_vision_file`
- `my_process_file`, `scratchpad_file`, `references_file`

### Templates (mg_core/__assets__/minds/)

- `welcome.md.j2` - Task assignment template for creator to fill in
- `references.toml.j2` - External document references template

### Command (mg_core/commands/minds/new.py)

Thin wrapper that:
1. Gets or generates name
2. Validates name
3. Scaffolds mind using helper
4. Outputs next steps (edit welcome.md, run suggest_role, start mind)

### Documentation

Updated CLAUDE.md with Mind Structure section explaining:
- Directory layout (startup/, docs/, _new/, _archived/)
- Purpose of each startup file
- How startup loading works

## Key Decisions

1. **Startup files chosen:** welcome.md, immediate-plan.md, long-term-vision.md, my-process.md, scratchpad.md, references.toml
2. **Templates in assets:** Used template system for welcome.md and references.toml
3. **Role suggestion deferred:** Created placeholder for `mg minds suggest_role` command instead of listing roles inline
4. **PkgPaths.from_module():** Added classmethod to simplify getting package paths from module

## Verification

- 197 mg-core tests pass
- 21 new tests for minds new command
- 20 new tests for helper functions (validate, exists, generate, scaffold)

## Future Work

- Implement `mg minds suggest_role --name {mind}` to read welcome.md and suggest roles
- Consider `mg aar` command to simplify/normalize AAR creation

## Files Changed

**New:**
- `mg-core/src/mg_core/commands/minds/__init__.py`
- `mg-core/src/mg_core/commands/minds/new.py`
- `mg-core/src/mg_core/__assets__/minds/welcome.md.j2`
- `mg-core/src/mg_core/__assets__/minds/references.toml.j2`
- `mg-core/tests/test_minds_new.py`

**Modified:**
- `mg-core/src/mg_core/helpers/minds.py` - Added MindPaths properties and creation functions
- `mg-core/tests/test_minds_helper.py` - Added tests for new functions
- `mg/src/mg/paths.py` - Added PkgPaths.from_module()
- `CLAUDE.md` - Added Mind Structure documentation
