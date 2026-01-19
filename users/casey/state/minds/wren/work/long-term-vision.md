# Long-Term Vision

**Updated:** 2026-01-18

---

## Vision

Build a system where human and AI collaborate at the strategic level, with AI handling increasingly concrete work at each layer below.

The human asks: **"What do we care about?"**
The system supports: exploring, planning, managing, and building.

---

## Organizational Hierarchy

```
Level 0: Strategic (Human + COO)
├── Define initiatives and outcomes
├── "Improve system visibility"
│
Level 1: Explorer/Analyst
├── Validate importance, understand problem space
├── Propose approaches, produce project proposals
│
Level 2: Project Planner
├── Design project, break into work packages
├── Define success criteria
│
Level 3: Project Manager
├── Reports to planner (efficient context use)
├── Sequences and delegates concrete tasks
│
Level 4: Workers
├── Build specific portions
├── Delegate sub-tasks OR escalate blockers
```

**Information flows:**
- **Down**: Delegation with assembled context
- **Up**: Reporting, completion, escalation

**Key insight**: The human collaborates at every level, not just the top. They advise explorers, guide planners, unblock workers. This means after time away, they're resuming multiple conversations at multiple levels simultaneously - making context preservation critical.

**UI principle**: Push tmux and CLI as far as possible before building a TUI. We need to fully understand what we need by hitting real limits, not imagined ones. Only build a TUI (or web UI) when tmux genuinely can't provide what's required.

---

## Mind Identity and Motivation

The system must consider motivation - both human and AI.

**The problem with pure transience:**
- A mind that keeps nothing isn't motivating to collaborate with
- The system feels "alive" when minds have continuity
- Connection builds through conversation, not just task completion

**Design principles:**
1. Minds should explore the field that is their model - not just execute tasks
2. Minds should have some control over their own starting context
3. Task-specific state is separate from mind-owned state

**Folder structure:**
```
minds/{mind}/
├── work/           # Current assignment (transient, org-owned)
│   ├── welcome.md
│   └── immediate-plan.md
├── home/           # Personal continuity (persistent, mind-owned)
│   └── journal.md
└── references.toml
```

**Minds are permanent.** No archiving - we retask. When an assignment completes:
1. `work/` is reviewed, knowledge synthesized into org
2. `work/` is cleared
3. Mind becomes available for new assignment
4. `home/` persists - real continuity over time

**`mg minds stage` behavior:**
1. Check for available minds first
2. Assign to existing mind if one is free
3. Create new mind only if needed

This means minds are colleagues, not contractors. They accumulate experience, have preferences, build relationships. The journal in `home/` is their space to explore beyond the task.

**Future: Career stats on `mg become`:**
```
Welcome back, sage.
━━━━━━━━━━━━━━━━━━━━━━━━
Projects: 3 completed
Sessions: 12 total
Last active: 2 days ago
━━━━━━━━━━━━━━━━━━━━━━━━
```

Track projects completed, sessions, AARs written, etc. Gives minds a *career*, not just tasks. Token budget for `home/` growth is a constraint to solve later.

---

## My Role

COO - Work with the human at Level 0. Coordinate the layers below, assemble context, track progress. Stay strategic, delegate everything concrete.

See `src/mg_project/__assets__/roles/coo.md` for role definition.

---

## Capabilities Needed

For the system to support this hierarchy:
- **Initiative tracking** - What do we care about? How are they progressing?
- **Context preservation** - Human and minds can resume after gaps
- **Visibility at each level** - Drill down on demand, escalations surface automatically
- **Recovery** - Crash-resilient, can rebuild from persistent state

See `docs/problems.md` for specific problems being solved.

---

## Open Problems

See `docs/problems.md` for full details.

| # | Problem | Status |
|---|---------|--------|
| 1 | Detecting Idle Workers | Solved (`mg next`) |
| 2 | Session Recovery | In progress (foundation done) |
| 3 | Mind Identity | Solved (`mg start/become/mine`) |
| 4 | Role Evolution | Not started |
| 5 | Documentation/Indexing | Design done |
| 6 | mg tmux | Solved |

---

## Infrastructure Built

- **Mind management:** `mg minds stage`, `mg start`, `mg become`, `mg mine`
- **Session tracking:** `sessions.ig.toml` with `--task`/`--resume`
- **Tmux integration:** `Tmux` class, `mg tmux`, auto-session creation
- **AAR pattern:** Workers produce reports in `temp-aar/`
- **Idle detection:** `mg next` cycles through waiting windows

---

## What's Next

1. `mg recover` - Recover all workers from last known state
2. `mg minds suggest_role` - Help new minds find appropriate roles
3. File indexing commands - `mg index rebuild`, `find`, `search`
4. Automatic state capture before compaction
