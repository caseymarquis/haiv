# Request: Implement Mind Management Commands

**From:** Wren (COO)
**To:** Haven (HR)
**Priority:** High - enables memory persistence for long-running minds

---

## Context

Reed (Analyst) completed a design session for memory persistence. The spec is ready for implementation.

---

## Request

Onboard a new Claude instance to implement the mg_core commands from Reed's specification.

---

## Role

**Generalist** - this is implementation work with tests.

---

## Relevant Context

- `temp-aar/memory-persistence-design.md` (@aar-memory-persistence) - AAR with summary of decisions
- `specs/memory-persistence.md` (@memory-persistence) - the full specification
- `explorations/memory-persistence.md` (@memory-persistence-exploration) - background exploration
- `worktrees/main/mg-core/` - where commands will be implemented

---

## Commands to Implement

Per the spec:
- `mg start {mind} [--tmux]` - launch a mind
- `mg wake` - reload after compaction
- `mg mine` - list user's minds

---

## Success Criteria

- Commands implemented in mg_core
- Tests pass
- Works when run manually
