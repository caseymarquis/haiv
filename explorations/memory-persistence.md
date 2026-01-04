```index
@memory-persistence-exploration
Exploration of memory persistence for long-running minds. Covers alpha project
learnings, role vs mind state separation, and proposed architecture. See @memory-persistence for spec.
```

# Memory Persistence for Long-Running Minds

**Type:** Exploration Document
**Author:** Reed
**Date:** 2026-01-04

---

## Problem Statement

Long-running minds (like Wren, the COO) lose context during compaction. A fresh Claude instance doesn't know:
- Who it is
- What role it plays
- What it was working on
- Where its state lives

Without memory persistence, every compaction resets the mind to a blank slate.

---

## Design Goals

The new system separates two distinct concepts:

### 1. Role (shareable blueprint)
- How to operate, what to prioritize, communication style
- Reusable across many minds and projects
- Example: "analyst" role can be assigned to any mind doing analysis work
- Lives in `__assets__/roles/` in any mg package
- Human-maintained, evolves based on what works

### 2. Long-Running Mind (particular work)
- Accumulated context about specific responsibilities
- Task history, decisions made, relationships, domain knowledge
- Example: Wren knows the problem backlog, has opinions on priorities
- Lives in `users/{user}/state/minds/{mind}/`
- Mind-maintained (with human guidance)

**Why this separation matters:**
- Roles become shareable artifacts - learnings transfer across projects
- Short-lived workers can use roles without needing mind state
- Long-running minds get role + their accumulated context
- Roles can be versioned, improved, and packaged

---

## Alpha Project Context

The alpha system handled memory persistence well but was optimized for long-running minds only. Key characteristics:
- Context files were tightly coupled to individual minds
- No separation between role (reusable) and mind state (particular)
- Worked excellently for its purpose, but artifacts weren't shareable

**What transfers:** The mechanics of saving/loading context, the importance of structure
**What's different:** Explicit role/mind separation, shareable roles across packages

---

## Proposed Architecture

### Role Storage (Shareable)

Roles live in `__assets__/roles/` within any mg package:

```
mg_core/
└── __assets__/
    └── roles/
        └── default.md          # baseline role

mg_project/
└── __assets__/
    └── roles/
        └── analyst.md          # project-specific role
        └── coo.md

mg_user/
└── __assets__/
    └── roles/
        └── my-variant.md       # user customization
```

Resolution follows mg convention: mg_core → mg_project → mg_user (later levels can override).

A role is a markdown file explaining:
- Purpose and responsibilities
- How to approach work
- Communication style
- Document formats (for analyst: exploration vs spec)

### Mind State Storage (Particular)

Mind-specific state lives in startup folder:

```
users/{user}/state/minds/{mind}/
└── startup/
    ├── references.toml      # pointers to external docs
    ├── identity.md          # who I am, my responsibilities
    ├── current-focus.md     # what I'm working on now
    └── ...                   # any other context docs
```

**identity.md** - The mind's particular context:
- Name and responsibilities (Wren is the COO)
- Key relationships (reports to Casey, delegates to workers)
- Domain knowledge accumulated over time
- Preferences and working style

**current-focus.md** - Ephemeral working state:
- Active tasks and priorities
- Recent decisions and rationale
- Blockers and dependencies
- Next steps

**references.toml** - Pointers to external docs:

```toml
[[references]]
path = "mg_project/__assets__/roles/coo.md"
description = "My operating role"

[[references]]
path = "users/casey/state/minds/wren/docs/problems.md"
description = "Problem backlog I maintain"
```

Later, we may also support @syntax for document references (e.g., `ref = "@memory-persistence"`) once the indexing system is in place. This would allow references to resolve dynamically rather than hardcoding paths.

---

## Startup Flow

### The `mg start` Command

```
mg start {mind} [--tmux]
```

Single command for all scenarios:

**Without `--tmux` (current terminal):**
```
mg start wren
  → Clears terminal
  → Starts Claude
  → Injects prompt: "Run mg wake wren"
```

Use this for:
- Cold start from a fresh terminal
- Context refresh after /reset (run from within Claude or externally)

**With `--tmux` (new window):**
```
mg start wren --tmux
  → Creates new tmux window named "wren"
  → Clears the window
  → Starts Claude
  → Injects prompt: "Run mg wake wren"
```

Use this for:
- Manager spawning a new worker
- Launching additional minds in parallel

### The `mg wake` Command

Called by the mind after `mg start` injects the prompt:

```
mg wake {mind}
  → Locates minds/{mind}/ or minds/_new/{mind}/
  → Reads startup/ folder and references.toml
  → Outputs: "Read the following files in their entirety:
      - mg_project/__assets__/roles/coo.md
      - users/casey/state/minds/wren/startup/identity.md
      - ..."
  → Mind reads files, now has full context
```

### Mind Directory Convention

