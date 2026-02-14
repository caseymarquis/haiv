# Task: Design and implement a command hook system for mg

Commands need extensibility points. Example: after worktree creation, auto-run `uv sync`. After merge, trigger cleanup. The system should let each layer (mg_core, mg_project, mg_user) register hooks that respond to events emitted by commands.

**Location:** `worktrees/echo/`

---

## Context

The immediate pain point: every time a worktree is created, the packages inside need `uv sync` run. Today this is manual and easy to forget. Hooks would let mg_project register a post-worktree-creation hook that handles it automatically.

### Prior sketch (from our problems list — starting point for discussion, not finalized)

**Desired pattern:** Observer/event system where commands emit events and hooks subscribe.

Type-safe hook points with request/response generics:
```python
# mg/src/mg/hooks.py
@dataclass
class HookPoint(Generic[TRequest, TResponse]):
    guid: str

    def emit(self, request: TRequest) -> list[TResponse]:
        """Call all registered hooks, return array of results."""
        ...
```

Commands define typed hook points:
```python
# mg-core/src/mg_core/commands/minds/new.py
from mg.hooks import HookPoint

@dataclass
class WorktreeCreatedRequest:
    worktree_path: Path
    branch_name: str

@dataclass
class WorktreeCreatedResponse:
    success: bool
    message: str | None = None

AFTER_WORKTREE_CREATED = HookPoint[WorktreeCreatedRequest, WorktreeCreatedResponse](
    guid="mg-core:minds:new:after-worktree-created"
)
```

Hooks subscribe with type safety:
```python
# mg_project/src/mg_project/hooks/uv_sync_worktree.py
from mg_core.commands.minds.new import AFTER_WORKTREE_CREATED, WorktreeCreatedRequest, WorktreeCreatedResponse
from mg.hooks import hook

@hook(AFTER_WORKTREE_CREATED)
def sync_packages(req: WorktreeCreatedRequest) -> WorktreeCreatedResponse:
    # Run uv sync for each package in worktree
    return WorktreeCreatedResponse(success=True)
```

Caller decides how to handle multiple results:
```python
# In minds/new.py execute()
results = AFTER_WORKTREE_CREATED.emit(WorktreeCreatedRequest(path, branch))
# results is list[WorktreeCreatedResponse] - caller decides what to do
```

**Key elements:**
- Generic `HookPoint[TRequest, TResponse]` for type safety
- Returns `list[TResponse]` — caller handles multiple hooks
- Opens up RPC-style patterns beyond pure observation
- GUIDs for unique identification
- Hooks in `hooks/` directories (project or user level)
- Resolution order: mg_core → mg_project → mg_user

---

## Key Files

| File | Role |
|------|------|
| `users/casey/state/minds/wren/work/docs/problems.md` | Problem #17 — original hook system sketch |
| `mg-core/src/mg_core/commands/minds/stage.py` | Worktree creation — first hook consumer |
| `mg-core/src/mg_core/commands/pop.py` | Session close-out — another hook consumer |
| `mg/src/mg/` | Core mg package — where hook infrastructure likely lives |

---

## Requirements

- Existing tests must still pass
- Follow existing code patterns and conventions
- Resolution order should follow mg's layering: mg_core → mg_project → mg_user

---

## Verification

```bash
cd mg && uv run pytest -v
cd mg-core && uv run pytest -v
```
