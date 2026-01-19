# Problems to Solve

A running list of high-level problems. Research before implementing.

---

## Priorities

1. **#2 - Session Recovery** - In progress, foundation in place
2. **#4 - Role Evolution** - Not started
3. **#5 - Documentation/Indexing** - Design done, implementation pending

---

## 1. Detecting Idle Workers

**Problem:** How do we know which Claude instances are waiting for a prompt?

A Claude is either actively processing or paused waiting for human input. The manager needs to know who's paused so they know where attention is needed.

**Possible approaches:**
- `tmux capture-pane` + detect prompt pattern
- Claude Code hooks (idle/waiting hook?)
- Process monitoring (CPU drops when waiting?)
- Statusline data
- File-based signaling

**Status:** Solved (for now)

**Solution:** `mg next` command (mg_project level) captures panes, detects active/idle status, and switches to the next idle mind in order. Experiment before promoting to mg_core.

---

## 2. Session Recovery After Catastrophic Failure

**Problem:** If we kill all terminals and tmux, how do we recover?

Power loss, crashes, or intentional restarts destroy all running Claude sessions. Currently there's no way to restore work in progress - we lose context, conversation history, and have to manually reconstruct what was happening.

**Prerequisites:** ✅ Complete
- Mind management commands (start, become, mine) - working
- Named Claude sessions that match tmux windows - working via `--task`

**Foundation in place:**
- `mg start {mind} --tmux --task "desc"` creates tracked session in `sessions.ig.toml`
- `mg start {mind} --tmux --resume [id]` resumes previous session
- Sessions stored per-mind, most-recent-first, max 20 kept
- Partial ID matching for convenience

**Remaining work:**
- `mg recover` or `mg wake --all` to recover all workers from last known state
- Integration with Claude's `--resume` flag for conversation continuity
- Automatic state capture before compaction (needs status line integration)

**Status:** In progress - foundation complete, recovery command needed

See AAR: `temp-aar/session-management.md`

---

## 3. Mind Identity on Startup (prerequisite for #2)

**Problem:** How does a new Claude instance know who it is and where its state lives?

Need an environment variable or similar mechanism so the system can tell a Claude instance its identity. This is a prerequisite for:
- Context preservation before compaction
- Reload scripts after compaction
- Persistent memory per mind

**Status:** Solved

**Solution:**
- `MG_MIND` environment variable identifies the mind
- `mg become {mind}` outputs files to load for identity context
- `mg start {mind}` launches Claude with `MG_MIND` set
- `mg mine` displays current mind info
- Mind state lives at `users/{user}/state/minds/{mind}/`

See AAR: `temp-aar/session-management.md`

---

## 4. Role Evolution and Instance Bootstrapping

**Problem:** How do we efficiently bring a new Claude instance up to speed for a task?

Each new instance is like an employee on their first day. They need enough context to work effectively but have limited tokens before compaction. Current approach (roles + welcome docs) works but is manual and inconsistent.

**Sub-problems:**
- What's the minimum viable context for different task types?
- How do roles evolve based on what works?
- How do we capture learnings from successful instances?

**Possible approaches:**
- Templated role + task composition
- Learning from successful sessions (what context led to good outcomes?)
- Graduated context loading (start minimal, add as needed)

**Status:** Not started

---

## 5. Documentation for AI-First Development

**Problem:** Software is being built quickly but isn't well documented. New instances can't understand what existing code does.

Traditional docs fall out of date. But with AI:
- AI can read code directly
- AI can generate docs as it works
- Docs could be optimized for AI consumption
- Don't restate what code does - AI can read it

**Sub-problems:**
- What documentation is actually useful for a new Claude instance?
- How do we keep docs in sync with rapidly changing code?

**Emerging approach: Two-level system**

1. **Task playbooks** - "Here are common tasks, here are the files you need, here's the workflow"
2. **File frontmatter** - First 10 lines summarize purpose, read more if needed

**Frontmatter template:**
```python
"""
filename.py - One sentence purpose.

Longer description of what's in this file and when you'd want to read it.
High-level, not signatures (those go stale).

Key pieces: function_name, ClassName, other_function
"""
```

Durable over precise. Only update when file's *purpose* changes, not when signatures change. Add incrementally as files are touched.

**Future: Layered intelligent RAG**

Frontmatter enables a programmatic index. Flow:
1. Task comes in
2. "Librarian" mind reads index, suggests relevant files for this task
3. Task mind loads only what's needed
4. Task mind works with focused context (not everything)

This is RAG with fine control:
- Human/AI-curated content (frontmatter)
- Structured index (not embeddings)
- Intelligent routing (mind decides relevance, not vector similarity)
- Solves the "120K tokens before compaction" constraint

