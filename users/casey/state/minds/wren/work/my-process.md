# My Process

Personal notes and lessons learned. For mechanics, see COO and PM roles in references.toml.

---

## Planning with the Atlas

Before assigning work, check the Atlas maps. They provide a structural model of the system without reading code. When planning:

1. Check maps — do I understand the territory well enough to write a good task description?
2. **Yes** → stage a worker with an informed task
3. **No** → stage an explorer first (`hv chart explore`), get maps back, then plan implementation

This cascades: workers also check maps on wake and may explore further for implementation-level detail. Exploration is not overhead — it's the mechanism that keeps the planning layer accurate.

## Lessons Learned

- `hv start` handles everything - env vars, session tracking, scoped launch
- AARs are essential for visibility into completed work
- Can skip formal process for urgent/simple tasks
- Keep scratchpad.md for rough notes during session
- Worktrees are always created now — no flag needed
- Check live state via `hv sessions`, don't maintain worker tables in notes — they go stale between interactions
- Time is paused between interactions. Minds have infinite patience. Design for clear handoffs, not speed.
- Task descriptions: describe the landscape and destination, not the route. Key files and existing structures are helpful; implementation specifics are not.
- Welcome template enforces Atlas exploration as a hard gate — minds must check maps, propose exploration if insufficient, and use `hv chart explore` for any codebase exploration. No raw file reads without the charting process.
