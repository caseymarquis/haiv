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
from textual.containers import Vertical
from textual.events import Click
from textual.widgets import Static, Tree

from haiv.helpers.tui import helpers
from haiv.helpers.tui.TuiModel import ActiveMindRaw, GitRaw, SessionEntry, SessionsRaw
from haiv.helpers.utils.trees import TreeNode, build_tree
from haiv.wrappers.git import BranchStats


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class SessionPreview(Static):
    """Preview area showing details of the highlighted session."""

    DEFAULT_CSS = """
    SessionPreview {
        height: auto;
        max-height: 8;
        padding: 0 1;
        border-top: solid $surface-lighten-2;
    }
    """

    def render_preview(self, view: SessionNodeView | None) -> None:
        if view is None:
            self.update("")
            return
        lines = [
            f"{view.mind}: {view.task}",
            f"Status: {view.status or 'none'} | Session: {view.short_id}",
        ]
        if view.description:
            lines += ["", view.description]
        self.update("\n".join(lines))


class SessionsWidget(Vertical):
    """Sessions tab — tree with inline preview."""

    BINDINGS = [
        Binding("j", "cursor_down", "Cursor Down", show=False, id="sessions.cursor_down"),
        Binding("k", "cursor_up", "Cursor Up", show=False, id="sessions.cursor_up"),
        Binding("enter", "launch_session", "Launch", id="sessions.launch", priority=True),
    ]

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
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
        store = self.app.store
        store.sessions_changed.connect(self._on_sessions_changed)
        store.git_changed.connect(self._on_git_changed)
        store.active_mind_changed.connect(self._on_active_mind_changed)
        if store.snapshot is not None:
            self._sessions = store.snapshot.sessions
            self._git = store.snapshot.git
            self._active_mind = store.snapshot.active_mind
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
        views = build_session_tree(self._sessions, self._git, self._active_mind)

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

        app = self.app
        if app.terminal is not None and app.paths is not None:
            try:
                helpers.mind_launch(
                    app.terminal,
                    app.tui_client,
                    app.paths.user.sessions_file,
                    view.mind,
                    app.paths.root,
                )
            except Exception as e:
                app.internal_errors.append(f"mind_launch: {e}")

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
    children: list[SessionNodeView] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def build_session_tree(
    sessions: SessionsRaw | None,
    git: GitRaw | None,
    active_mind: ActiveMindRaw | None,
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
        return SessionNodeView(
            short_id=entry.short_id,
            mind=entry.mind,
            task=entry.task,
            description=entry.description,
            status=entry.status,
            git_stats=stats.format(),
            is_active=entry.mind == active,
            children=[_to_view(c) for c in node.child_nodes],
        )

    return [_to_view(r) for r in roots]
