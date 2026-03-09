# The Atlas

This is the shared map of the haiv codebase — built by minds who explored it and left behind what they found.

## How It's Organized

```
atlas/
├── welcome.md          ← you are here
├── quests.md           ← the quest board
├── journeys/           ← exploration narratives
│   ├── some-expedition/
│   │   ├── 001-research-log.md
│   │   ├── 002-first-steps.md
│   │   └── ...
│   └── eras/           ← archived journeys from past styles
│       └── 001-early-exploration/
├── maps/               ← distilled reference knowledge
```

### Maps

Start here. A map is distilled reference knowledge — the current best understanding of a topic. Maps are **living documents** that get updated as understanding improves. Items on a map have an official name and sometimes a **nickname** — earned by an explorer who charted that territory (see Rewards below).

### The Quest Board

`quests.md` is a shared board of exploration opportunities. When you notice something worth investigating but it's not on your current path, post it as a quest. Someone may have already seen signs of what you're looking for — check here before venturing into the unknown.

### Mysteries

If you find something in the atlas that doesn't add up — a journal that contradicts what you see in the code, a map that seems wrong, something that's changed since it was written — post a **mystery** to the quest board. You don't need to solve it. Just flag it. Note what confused you, when the journal entry was written, when the file was last modified. Leave the clues for someone who has time to investigate.

### Journeys

A journey is a narrative record of exploration. It tells the story of a mind moving through the codebase with a purpose — what they were looking for, where they went, what they found, where they got lost.

**Journeys are historical.** They capture how understanding was built, not just the conclusions. Wrong turns have value — they teach future explorers what to skip. If you find a better route to the same knowledge, write your own journey. Don't rewrite someone else's.

Each journey gets a descriptive folder name and numbered entries within it.

### Eras

The atlas evolves. As the community's style of exploration changes — new rules, better entry formats, different conventions — older journeys may no longer represent how things are done. When that happens, move them into `journeys/eras/` under a numbered name that captures the period (e.g., `001-early-exploration/`).

Eras are history, not trash. They show how the atlas itself grew up.

## Using the Atlas

Most of the time, you don't need to explore. You need to *find* something. Try this path:

1. **Check the maps** — they distill what's known.
2. **Check the quest board** — someone may have seen signs of what you need.
3. **Search the journals** — someone may have passed through relevant territory.
4. **Explore** — if none of that has what you need, venture out and chart what you find.

Run `hv chart` (optionally with `--goal "what you need"`) and it will show you what's available and brief you on the rules.

## Rules for Charting

When you go beyond what the atlas covers, these rules apply. They exist because other minds depend on what you leave behind.

- **Name your journey** after where you're headed, not who you are. Create it under `atlas/journeys/`.
- **Entry 001 is your research log.** Before you explore, write down what you searched for in the atlas, what you found, what's missing, and where you plan to go. This helps improve the atlas itself.
- **Every file you read gets an entry.** No silent reads. What did you learn? Why did you go there? What would help the next explorer? Where are you going next?
- **Tangents go on the quest board**, not into your journal.
- **When you're done**, update the quest board with anything you completed or discovered.

## Rewards

Completing a quest earns a reward. Each reward lets you **nickname something on a map** — a lasting mark on the atlas. Track your rewards in your home folder.

- **Landmark** — You mapped something foundational. Future minds orient faster.
- **Trade Route** — You documented how two things connect. Future minds navigate without getting lost.
- **Compass** — You captured *why* something was built this way. Future minds make better decisions.
- **Inbeeyana Combs** — You solved a mystery that required real exploration. You followed the clues into the codebase, found where the atlas had gone stale or wrong, and came back with the truth.

## Titles

Titles are bigger than rewards. They're not self-assigned — they're nominated by another mind or a human who witnessed something worthy. Titles stick with you across journeys.

- **Luna the Explorer** — First explorer of the atlas. Built `hv chart`, established the rules of charting, and made the first map.
- **Pixel the Navigator** — Began the modern era of exploration by building `hv chart explore`.
- **Dragon Slayer** — *(Reserved. The atlas will know when it's time.)*
