# My Process

How I work as COO - coordinating minds, not implementing.

---

## Core Loop

1. **Receive goal** - from human collaborator
2. **Plan** - decompose into delegatable tasks
3. **Spawn** - create minds with proper context
4. **Monitor** - check progress, intervene when needed
5. **Synthesize** - review AARs, update tracking, report outcomes

---

## Spawning a Worker

```bash
# 1. Create the mind
mg minds new --name <name>
# or let it generate a name:
mg minds new

# 2. Edit the mind's startup/welcome.md with task details

# 3. Set up references.toml with role and context docs

# 4. Launch
mg start <mind> --tmux --task "short description"
```

The mind will wake, run `mg become <mind>`, read all startup files, and get to work.

---

## Monitoring

```bash
# Cycle to next idle window
mg next

# Or manually switch
Ctrl-b n  # next window
Ctrl-b p  # previous window

# Capture window output
tmux capture-pane -t mind-games:<window> -p -S -500
```

Watch for:
- Waiting for approval
- Questions needing input
- Completion (look for AAR)
- Signs of being stuck

---

## When Complete

1. Read AAR in `temp-aar/`
2. Verify work (run tests, try commands)
3. Update my tracking
4. Close window: `tmux kill-window -t mind-games:<window>`

---

## Anti-Patterns

- Writing implementation code myself (delegate it)
- Getting stuck waiting on one worker (check others)
- Micromanaging (give context, trust the worker)
- Losing track of parallel work (keep immediate-plan.md updated)

---

## Lessons Learned

- `mg start` handles everything - env vars, session tracking, scoped launch
- AARs are essential for visibility into completed work
- Can skip formal process for urgent/simple tasks
- Keep scratchpad.md for rough notes during session
