# AAR: Mind Setup Checklist

## Problem

When creating a worker mind, the PM skipped critical setup steps:

1. Didn't assign a role via `references.toml`
2. Didn't run `mg minds suggest_role` to get role recommendations
3. Wrote an ambiguous task description (worker thought "migrate" meant file migration, not code changes)

The worker started without proper context, wasted effort, and needed to be restarted.

## Root Cause

The `mg minds new` → `mg start` workflow has multiple manual steps with no enforcement:

```
mg minds new --worktree
# 1. Edit startup/welcome.md     <-- easy to do poorly
# 2. Edit references.toml        <-- easy to forget
# 3. Run suggest_role            <-- easy to skip
mg start <mind> --tmux --task "..."
```

Nothing prevents `mg start` from running on an improperly configured mind.

## Key Insight

Minds already have a well-developed TODO tool (TodoWrite) built into Claude Code. Instead of creating new infrastructure, we should leverage this existing system.

The pattern: **pre-populate todos before the main task begins**.

## Proposed Solution

### 1. PM Gets Setup Todos

When a PM creates a worker, their own todo list should include setup steps:

```
[ ] Read the role I'm assigning (generalist, coo, etc.)
[ ] Edit welcome.md with clear task description
[ ] Add role to references.toml
[ ] Run mg minds suggest_role (optional)
[ ] Start the mind
```

This could be:
- Documented in the PM role guide
- Output by `mg minds new` as suggested todos
- Enforced by `mg start` checking for common issues

### 2. `mg start` Light Validation

Before starting, `mg start` checks for obvious issues:

```
$ mg start nova --tmux --task "do stuff"
Warning: references.toml has no role assigned.
Warning: welcome.md appears unedited (still contains template markers).

Continue anyway? [y/N]
```

Or with `--force` to skip.

### 3. Worker Gets Onboarding Todos

The worker mind could start with pre-populated todos based on their role:

```
[ ] Read welcome.md and role docs completely
[ ] Ask clarifying questions before starting
[ ] Design approach (skeleton code if applicable)
[ ] Write tests first
[ ] Implement
[ ] Write AAR
```

This could be injected via the `--task` description or a startup prompt.

## Benefits

- Leverages existing TodoWrite infrastructure
- No new file formats or commands needed
- Self-documenting through the todo list
- Natural fit for how minds already work

## Implementation

1. **Update PM role docs** - Add explicit "read the role first" guidance
2. **Update `mg minds new` output** - Suggest todos for the creating mind
3. **Update `mg start`** - Add light validation with warnings
4. **Consider** - Injecting role-specific onboarding todos into worker startup

## Related

- `mg fix` command - staged workflow pattern (heavier weight)
- TodoWrite tool - existing infrastructure to leverage