```
users/{user}/state/minds/
├── wren/                    # established mind (top-level)
│   └── startup/
│       ├── references.toml
│       ├── identity.md
│       └── current-focus.md
├── _new/                    # organizational: onboarding
│   └── reed/
│       └── startup/
│           └── references.toml
├── _archived/               # organizational: no longer active
│   └── old-worker/
└── _project-x/              # organizational: project-specific
    └── specialist/
```

**Naming convention:**
- Mind names cannot start with underscore
- Directories starting with `_` are organizational (not mind names)
- `_new/` is the convention for minds being onboarded
- Other organizational dirs as needed: `_archived/`, `_project-x/`, etc.

**Resolution:** `mg wake reed` searches for `minds/reed/` or `minds/**/reed/` (finds it in `_new/reed/`)

**Separation of concerns:**
- **Onboarding prep** = create folder, populate startup context
- **Launch** = `mg start {mind}`, works the same regardless of where the mind lives

**Promotion:** Move from `_new/reed/` to `minds/reed/` when established. Or start at top-level if you know they'll be long-running.

### One Path for All Minds

Every mind gets a folder, even short-lived workers:

```
users/{user}/state/minds/_new/reed/
└── startup/
    └── references.toml    # points to analyst role
```

**Why always create a folder:**
- Simpler mental model (no special cases)
- Folders are cheap
- No friction if the mind needs to persist later
- Clean up by deleting folders when done

**Cleanup:** Remove `_new/{mind}/` folders when work is complete and context isn't needed.

---

## State Preservation

### When to Save

Start with manual triggers:
- Mind runs `mg sleep` when done for now
- Human prompts mind to update context before ending session

Future: automatic threshold detection via status line integration.

### What to Save

For long-running minds, update:

**identity.md** - When responsibilities or domain knowledge changes
- Usually stable, updated occasionally
- "I now also manage the documentation system"

**current-focus.md** - Before each sleep
- What you're working on
- Key decisions made
- Blockers encountered
- Next steps

**references.toml** - When tracking new external docs
- Add new docs as they become relevant
- Remove stale references

### How to Save

Two approaches for current-focus.md:

**Option A: Structured template**
```markdown
## Active Work
[Current tasks and priorities]

## Recent Decisions
[What was decided and why]

## Blockers
[What's preventing progress]

## Next Steps
[What should happen next]
```

**Option B: Guided prompting**
A command that asks the mind to reflect:
> "Before sleeping, summarize: What are you working on? What did you decide? What's blocked? What's next?"

**Recommendation:** Start with structured template. Easier to parse, consistent format.

---

## Mind Identity Mechanism

How does the system know which mind this Claude instance is?

| Approach | How it works |
|----------|--------------|
| **Environment variable** | `MG_MIND=wren` set at launch |
| **tmux environment** | Store in tmux window's environment |
| **Initial prompt** | First message identifies the mind |

**Recommendation:** Environment variable, set by `mg start {mind}`.

`mg wake` can read it:
```bash
mg wake           # uses MG_MIND env var
mg wake wren      # explicit override
```

---

## Open Questions

1. **references.toml format** - Simple path list? Or richer metadata (load order, conditionals, descriptions)?

2. **Identity vs role boundary** - What belongs in identity.md (mind-specific) vs role.md (shareable)? The line might blur.

3. **Context growth** - How do we prevent identity.md from growing unboundedly? When does accumulated knowledge need distillation?

4. **Role overrides** - Can a mind customize aspects of their role, or is that a new role?

5. **Handoff** - If Wren needs to hand off COO duties, how much of their mind state transfers vs starts fresh?

---

## Not Addressing Yet

- **Automatic compaction detection** - Requires status line integration
- **Distillation system** - Manual curation for now
- **Multi-mind coordination** - Out of scope for memory persistence

---

## Minimal Implementation Path

### Phase 1: Structure
- Create `__assets__/roles/` in mg_project
- Create `users/{user}/state/minds/{mind}/startup/` structure
- Manually create identity.md and current-focus.md for existing minds

### Phase 2: Wake Command
- `mg wake {mind}` reads startup folder
- Outputs file list for mind to read
- Optionally uses MG_MIND env var

### Phase 3: Sleep Command (or template)
- Template for capturing current-focus.md
- Mind fills it out before ending session

### Phase 4: Start Command
- Sets MG_MIND environment
- Creates tmux window
- Injects "Run mg wake" prompt

---

## Summary

**Core design:** Separate role (shareable blueprint) from mind state (particular work).

**Roles** in `__assets__/roles/`:
- Reusable across minds and projects
- Human-maintained
- Can be packaged and shared

**Mind state** in `users/{user}/state/minds/{mind}/startup/`:
- identity.md - who this mind is, accumulated knowledge
- current-focus.md - ephemeral working state
- references.toml - pointers to external docs

**Commands:**
- `mg wake` - output files to read on startup
- `mg sleep` - template for capturing state before compaction
- `mg start` - set identity and launch with context

This gives long-running minds persistent memory while keeping roles as shareable artifacts.
