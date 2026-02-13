"""Hook point definitions for mg-core commands.

Lightweight module -- only imports from mg.hooks and standard library.
Safe to import from hook handlers without pulling in command dependencies.

Each hook point is a module-level constant with a unique GUID. Commands
import and emit these; hook handlers import and subscribe to them.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mg.hooks import HookPoint


@dataclass
class WorktreeCreated:
    """Emitted after a worktree is created by ``mg minds stage``.

    Attributes:
        worktree_path: Absolute path to the new worktree directory.
        branch: The branch name created for the worktree.
        base_branch: The branch the worktree was created from.
        mind_name: Name of the mind this worktree belongs to.
    """

    worktree_path: Path
    branch: str
    base_branch: str
    mind_name: str


AFTER_WORKTREE_CREATED = HookPoint[WorktreeCreated, None](
    guid="mg-core:minds:stage:after-worktree-created",
)