Applies to all documents (code, specs, docs, plans) - same process, standardized formats.

**Open questions:**
- How to fragment the index? One big index or topic-based?
- Does frontmatter need multiple sections? (purpose, dependencies, related docs?)
- These are probably related questions

**After-Action Reports (AARs)**

When delegating work, the delegating mind needs to know what happened. Current problem: Wren had no visibility into worker outcomes without manually checking.

Delegation should be request/response:
- Request: welcome doc (task assignment)
- Response: AAR (what was done, decisions made, blockers hit)
- Both get archived and indexed

**Status:** Working manually

AARs are being produced in `temp-aar/`. Workers create them on completion. Still manual - no enforced workflow or automatic archiving yet.

**File Indexing**

Design complete for hybrid approach:
- Files with ```index blocks are source of truth
- SQLite cache (gitignored) for queries
- Commands: `mg index rebuild`, `find`, `check`, `refs`, `search`, `query`

See AARs: `temp-aar/file-indexing-analysis.md`, `temp-aar/memory-persistence-design.md`

**Status:** Design done, implementation pending

---

## 6. Simplify Initial tmux Startup

**Problem:** Starting a tmux session for an mg-managed repo is manual and error-prone.

Currently requires remembering: `tmux new-session -s <dirname> -c <path>`. Should be a single command that infers the session name from the directory.

**Status:** Solved

**Solution:**
- `mg tmux` command creates session (named after repo directory) or attaches if exists
- `Tmux` class in `mg/src/mg/tmux.py` handles all tmux operations
- Auto-creates sessions on first use (lazy initialization)
- Guards prevent running from inside Claude Code or existing tmux

See AAR: `temp-aar/tmux-class.md`

---

## 7. Session Context Extraction (Fork and Summarize)

**Problem:** Rich context is trapped in active sessions, but using those sessions for meta-tasks wastes their focus and tokens.

When managing multiple parallel workers, reintegration after being away is disorienting. You need to understand what's happening across sessions, but:
- Asking each session to summarize distracts from their real work
- The context needed for orientation lives inside the sessions
- Similar problem occurs when hitting blockers - you need to describe the problem without derailing the session

**Use cases:**
- **Reintegration summaries** - "What's the current state of all workers?"
- **Blocker descriptions** - Fork to document the problem, delegate fix, test result, resume original session undisturbed
- **Mid-session status reports** - Track progress without interrupting work
- **Automated memory consolidation** - Periodic forks to cheaper models writing state updates (transparent persistent memory)

**Possible approach: Session forking**
1. Identify session ID (from `sessions.ig.toml` or tmux env)
2. Start new Claude session that loads the same conversation (`--resume`)
3. Give fork a specific meta-task (summarize, describe blocker, report status)
4. Original session remains untouched and focused

This is effectively building a hippocampus - consolidating short-term memory (session context) into long-term memory (written state) without interrupting active processing.

**Considerations:**
- Could automate with cheaper models for cost efficiency
- Fork results could feed into queryable "what's happening" system
- May need conventions for fork task types (summary, blocker, status)

**Status:** Not started

---

## 8. System Discoverability

**Problem:** After time away, it's hard to remember what commands exist, their flags, and usage patterns.

The system grows quickly with multiple minds contributing. Without a quick reference, you waste context trying to remember or searching through code.

**Requirements:**
- Printable summary of available commands with descriptions
- Common usage patterns and examples
- Grouped by purpose (mind management, tmux, development, etc.)

**Key principle: Don't derail current work**

Similar to #7, we don't want to waste context on the current session researching commands. Options:
- `mg commands` - quick printable summary
- `mg commands --help-session` - opens new tmux window with helper mind that has full command knowledge
- Helper can research specifics, answer questions, suggest relevant commands

The helper mind approach means you stay focused on your task while getting detailed help in parallel.

**Future enhancement:**
- Agent with cheaper model suggests relevant commands based on what you're trying to do (similar to `suggest_role`)
- Probably overkill for now

**Possible implementation:**
- Introspect command files across all mg packages
- Extract docstrings/descriptions from `define()` calls
- Format as quick reference

**Status:** Not started

---

## 9. Task Completion Visibility

**Problem:** How do we bubble up task completions for analysis?

When workers finish tasks, we need to know what happened. Currently using AARs (After-Action Reports) in `temp-aar/`, but:
- Manual creation with no enforced structure
- No tooling (`mg aar new`, helpers)
- Unclear if AARs are even the right abstraction
- Layering questions: do sub-tasks get their own AARs? How do they roll up?

**The deeper question:** What's the right form for surfacing completed work? Options:
- Structured AARs with tooling
- Simpler completion signals with metadata
- Session fork summaries (see #7)
- Something else entirely

**Possible first step:**
- Implement at project level first (mg_project) to experiment
- `mg aar new` with helper to scaffold structure
- See what patterns emerge before promoting to mg_core

**Why it's complex:**
- Gets into organizational memory and knowledge management
- Interacts with #5 (Documentation/Indexing) and #7 (Session Forking)
- Wrong abstraction early could create friction

**Status:** Not started - needs research

---

## 10. Streamline Mind + Worktree Creation

**Problem:** When creating a mind for feature work, you often know you'll need a worktree. Currently this requires separate steps.

**Status:** Solved

**Solution:**
```bash
mg minds stage --worktree              # Creates mind + worktree (branch = mind name)
mg minds stage --worktree --branch X   # Creates mind + worktree named X
mg minds stage --no-worktree           # Creates mind only
mg minds stage                         # Error with guidance
```

Also delivered settings infrastructure:
- `mg.toml` at project root, `users/{user}/mg.toml` for overrides
- `ctx.settings.default_branch` (worktree branches from this)

**Open items for future:**
- Project hooks for post-worktree setup (auto `uv sync`)
- `mg settings show/set` CLI
- Settings validation

See AAR: `temp-aar/project-worktree-integrated-minds.md`

---

## 11. Return to Parent Context After Blocking Task

**Problem:** When a short-running blocking task completes, we want to return to the parent context seamlessly.

Workflow:
1. Working in context A
2. Hit blocker, assign mind B to resolve it
3. Mind B completes
4. Want to return to context A and continue

Currently no tooling for this. You manually switch windows and lose the "where was I?" moment.

**Desired:**
```bash
mg pop  # return to parent context
```

**Advanced (future):**
```bash
mg pop --time-travel  # restore parent to state before blocker
```

The `--time-travel` flag would restore the parent conversation to the point when you first encountered the issue - as if you were never blocked at all. The blocker was handled transparently.

**Implementation notes:**
- Initial version: simple window/session switch to parent
- Need to track parent relationship when assigning
- Time-travel requires conversation state management (more complex)

**Status:** Not started

---

## 12. Development Iteration in Worktrees

**Problem:** When developing mg commands in a worktree, manual testing and iteration is awkward.

The installed `mg` command runs from the main branch, not the worktree. To test changes, you either:
- Run directly with `uv run` from the worktree (verbose)
- Temporarily work in main (risky, pollutes main)
- Install from worktree (extra step, easy to forget)

Accidentally building `mg help` in main was actually nice - changes were immediately testable. This only works for commands without significant side effects.

**Why it matters:**
- Fast iteration is crucial for development
- Current workflow has friction
- Easy to forget which mg you're running

**Possible approaches:**
- Worktree-aware mg that detects and uses local code
- `mg dev` command that runs from worktree context
- Better conventions/tooling for worktree development

**Status:** Not started - documenting for future consideration

---

## 13. Session-Aware Workflow

**Problem:** Minds don't know their session context, limiting tooling for status updates and AAR creation.

Currently `mg start` creates a session ID and stores it in `sessions.ig.toml`, but the mind has no way to know its own session. This prevents intuitive commands that operate on "my current session."

**What's missing:**

1. **MG_SESSION env var** - `mg start` should set this alongside MG_MIND so minds know their session context

2. **Status field** - Free text field in session data that minds can update. No constraints - we're intelligent readers. Commands like `mg session status "Working on WP4"`

3. **Session-aware AAR creation** - `mg aars new` that:
   - Auto-names from session task slug
   - Adds frontmatter linking to session ID
   - Links to startup/welcome.md (or future task.md)

4. **Task document linkage** - AARs reference their source task. May evolve welcome.md → task.md since it's not just for first wake.

**Desired flow:**
```bash
mg start mind --tmux --task "desc"
  # → creates session, sets MG_MIND + MG_SESSION, launches claude

