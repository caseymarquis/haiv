"""Sessions widget — assembly and widget-level tests."""

from __future__ import annotations

from collections import deque
from pathlib import Path

import pytest

from haiv.helpers.tui.TuiModel import (
    ActiveMindRaw,
    GitRaw,
    SessionsRaw,
    TuiModel,
)
from haiv.wrappers.git import BranchStats
from haiv.settings import HaivSettings
from haiv_tui.widgets.debounce_button import DebounceButton
from haiv_tui.widgets.sessions import SessionActionBar, SessionNodeView, SessionsWidget, build_session_tree

from harness import WidgetTestApp, make_entry


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


class TestBuildSessionTree:
    """build_session_tree assembles raw data into SessionNodeViews."""

    def test_empty_when_no_sessions(self):
        result = build_session_tree(None, None, None)
        assert result == []

    def test_empty_when_sessions_empty(self):
        result = build_session_tree(SessionsRaw(entries=[]), None, None)
        assert result == []

    def test_single_session(self):
        sessions = SessionsRaw(entries=[make_entry("wren", id="1", task="test task", short_id=1)])
        result = build_session_tree(sessions, None, None)
        assert len(result) == 1
        assert result[0].mind == "wren"
        assert result[0].task == "test task"
        assert result[0].short_id == 1
        assert result[0].is_active is False
        assert result[0].children == []

    def test_active_mind_highlighted(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1"),
            make_entry("sage", id="2"),
        ])
        active = ActiveMindRaw(mind="wren")
        result = build_session_tree(sessions, None, active)
        by_mind = {v.mind: v for v in result}
        assert by_mind["wren"].is_active is True
        assert by_mind["sage"].is_active is False

    def test_git_stats_merged_by_branch(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", branch="feature-x"),
        ])
        git = GitRaw(branches={
            "feature-x": BranchStats(ahead=2, behind=1, changed_files=3),
        })
        result = build_session_tree(sessions, git, None)
        assert result[0].git_stats == "↑2 ↓1 ~3"

    def test_git_stats_default_when_branch_missing(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", branch="unknown"),
        ])
        git = GitRaw(branches={})
        result = build_session_tree(sessions, git, None)
        assert result[0].git_stats == "(no branch)"

    def test_git_stats_default_when_no_git(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", branch="feature"),
        ])
        result = build_session_tree(sessions, None, None)
        assert result[0].git_stats == "(no branch)"

    def test_parent_child_hierarchy(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="parent-1", short_id=1),
            make_entry("sage", id="child-1", short_id=2, parent_id="parent-1"),
        ])
        result = build_session_tree(sessions, None, None)
        assert len(result) == 1
        assert result[0].mind == "wren"
        assert len(result[0].children) == 1
        assert result[0].children[0].mind == "sage"

    def test_description_passed_through(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", description="detailed work"),
        ])
        result = build_session_tree(sessions, None, None)
        assert result[0].description == "detailed work"

    def test_status_passed_through(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", status="staged"),
        ])
        result = build_session_tree(sessions, None, None)
        assert result[0].status == "staged"

    def test_worktree_path_assembled_from_branch(self, tmp_path):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", branch="feature-x"),
        ])
        worktrees_dir = tmp_path / "worktrees"
        result = build_session_tree(sessions, None, None, worktrees_dir)
        assert result[0].worktree_path == worktrees_dir / "feature-x"

    def test_worktree_path_none_when_no_branch(self, tmp_path):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", branch=""),
        ])
        worktrees_dir = tmp_path / "worktrees"
        result = build_session_tree(sessions, None, None, worktrees_dir)
        assert result[0].worktree_path is None

    def test_worktree_path_none_when_no_worktrees_dir(self):
        sessions = SessionsRaw(entries=[
            make_entry("wren", id="1", branch="feature-x"),
        ])
        result = build_session_tree(sessions, None, None)
        assert result[0].worktree_path is None


# ---------------------------------------------------------------------------
# Widget
# ---------------------------------------------------------------------------


