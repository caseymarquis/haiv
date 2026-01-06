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
- `mg recover` or `mg wake --all` to respawn all workers from last known state
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