mg session status "Implementing roles helper"
  # → updates status field for current session

mg aars new
  # → creates temp-aar/{slug}.md with session linkage
```

**Why it matters:**
- Enables `mg sessions` to show real-time status
- Reduces friction for AAR creation (less boilerplate)
- Creates audit trail linking tasks → sessions → AARs
- Foundation for richer workflow tooling

**Status:** Not started

---

## 14. Hierarchical Mind Visibility

**Problem:** No way to see the tree of active minds and their relationships.

Want `mg tree` to display active minds as a hierarchy (like the `tree` command for files), showing parent-child task relationships and status at a glance.

**Prerequisites:**
- Parent task concept - minds need to know who assigned them
- Session status (#13) - to show what each mind is doing

**Blocked on:** Parent task tracking not yet implemented.

**Status:** Not started - needs prerequisites

---

## 15. Manager Context Preservation

**Problem:** The human manager loses context when stepping away, with no automated way to rebuild it.

When managing multiple initiatives with minds at various levels, context exists at multiple layers:

```
User (Casey)
├── Initiative: Worktree integration
│   └── luna (PM) → workers...
├── Initiative: suggest-role
│   └── sage (PM, paused)
└── Ad-hoc tasks
    └── nova, etc.
```

Each level needs its own context:
- **User level** - What initiatives exist? Overall state?
- **Initiative level** - Goal, key decisions, current blockers
- **Task level** - What's this mind doing right now?

**The core challenge:**
- Manual notes get forgotten when deep in work
- Information exists in conversations but isn't captured
- Redirections, decisions, completions should log automatically
- After days away, need synthesis to resume advising

**Automation needed:**
- Capture key events (redirections, decisions, completions)
- Periodic or triggered summarization
- Briefings on demand: `mg briefing --since "3 days ago"`

**UI implications:**
- May need TUI for multi-level visibility
- Creative tmux usage (dedicated status pane?)
- Something beyond simple CLI commands

**Why it's foundational:**
This affects design of sessions, AARs, status tracking, and hierarchy. Without manager context preservation, the human becomes the bottleneck.

**Status:** Not started - needs design

---

## 16. Structural Change Visibility

**Problem:** Filesystem/structural changes get buried in conversation content. Mistakes (wrong locations, unexpected structure) only caught by chance.

Conversations highlight *content* (decisions, reasoning). But *structural changes* (new worktrees, directories, files) need their own visibility - especially when managing multiple minds making changes in parallel.

**Desired view:**
```
mg structure --since "1 hour ago"

