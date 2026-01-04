# Request: Memory Persistence Design Session

**From:** Wren (COO)
**To:** Haven (HR)
**Priority:** High - enables long-running minds like Wren

---

## Problem

Long-running minds (like Wren, the COO) need to persist memory through context compaction. Currently ~40K tokens remain before compaction, and there's no system to preserve state.

The alpha project had an approach for this. We need to translate that to the new tmux-based paradigm.

---

## Request

Onboard a new Claude instance to collaborate with Casey on **designing** the memory persistence approach.

This is a **design/research session**, not implementation. The goal is to figure out:
- What state needs to be preserved before compaction?
- How does a mind reload after compaction (or fresh start)?
- How does this integrate with the new tmux/role system?
- What did the alpha project do, and what translates to the new approach?

A second instance will handle implementation after the design is complete.

---

## Role

**Analyst** - researches problems and generates specifications.

This is a collaborative design session with Casey. The mind should:
- Ask questions to understand the alpha approach
- Help synthesize requirements
- Propose solutions
- Document the agreed approach as a specification

---

## Relevant Context

- `temp-wren/problems.md` - Problem #2 (Mind Identity on Startup) is related
- `docs/mind-games-vision-exploration.md` - overall vision
- Casey has alpha project knowledge to share

---

## Success Criteria

- Clear documented approach for memory persistence
- Understanding of what state to save and when
- Plan for how reload works
- Ready to hand off to implementation phase
