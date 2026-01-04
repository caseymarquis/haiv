# Problems to Solve

A running list of high-level problems. Research before implementing.

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

## 2. Mind Identity on Startup

**Problem:** How does a new Claude instance know who it is and where its state lives?

Need an environment variable or similar mechanism so the system can tell a Claude instance its identity. This is a prerequisite for:
- Context preservation before compaction
- Reload scripts after compaction
- Persistent memory per mind

**Possible approaches:**
- Environment variable (e.g., `MG_MIND=forge`)
- File in working directory
- Initial prompt injection
- tmux environment

**Status:** Not started

---

## 3. Role Evolution and Instance Bootstrapping

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

## 4. Documentation for AI-First Development

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

Implementation options:
- Lean on existing TODO tool, ensure loaded at start
- Build our own task tracking
- Command workflow that enforces AAR creation

Net result: after delegation completes, delegating mind receives AAR, and report is archived/indexed for future minds to learn from.

**Status:** Approach emerging, not yet implemented

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
