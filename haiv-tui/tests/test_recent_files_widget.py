"""RecentFilesWidget — widget-level tests."""

from __future__ import annotations

import time
from collections import deque
from pathlib import Path

import pytest

from textual.widgets import Tree

from haiv.helpers.tui.TuiModel import FileStatus, RecentFilesRaw, RecentFileEntry, TuiModel
from haiv_tui.store import TuiStore
from haiv_tui.widgets.recent_files import RecentFilesWidget

from harness import WidgetTestApp


def _make_widget(store=None, tmp_path=None):
    return RecentFilesWidget(
        store=store or TuiStore(),
        worktrees_dir=tmp_path or Path("/tmp/fake"),
        errors=deque(maxlen=5),
        id="recent-files",
    )


class TestRecentFilesWidget:

    @pytest.mark.asyncio
    async def test_mounts_empty(self):
        app = WidgetTestApp(_make_widget())
        async with app.run_test():
            pass

    @pytest.mark.asyncio
    async def test_populates_on_signal(self):
        store = TuiStore()
        widget = _make_widget(store=store)
        app = WidgetTestApp(widget)
        now = time.time()

        async with app.run_test() as pilot:
            files = RecentFilesRaw(modified=[
                RecentFileEntry(path="src/app.py", worktree="main", mtime=now - 10, additions=3, deletions=1),
                RecentFileEntry(path="src/store.py", worktree="main", mtime=now - 60, additions=1, deletions=0),
            ])
            store.update(TuiModel(recent_files=files), frozenset({"recent_files"}))
            await pilot.pause()

            tree = widget.query_one(Tree)
            # Should have one category node (Recently Modified) with 2 children
            children = list(tree.root.children)
            assert len(children) == 1
            assert len(list(children[0].children)) == 2

    @pytest.mark.asyncio
    async def test_categories_shown_only_when_populated(self):
        store = TuiStore()
        widget = _make_widget(store=store)
        app = WidgetTestApp(widget)
        now = time.time()

        async with app.run_test() as pilot:
            files = RecentFilesRaw(
                modified=[
                    RecentFileEntry(path="app.py", worktree="main", mtime=now, additions=1, deletions=0),
                ],
                deleted=[
                    RecentFileEntry(path="old.py", worktree="main", status=FileStatus.DELETED, deletions=10),
                ],
            )
            store.update(TuiModel(recent_files=files), frozenset({"recent_files"}))
            await pilot.pause()

            tree = widget.query_one(Tree)
            children = list(tree.root.children)
            # 2 categories: Recently Modified and Deleted (no Conflicted)
            assert len(children) == 2

    @pytest.mark.asyncio
    async def test_enter_opens_file(self, tmp_path, monkeypatch):
        """Enter on a highlighted file calls open_with_os."""
        opened_paths: list[Path] = []
        monkeypatch.setattr(
            "haiv_tui.widgets.recent_files.open_with_os",
            lambda p: opened_paths.append(p),
        )

        store = TuiStore()
        now = time.time()
        # Create a real file so is_file() passes
        wt = tmp_path / "worktrees" / "main" / "src"
        wt.mkdir(parents=True)
        (wt / "app.py").write_text("pass")

        widget = RecentFilesWidget(
            store=store,
            worktrees_dir=tmp_path / "worktrees",
            errors=deque(maxlen=5),
            id="recent-files",
        )
        app = WidgetTestApp(widget)

        async with app.run_test() as pilot:
            files = RecentFilesRaw(modified=[
                RecentFileEntry(path="src/app.py", worktree="main", mtime=now, additions=1, deletions=0),
            ])
            store.update(TuiModel(recent_files=files), frozenset({"recent_files"}))
            await pilot.pause()

            tree = widget.query_one(Tree)
            tree.focus()
            await pilot.pause()
            # Navigate into the category and to the file
            await pilot.press("down")  # category node
            await pilot.press("down")  # first file
            await pilot.press("enter")
            await pilot.pause()

            assert len(widget._errors) == 0
            assert len(opened_paths) == 1
            assert opened_paths[0] == tmp_path / "worktrees" / "main" / "src" / "app.py"
