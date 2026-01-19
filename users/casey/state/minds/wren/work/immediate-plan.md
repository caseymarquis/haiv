# Immediate Plan

**Updated:** 2026-01-19

---

## Current State

Minds cleaned up and restructured:
- Only wren and sage remain (others removed - no accumulated experience)
- New folder structure: `work/` + `home/` replaces `startup/`
- Terminology updated: "assign" not "spawn", "recover" for recovery commands

---

## Completed This Session

1. **Terminology cleanup** - Replaced "spawn" with "assign" across codebase
2. **Role docs updated** - Clarified when worktrees are needed (code work only)
3. **Mind cleanup** - Removed empty minds from `_new/`, kept wren + sage
4. **Folder restructure** - Migrated to new `work/` + `home/` structure

---

## New Folder Structure

```
minds/{mind}/
├── work/           # All assignment/role docs (cleared between assignments)
│   ├── welcome.md
│   ├── immediate-plan.md
│   ├── long-term-vision.md
│   ├── my-process.md
│   └── scratchpad.md
├── home/           # Personal continuity only (persists)
│   └── journal.md
└── references.toml
```

---

## Next Steps

### 1. Update `mg become` command
Load files from `work/` + `home/` instead of `startup/`

### 2. Update `mg minds stage` command
Create new structure when scaffolding minds

### 3. Create PM for continuity work
- Retasking system (assigned/available status)
- Journaling support (`mg journal`)
- Upward reporting guidance

---

## Paused Work

| Mind | Task | Status |
|------|------|--------|
| sage | `mg minds suggest_role` | Design done, WIP committed |

---

See `docs/problems.md` for full problem list.
