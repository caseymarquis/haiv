# Delegation Playbook

A reusable process for spawning and managing worker Claudes.

---

## Phase 1: Define the Task

1. What's the goal? (specific outcome)
2. What are the success criteria?
3. Does it need a worktree? Which one?
4. What context docs are relevant?
5. What role fits? (generalist, researcher, etc.)

---

## Phase 2: Create Welcome Document

Create `temp-welcome/<task-name>.md` with:

```markdown
# Task Assignment

Load the following documents into context:
- ./temp-roles/<role>.md (your role - how to work)
- <additional context docs...>

---

## Task

**<Task name>**

<Description>

**Location:** `<working directory if applicable>`

## Success Criteria

- <criterion 1>
- <criterion 2>
- ...

## Patterns to Follow

- <relevant patterns or reference files>

## Verification

<how to verify success - commands to run, etc.>

---

## Process

1. Read the context documents first
2. Propose your approach before coding
3. Ask clarifying questions if needed
4. Implement incrementally, testing as you go
```

---

## Phase 3: Launch Worker

```bash
# Create window (use mg-state root as cwd)
tmux new-window -n <task-name> -c /home/casey/code/mind-games

# Start Claude
tmux send-keys -t <task-name> 'claude' Enter

# Wait for startup (~3 seconds), then send instruction
sleep 3
tmux send-keys -t <task-name> 'Read ./temp-welcome/<task-name>.md and follow the instructions.' Enter
```

---

## Phase 4: Monitor

Check on worker periodically:

```bash
# See recent output
tmux capture-pane -t <task-name> -p | tail -50

# See full scrollback
tmux capture-pane -t <task-name> -p -S -1000
```

Watch for:
- Worker proposing design (approve or redirect)
- Questions needing input
- Completion signals
- Signs of being stuck

---

## Phase 5: Intervene When Needed

```bash
# Send a message to the worker
tmux send-keys -t <task-name> 'Your message here' Enter
```

Common interventions:
- Approve proposed design
- Answer clarifying questions
- Redirect if going off track
- Provide missing context

---

## Phase 6: Complete

When success criteria are met:
- Verify the work (run tests, try it)
- Have worker commit if appropriate
- Clean up or close window
- Update any tracking docs

```bash
# Close window when done
tmux kill-window -t <task-name>
```

---

## Tips

- Stay high-level - don't get pulled into implementation details
- Check multiple workers in rotation if parallel
- Trust the worker's process, intervene only when needed
- Note friction points to improve tooling later
