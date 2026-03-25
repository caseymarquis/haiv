"""Sessions widget — displays active sessions in a tree with preview.

Full-screen tab content. The tree shows sessions nested by delegation
hierarchy. Highlighting a node updates the preview area below. The launch
action starts the highlighted mind.

Architecture:
    DTOs define what the widget needs. Assembly functions build DTOs from
    raw data. The widget renders DTOs. Assembly is testable without Textual.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.events import Click
from textual.widgets import Static, Tree

from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

from haiv.helpers.open import open_in_editor, open_in_explorer
from haiv.helpers.tui import helpers
from haiv_tui.widgets.debounce_button import DebounceButton
from haiv.helpers.tui.TuiModel import ActiveMindRaw, GitRaw, SessionEntry, SessionsRaw
from haiv.helpers.tui.terminal import TerminalManager
from haiv.helpers.utils.trees import TreeNode, build_tree
from haiv.paths import Paths
from haiv.settings import HaivSettings
from haiv.wrappers.git import BranchStats

if TYPE_CHECKING:
    from haiv._infrastructure.TuiServer import TuiLocalClient
    from haiv_tui.store import TuiStore


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class SessionActionBar(Vertical):
    """Action bar — open worktree in explorer or editor."""

    DEFAULT_CSS = """
    SessionActionBar {
        width: auto;
        height: auto;
    }
    SessionActionBar DebounceButton {
        margin: 0 0 1 0;
    }
    SessionActionBar DebounceButton Button {
        min-width: 12;
    }
    """

    def __init__(self, *, settings: HaivSettings, errors: deque[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self._settings = settings
        self._errors = errors
        self._path: Path | None = None

    def compose(self) -> ComposeResult:
        yield DebounceButton("Explorer", disabled=True, id="btn-explorer")
        yield DebounceButton("Editor", disabled=True, id="btn-editor")

    def set_path(self, path: Path | None) -> None:
        self._path = path
        has_path = bool(path)
        self.query_one("#btn-explorer", DebounceButton).disabled = not has_path
        self.query_one("#btn-editor", DebounceButton).disabled = not has_path

    def on_debounce_button_pressed(self, event: DebounceButton.Pressed) -> None:
        path = self._path
        if not path or not path.is_dir():
            return
        try:
            if event.debounce_button.id == "btn-explorer":
                open_in_explorer(path, self._settings.file_explorer_command)
            elif event.debounce_button.id == "btn-editor":
                open_in_editor(path, self._settings.editor_command)
        except Exception as e:
            self._errors.append(f"{event.debounce_button.id}: {e}")


class SessionPreview(VerticalScroll):
    """Preview area showing details of the highlighted session."""

    DEFAULT_CSS = """
    SessionPreview {
        height: auto;
        max-height: 5;
        padding: 0 1;
        border-top: solid $surface-lighten-2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("", id="session-preview-content")

    def render_preview(self, view: SessionNodeView | None) -> None:
        content = self.query_one("#session-preview-content", Static)
        if view is None:
            content.update("")
            return
        lines = [
            f"{view.mind}: {view.task}",
            f"Status: {view.status or 'none'} | Session: {view.short_id}",
        ]
        if view.description:
            lines += ["", view.description]
        content.update("\n".join(lines))


class SessionsWidget(Vertical):
    """Sessions tab — tree with inline preview."""

    BINDINGS = [
        Binding("j", "cursor_down", "Cursor Down", show=False, id="sessions.cursor_down"),
        Binding("k", "cursor_up", "Cursor Up", show=False, id="sessions.cursor_up"),
        Binding("enter", "launch_session", "Launch", id="sessions.launch", priority=True),
    ]

    def __init__(
        self,
        *,
        store: TuiStore,
        terminal: TerminalManager,
        tui_client: TuiLocalClient,
        sessions_file: Path,
        haiv_root: Path,
        settings: HaivSettings,
        errors: deque[str],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._store = store
        self._terminal = terminal
        self._tui_client = tui_client
        self._sessions_file = sessions_file
        self._haiv_root = haiv_root
        self._paths = Paths(_called_from=None, _pkg_root=None, _haiv_root=haiv_root)
        self._settings = settings
        self._errors = errors
        self._sessions: SessionsRaw | None = None
        self._git: GitRaw | None = None
        self._active_mind: ActiveMindRaw | None = None

    def action_cursor_down(self) -> None:
        self.query_one(Tree).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one(Tree).action_cursor_up()

    def compose(self) -> ComposeResult:
        yield Tree[SessionNodeView]("Sessions", id="sessions-tree")
        yield SessionPreview(id="session-preview")

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        tree.root.expand()
        self._store.sessions_changed.connect(self._on_sessions_changed)
        self._store.git_changed.connect(self._on_git_changed)
        self._store.active_mind_changed.connect(self._on_active_mind_changed)
        if self._store.snapshot is not None:
            self._sessions = self._store.snapshot.sessions
            self._git = self._store.snapshot.git
            self._active_mind = self._store.snapshot.active_mind
            self._refresh_tree()

    def _on_sessions_changed(self, sender) -> None:
        self._sessions = sender
        self._refresh_tree()

    def _on_git_changed(self, sender) -> None:
        self._git = sender
        self._refresh_tree()

    def _on_active_mind_changed(self, sender) -> None:
        self._active_mind = sender
        self._refresh_tree()

    def _refresh_tree(self) -> None:
        tree = self.query_one(Tree)
        tree.root.remove_children()
        views = build_session_tree(self._sessions, self._git, self._active_mind, self._paths.worktrees_dir)

        def _add_nodes(parent, nodes: list[SessionNodeView]) -> None:
            for view in nodes:
                label = self._build_label(view)
                if view.children:
                    branch = parent.add(label, data=view)
                    branch.expand()
                    branch.allow_expand = False
                    _add_nodes(branch, view.children)
                else:
                    parent.add_leaf(label, data=view)

        _add_nodes(tree.root, views)

    def on_click(self, event: Click) -> None:
        """Double-click launches the highlighted mind."""
        if event.chain >= 2:
            self.action_launch_session()

    def on_tree_node_highlighted(self, event: Tree.NodeHighlighted) -> None:
        """Update preview when cursor moves to a new node."""
        preview = self.query_one(SessionPreview)
        preview.render_preview(event.node.data)

    def action_launch_session(self) -> None:
        """Launch the highlighted mind."""
        tree = self.query_one(Tree)
        node = tree.cursor_node
        if node is None:
            return
        view: SessionNodeView | None = node.data
        if view is None:
            return

        try:
            helpers.mind_launch(
                self._terminal,
                self._tui_client,
                self._sessions_file,
                view.mind,
                self._haiv_root,
            )
        except Exception as e:
            self._errors.append(f"mind_launch: {e}")

    @staticmethod
    def _build_label(view: SessionNodeView) -> Text:
        base = f"[{view.short_id}] {view.mind}: {view.task}"
        suffix = f"  {view.git_stats}"
        style = "bold on dark_green" if view.is_active else ""
        return Text(f"{base}{suffix}", style=style)


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


@dataclass
class SessionNodeView:
    """What the tree needs to render one session node."""

    short_id: int
    mind: str
    task: str
    description: str
    status: str
    git_stats: str
    is_active: bool
    worktree_path: Path | None = None
    children: list[SessionNodeView] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_session_tree(
    sessions: SessionsRaw | None,
    git: GitRaw | None,
    active_mind: ActiveMindRaw | None,
    worktrees_dir: Path | None = None,
) -> list[SessionNodeView]:
    """Assemble a list of session tree nodes from raw data.

    Pure function — raw data in, DTOs out. Testable without Textual.
    """
    if sessions is None:
        return []

    entries = sessions.entries
    by_id = {e.id: e for e in entries}
    pairs = [(e, by_id.get(e.parent_id) if e.parent_id else None) for e in entries]
    roots = build_tree(pairs)
    active = active_mind.mind if active_mind else None
    git_branches = git.branches if git else {}

    def _to_view(node: TreeNode[SessionEntry]) -> SessionNodeView:
        entry = node.item
        stats = git_branches.get(entry.branch, BranchStats())
        wt_path = worktrees_dir / entry.branch if worktrees_dir and entry.branch else None
        return SessionNodeView(
            short_id=entry.short_id,
            mind=entry.mind,
            task=entry.task,
            description=entry.description,
            status=entry.status,
            git_stats=stats.format(),
            is_active=entry.mind == active,
            worktree_path=wt_path,
            children=[_to_view(c) for c in node.child_nodes],
        )

    return [_to_view(r) for r in roots]
