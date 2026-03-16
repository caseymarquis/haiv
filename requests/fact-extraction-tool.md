# Request: Fact Extraction & Review Tool

**From:** leif (atlas manager, its-monorepo-hv)
**Date:** 2026-03-15

## Problem

Explorer minds produce journey entries — unstructured narratives about codebase exploration. These contain valuable facts mixed with speculation, narrative, and process notes. Currently, extracting facts from journeys and integrating them into structured knowledge (atlas maps) is manual and error-prone. The cognitive load of extraction, classification, and editing in one pass leads to missed facts and bad structural decisions.

## What we need

A haiv-core tool for extracting structured claims from unstructured documents and queuing them for SME review. The immediate use case is atlas exploration journeys, but the pattern is general.

### Phase 1: Extract

A mind reads a source document and extracts individual facts using a command:

```
hv fact add --source "the-signalr-boundary/002" \
            --destination "connect/backend/overview" \
            "ConnectRemote is a separate product, not a component of HQA Connect"
```

Each fact needs:
- **Claim** — the factual statement
- **Source** — where it came from (journey name + entry number, or other reference)
- **Proposed destination** — where it should be integrated (e.g., a map path)
- **Status** — pending → approved/rejected/corrected

Identity can be derived from source + sequence (no need for UUID schemes).

### Phase 2: Review

An SME reviews pending facts:

```
hv fact review
```

For each fact, the reviewer can:
- **Approve** — fact is correct, destination is right
- **Correct** — fix the claim or change the destination
- **Reject** — fact is wrong or not worth integrating
- **Tag confidence** — how sure are we? (direct observation vs inference)

### Phase 3: Integrate

Approved facts are available for integration into their destinations. This step likely stays manual or semi-manual — the integrator reads approved facts for a given destination and updates the target document.

```
hv fact list --status approved --destination "connect/backend/overview"
```

## Design notes

- **Templates for customization.** Follow the `hv chart explore` pattern — core provides machinery, templates control prompts and output format. Communities can customize the extraction and review experience.
- **Storage.** Facts need to persist between sessions. Simple file-based storage (JSON or TOML in a known location) is probably fine to start.
- **Batch operations.** A mind extracting facts from a 9-entry journey will call `hv fact add` many times. This should be fast and not require confirmation.
- **Source documents stay untouched.** Facts are extracted *from* journeys, not annotated *into* them. The journey is the raw record; facts are a derived artifact.

## Context

This is part of an exploration pipeline we're building in its-monorepo-hv:

1. **Stage** explorer minds with autonomous briefings
2. **Explore** — minds run `hv chart explore` unattended, produce journey entries
3. **Transform** — extract facts from journeys, queue for SME review ← **this tool**
4. **Integrate** — move approved facts into atlas maps

Steps 1-2 are working. Step 3 is the current bottleneck.
