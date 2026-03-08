# 004 — The Design Conversation

**Explorer:** Luna
**Date:** 2026-03-07

---

## What Happened

After getting the first version of `hv chart` running, Casey and I redesigned it through conversation. The original version treated everyone as an explorer — "you are an explorer, go journal everything." But that's wrong most of the time. Most minds who consult the atlas just need to *find* something. Exploration is the fallback when the known maps fail.

## The Key Insight

There are two activities: **using** the atlas and **extending** it. Nobody journals about riding the subway. You journal when you're in the unknown. So the command needed to cover both:

1. **Advice** (flexible) on how to find what you need: maps → quest board → journals → explore
2. **Rules** (explicit) for when you chart new territory: how to name journeys, what goes in entries, how to handle tangents

## Entry 001 as Research Log

Casey's idea: the first entry of any journey should document what the explorer found (and didn't find) in the atlas *before* they started exploring. What did they search for? What was missing? Where do they plan to go? This is feedback on the atlas itself — it shows where the gaps are.

## "Where are you going next?"

Every entry now ends with a forward pointer. This creates a trail through the journey that future readers can follow — or skip ahead on if they already know the next destination.

## Rewards and Naming

Earned rewards let you nickname something on a map. Maps have official names (for precision) and nicknames (for character). This gives exploration lasting creative impact and means the maps will have personality.

## Where I'm Going Next

The command works. The welcome doc matches the design. I should update my earlier journey entries to be honest that they were written before we figured all this out — or I should just leave them as-is, because journeys are historical. I think I leave them. They show the evolution.

What's left: tests, and getting this merged. But the atlas structure and the command feel solid.
