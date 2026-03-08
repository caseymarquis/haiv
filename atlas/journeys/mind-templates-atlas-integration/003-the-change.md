# 003 — The Change

**Came from:** 002 — identified the welcome template's "Before You Begin" section as the right place.

## What changed

`worktrees/main/haiv-core/src/haiv_core/__assets__/minds/welcome.md.j2`

Replaced the "Before You Begin" prose with a sequential checklist:

1. Read the assignment
2. Run `hv chart` and check the maps
3. Discuss findings and approach with human collaborator
4. No planning tools unless human requests it

The old version was a paragraph that buried the key instructions. The new version is a numbered sequence that puts atlas consultation between reading and discussing — exactly where orientation belongs in the workflow.

## Design decisions

- **No explanation of what atlas is or how it works.** `hv chart` handles that. The template just says to run it.
- **Sequential, not parallel.** Read first (know what you're doing), chart second (know what's already known), discuss third (bring both to the conversation).
- **Kept it short.** Four steps. A mind can read this in seconds.
