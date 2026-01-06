# Handoff: Session Management for Mind Commands

**Task:** Add session tracking to `mg start {mind} --tmux`
**Status:** Ready to implement
**Date:** 2026-01-05

---

## Context Documents to Load

```
Required:
- ./worktrees/main/mg-core/src/mg_core/commands/start/_mind_.py  # Current start command
- ./worktrees/main/mg-core/src/mg_core/helpers/minds.py          # Mind/MindPaths classes
- ./worktrees/main/mg-core/tests/test_start.py                   # Existing tests

Reference:
- ./worktrees/main/mg/src/mg/cmd.py                              # Flag definitions
- ./worktrees/main/mg-core/tests/test_become.py                  # Test patterns
```

---

## Recently Completed Work

### Commands Implemented
- `mg start {mind} [--tmux]` - Launch a mind (terminal or tmux window)
- `mg become {mind}` - Load mind's context (renamed from wake)
- `mg mine` - Display current mind info

### Key Files
| Item | Location |
|------|----------|
| Start command | `mg-core/src/mg_core/commands/start/_mind_.py` |
| Become command | `mg-core/src/mg_core/commands/become/_mind_.py` |
| Mine command | `mg-core/src/mg_core/commands/mine.py` |
| Mind helpers | `mg-core/src/mg_core/helpers/minds.py` |
| Tmux class | `mg/src/mg/tmux.py` (includes TmuxWindow) |

### Test Status
- 148 tests passing in mg-core
- 30 tests passing for Tmux class

---

## New Task: Session Management

### Overview

When a manager mind spawns workers via `mg start {mind} --tmux`, we want to:
1. Track sessions with UUIDs and descriptions
2. Allow resuming previous sessions

### Claude CLI Flags

```bash
claude --session-id <uuid>     # Start with specific session ID
claude --resume <session_id>   # Resume existing session
```

### New Flags for `mg start`

Only applicable with `--tmux` (spawning workers):

```
--task "description"      Start new session with description, generate UUID
--resume [session_id]     Resume session (most recent if ID omitted)
```

### sessions.toml Format

Location: `{mind_root}/sessions.toml`

```toml
[[sessions]]
id = "abc-123-def-456"
task = "Implement user authentication"
started = 2026-01-05T14:30:00Z

[[sessions]]
id = "xyz-789-..."
task = "Fix pagination bug"
started = 2026-01-05T10:15:00Z
```

Sessions should be ordered most-recent-first (prepend new sessions).

---

## Implementation Plan

### 1. Extend MindPaths

In `mg-core/src/mg_core/helpers/minds.py`:

```python
@property
def sessions_file(self) -> Path:
    return self.root / "sessions.toml"
```

### 2. Add Session Helper Functions

New file or extend minds.py:

```python
@dataclass
class Session:
    id: str
    task: str
    started: datetime

def load_sessions(sessions_file: Path) -> list[Session]:
    """Load sessions from TOML file."""

def save_session(sessions_file: Path, session: Session) -> None:
    """Prepend a new session to the file."""

def get_most_recent_session(sessions_file: Path) -> Session | None:
    """Get the most recently started session."""

def find_session(sessions_file: Path, session_id: str) -> Session | None:
    """Find session by ID (can be partial match)."""
```

### 3. Update Start Command Definition

```python
def define() -> cmd.Def:
    return cmd.Def(
        description="Launch a mind",
        flags=[
            cmd.Flag("tmux", type=bool, description="Start in a new tmux window"),
            cmd.Flag("task", type=str, description="Task description for new session"),
            cmd.Flag("resume", type=str, min_args=0, max_args=1,
                     description="Resume session (most recent if no ID)"),
        ],
    )
```

### 4. Update _start_in_tmux()

```python
def _start_in_tmux(ctx: cmd.Ctx, mind: Mind) -> None:
    task = ctx.args.get_one("task") if ctx.args.has("task") else None
    resume_id = ctx.args.get_one("resume") if ctx.args.has("resume") else None

    if task and resume_id:
        raise CommandError("Cannot use --task and --resume together")

    # ... existing tmux setup ...

    if resume_id is not None:
        # Resume existing session
        if resume_id == True:  # --resume with no value
            session = get_most_recent_session(mind.paths.sessions_file)
        else:
            session = find_session(mind.paths.sessions_file, resume_id)

        if not session:
            raise CommandError("No session found to resume")

        prompt = f"Run `mg become {mind.name}`"
        window.send_keys(f'claude --resume {session.id} --prompt "{prompt}"')

    elif task:
        # Start new tracked session
        session = Session(
            id=str(uuid.uuid4()),
            task=task,
            started=datetime.now(timezone.utc),
        )
        save_session(mind.paths.sessions_file, session)

        prompt = f"Run `mg become {mind.name}`"
        window.send_keys(f'claude --session-id {session.id} --prompt "{prompt}"')

    else:
        # Untracked session (existing behavior)
        prompt = f"Run `mg become {mind.name}`"
        window.send_keys(f'claude --prompt "{prompt}"')
```

### 5. Validation Rules

- `--task` and `--resume` require `--tmux`
- `--task` and `--resume` are mutually exclusive
- `--resume` without value uses most recent session
- Partial session ID matching for convenience

---

## Test Cases to Add

```python
class TestStartSessionManagement:
    def test_task_flag_requires_tmux(self): ...
    def test_resume_flag_requires_tmux(self): ...
    def test_task_and_resume_mutually_exclusive(self): ...
    def test_task_creates_session_entry(self): ...
    def test_task_passes_session_id_to_claude(self): ...
    def test_resume_without_id_uses_most_recent(self): ...
    def test_resume_with_id_finds_session(self): ...
    def test_resume_with_partial_id_matches(self): ...
    def test_resume_nonexistent_session_errors(self): ...
```

---

## Verification

```bash
cd worktrees/main && uv run pytest mg-core/ -v
```

Manual test:
```bash
mg start wren
# Then as wren:
mg start robin --tmux --task "Implement feature X"
mg start robin --tmux --resume
```