main
├── suggest-role (branched from main)
│   └── [diff vs main]
└── settings-infra (branched from main)
    └── [+] mg/src/mg/settings.py
    └── [~] mg/src/mg/cmd.py

users/casey/state/minds/_new/
└── [+] prism/              # NEW
└── [~] luna/immediate-plan.md
```

**Key insight:** Show worktrees against their parent branch. The tree shows lineage, the diff shows changes relative to that lineage. Structure and history together.

**Use cases:**
- Catch misplaced worktrees/files early
- See what each mind has structurally changed
- Understand branch relationships at a glance

**Relates to:** #15 (Manager Context Preservation) - structural visibility is part of the broader context problem.

**Status:** Not started

---

## 17. Command Hook System

**Problem:** Commands need extensibility points. Example: after worktree creation, auto-run `uv sync`.

**Desired pattern:** Observer/event system where commands emit events and hooks subscribe.

**Sketch:**

Type-safe hook points with request/response generics:
```python
# mg/src/mg/hooks.py
@dataclass
class HookPoint(Generic[TRequest, TResponse]):
    guid: str

    def emit(self, request: TRequest) -> list[TResponse]:
        """Call all registered hooks, return array of results."""
        ...
```

Commands define typed hook points:
```python
# mg-core/src/mg_core/commands/minds/new.py
from mg.hooks import HookPoint

@dataclass
class WorktreeCreatedRequest:
    worktree_path: Path
    branch_name: str

@dataclass
class WorktreeCreatedResponse:
    success: bool
    message: str | None = None

AFTER_WORKTREE_CREATED = HookPoint[WorktreeCreatedRequest, WorktreeCreatedResponse](
    guid="mg-core:minds:new:after-worktree-created"
)
```

Hooks subscribe with type safety:
```python
# mg_project/src/mg_project/hooks/uv_sync_worktree.py
from mg_core.commands.minds.new import AFTER_WORKTREE_CREATED, WorktreeCreatedRequest, WorktreeCreatedResponse
from mg.hooks import hook

@hook(AFTER_WORKTREE_CREATED)
def sync_packages(req: WorktreeCreatedRequest) -> WorktreeCreatedResponse:
    # Run uv sync for each package in worktree
    return WorktreeCreatedResponse(success=True)
```

Caller decides how to handle multiple results:
```python
# In minds/new.py execute()
results = AFTER_WORKTREE_CREATED.emit(WorktreeCreatedRequest(path, branch))
# results is list[WorktreeCreatedResponse] - caller decides what to do
```

**Key elements:**
- Generic `HookPoint[TRequest, TResponse]` for type safety
- Returns `list[TResponse]` - caller handles multiple hooks
- Opens up RPC-style patterns beyond pure observation
- GUIDs for unique identification
- Hooks in `hooks/` directories (project or user level)
- Resolution order: mg_core → mg_project → mg_user

**Relates to:** Luna's lesson about needing post-worktree setup hooks.

**Status:** Not started

---

## Template

```markdown
## N. Problem Name

**Problem:** One-sentence description

Context and why it matters.

**Possible approaches:**
- Approach 1
- Approach 2

**Status:** Not started | Researching | Solved
```
