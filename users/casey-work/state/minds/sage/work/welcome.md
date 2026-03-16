# Task Assignment

**Design and build a fact extraction and review pipeline for the atlas**

Explorer minds produce journey entries — unstructured narratives about codebase exploration. These contain valuable facts mixed with speculation, narrative, and process notes. We need a tool that extracts structured claims from these documents and queues them for expert review before they get integrated into atlas maps.

**Location:** `worktrees/sage/`

---

## The Problem

Right now, turning journey narratives into structured atlas knowledge is manual and error-prone. The cognitive load of extraction, classification, and editing in one pass leads to missed facts and bad structural decisions. We need to break this into discrete steps: extract, review, integrate.

## Reference Request

Read `requests/fact-extraction-tool.md` — this is a request from another project (its-monorepo-hv) that uses haiv. It describes their pain point and proposes a specific solution.

**Important:** The request describes a real need, but the proposed design is just one person's first pass. Treat it as context, not a specification. The specific commands, flags, storage format, and workflow may or may not be right for haiv-core. Your job is to understand the underlying problem and design the right solution for this ecosystem — which may look quite different from what's proposed.

Discuss your design approach with your human collaborator before committing to an implementation path.

---

## Requirements

- A way for minds to extract individual factual claims from source documents
- A review step where an expert can approve, correct, or reject claims
- A way to query approved facts by destination for integration
- Should follow haiv patterns (commands, helpers, templates)
- Should be general enough for haiv-core, not specific to one project's workflow

---

## Success Criteria

- The extract → review → integrate pipeline works end-to-end
- Fits naturally into the existing haiv command structure
- Tests pass

---

## Verification

```bash
cd worktrees/sage/haiv-core && uv run pytest
```

---

## Process

1. Read the reference request to understand the need
2. Explore existing haiv patterns (especially `hv chart explore` for the template-driven approach)
3. Propose a design to your human collaborator
4. Implement iteratively
5. Delegate sub-tasks if scope warrants it

---

## Before You Begin

1. Read the full assignment above.
2. Run `hv chart` and check the maps for anything relevant to your task.
3. **Decision point:** Does the Atlas have what you need to understand the codebase for this task?
   - **Yes** → Continue to step 4.
   - **No** → Propose an exploration to your human collaborator. What territory do you need to chart? This becomes a journey before you write code.
4. Discuss your approach with your human collaborator.

Use `TaskCreate` to track these steps — there may be significant work between them. The task description is a starting point — not a spec. Work collaboratively with your human. Do not use planning tools unless they explicitly request it.

> **IMPORTANT:** When you need to understand the codebase, start with `hv chart` to check what's already mapped. If the Atlas doesn't have enough information, use `hv chart explore` — it will guide you through the exploration process. Do NOT read through code files without it. Exploration that follows the charting process builds the Atlas for future minds. Exploration that doesn't is wasted.
