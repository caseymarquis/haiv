# Task Assignment

Load the following documents into context:
- ./temp-roles/analyst.md (your role)
- ./temp-wren/problems.md (Problem #2: Mind Identity on Startup)
- ./docs/mind-games-vision-exploration.md (project vision)

---

## Task

**Design memory persistence for long-running minds**

This is a collaborative design session with Casey. Long-running minds (like Wren, the COO) need to persist memory through context compaction. There's currently no system for this.

You'll be exploring:
- What state needs to be preserved before compaction?
- How does a mind reload after compaction (or fresh start)?
- How does this integrate with the tmux/role system?
- What did the alpha project do, and what translates here?

Casey has knowledge from the alpha project to share. Ask questions to understand that approach.

---

## Deliverable

A specification document for memory persistence. Per your role:
- Start with brief context
- Define behavior through examples
- Show, don't tell
- Don't prescribe implementation

---

## Success Criteria

- Clear documented approach for memory persistence
- Understanding of what state to save and when
- Plan for how reload works
- Spec ready for implementation handoff

---

## Process

1. Read the context docs
2. Ask Casey about the alpha project approach
3. Explore the problem space together
4. Synthesize into a specification