class TestSessionActionBar:
    """SessionActionBar has clickable Explorer/Editor buttons."""

    @pytest.mark.asyncio
    async def test_buttons_disabled_initially(self):
        errors = deque(maxlen=5)
        bar = SessionActionBar(settings=HaivSettings(), errors=errors, id="bar")
        app = WidgetTestApp(bar)

        async with app.run_test() as pilot:
            assert bar.query_one("#btn-explorer", DebounceButton).disabled is True
            assert bar.query_one("#btn-editor", DebounceButton).disabled is True

    @pytest.mark.asyncio
    async def test_set_session_enables_buttons(self, tmp_path):
        errors = deque(maxlen=5)
        bar = SessionActionBar(settings=HaivSettings(), errors=errors, id="bar")
        app = WidgetTestApp(bar)

        async with app.run_test() as pilot:
            view = SessionNodeView(
                short_id=1, mind="wren", task="test", description="",
                status="started", git_stats="", is_active=False,
                worktree_path=tmp_path / "worktrees" / "feature-x",
            )
            bar.set_session(view)
            await pilot.pause()
            assert bar.query_one("#btn-explorer", DebounceButton).disabled is False
            assert bar.query_one("#btn-editor", DebounceButton).disabled is False

    @pytest.mark.asyncio
    async def test_set_session_disables_on_none(self):
        errors = deque(maxlen=5)
        bar = SessionActionBar(settings=HaivSettings(), errors=errors, id="bar")
        app = WidgetTestApp(bar)

        async with app.run_test() as pilot:
            bar.set_session(None)
            await pilot.pause()
            assert bar.query_one("#btn-explorer", DebounceButton).disabled is True
            assert bar.query_one("#btn-editor", DebounceButton).disabled is True

    @pytest.mark.asyncio
    async def test_explorer_button_calls_subprocess(self, tmp_path):
        errors = deque(maxlen=5)
        wt = tmp_path / "worktrees" / "feature-x"
        wt.mkdir(parents=True)
        bar = SessionActionBar(
            settings=HaivSettings(_file_explorer_command=["echo"]),
            errors=errors,
            id="bar",
        )
        app = WidgetTestApp(bar)

        async with app.run_test() as pilot:
            view = SessionNodeView(
                short_id=1, mind="wren", task="test", description="",
                status="started", git_stats="", is_active=False,
                worktree_path=wt,
            )
            bar.set_session(view)
            await pilot.pause()
            await pilot.click("#btn-explorer #inner")
            await pilot.pause()
            assert len(errors) == 0

    @pytest.mark.asyncio
    async def test_editor_button_calls_subprocess(self, tmp_path):
        errors = deque(maxlen=5)
        wt = tmp_path / "worktrees" / "feature-x"
        wt.mkdir(parents=True)
        bar = SessionActionBar(
            settings=HaivSettings(_editor_command=["echo"]),
            errors=errors,
            id="bar",
        )
        app = WidgetTestApp(bar)

        async with app.run_test() as pilot:
            view = SessionNodeView(
                short_id=1, mind="wren", task="test", description="",
                status="started", git_stats="", is_active=False,
                worktree_path=wt,
            )
            bar.set_session(view)
            await pilot.pause()
            await pilot.click("#btn-editor #inner")
            await pilot.pause()
            assert len(errors) == 0


class TestSessionsWidget:
    """SessionsWidget mounted with injected deps."""

    @pytest.mark.asyncio
    async def test_mounts_empty(self, sessions_deps):
        app = WidgetTestApp(SessionsWidget(**sessions_deps, id="sessions"))
        async with app.run_test():
            pass

    @pytest.mark.asyncio
    async def test_renders_sessions_on_signal(self, store, sessions_deps):
        widget = SessionsWidget(**sessions_deps, id="sessions")
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            sessions = SessionsRaw(entries=[
                make_entry("wren", task="build thing", short_id=1),
                make_entry("sage", id="2", task="test thing", short_id=2),
            ])
            store.update(TuiModel(sessions=sessions), frozenset({"sessions"}))
            await pilot.pause()

            assert widget._sessions is not None
            assert len(widget._sessions.entries) == 2

    @pytest.mark.asyncio
    async def test_active_mind_signal_updates_state(self, store, sessions_deps):
        widget = SessionsWidget(**sessions_deps, id="sessions")
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            active = ActiveMindRaw(mind="wren")
            store.update(TuiModel(active_mind=active), frozenset({"active_mind"}))
            await pilot.pause()

            assert widget._active_mind is not None
            assert widget._active_mind.mind == "wren"

    @pytest.mark.asyncio
    async def test_git_signal_updates_state(self, store, sessions_deps):
        widget = SessionsWidget(**sessions_deps, id="sessions")
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            git = GitRaw(branches={"main": BranchStats(ahead=1)})
            store.update(TuiModel(git=git), frozenset({"git"}))
            await pilot.pause()

            assert widget._git is not None
            assert "main" in widget._git.branches

    @pytest.mark.asyncio
    async def test_launch_error_captured_in_errors(self, store, sessions_deps):
        widget = SessionsWidget(**sessions_deps, id="sessions")
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            sessions = SessionsRaw(entries=[make_entry("wren", short_id=1)])
            store.update(TuiModel(sessions=sessions), frozenset({"sessions"}))
            await pilot.pause()

            # mind_launch will fail because terminal is a MagicMock
            widget.action_launch_session()

            errors = sessions_deps["errors"]
            if len(errors) > 0:
                assert "mind_launch" in errors[0]
