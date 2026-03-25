"""Recent files — assembly tests."""

import time

from haiv.helpers.tui.TuiModel import (
    CommitEntry,
    CommitFileEntry,
    FileStatus,
    RecentCommitsRaw,
    RecentFileEntry,
    RecentFilesRaw,
)
from haiv_tui.widgets.recent_files import (
    build_commit_views,
    build_file_tree_views,
    format_age,
    shortest_unique_names,
)


class TestShortestUniqueNames:

    def test_all_unique_filenames(self):
        paths = ["src/app.py", "src/store.py", "tests/test_app.py"]
        result = shortest_unique_names(paths)
        assert result == ["app.py", "store.py", "test_app.py"]

    def test_duplicate_filenames_different_parents(self):
        paths = ["src/haiv/helpers/tui/helpers.py", "src/haiv/helpers/utils/helpers.py"]
        result = shortest_unique_names(paths)
        assert result == ["tui/helpers.py", "utils/helpers.py"]

    def test_duplicate_filenames_deeper_disambiguation(self):
        paths = ["a/b/c/foo.py", "a/d/c/foo.py"]
        result = shortest_unique_names(paths)
        assert result == ["b/c/foo.py", "d/c/foo.py"]

    def test_single_file(self):
        result = shortest_unique_names(["src/deep/nested/file.py"])
        assert result == ["file.py"]

    def test_empty_list(self):
        assert shortest_unique_names([]) == []

    def test_identical_paths(self):
        paths = ["src/foo.py", "src/foo.py"]
        result = shortest_unique_names(paths)
        assert result == ["src/foo.py", "src/foo.py"]

    def test_root_level_files(self):
        paths = ["README.md", "setup.py"]
        result = shortest_unique_names(paths)
        assert result == ["README.md", "setup.py"]

    def test_mix_of_unique_and_duplicate(self):
        paths = [
            "haiv-tui/src/haiv_tui/app.py",
            "haiv-lib/src/haiv/app.py",
            "haiv-tui/src/haiv_tui/store.py",
        ]
        result = shortest_unique_names(paths)
        assert result == ["haiv_tui/app.py", "haiv/app.py", "store.py"]

    def test_backslash_paths_treated_as_single_component(self):
        """Windows-style backslash paths must not defeat disambiguation.

        git ls-files always outputs forward slashes, but if a backslash path
        somehow sneaks in (e.g. via str(Path) on Windows), PurePosixPath
        treats the whole thing as one component and returns it unchanged.
        This test locks in the expectation: forward-slash paths work,
        backslash paths degrade to the full string (not silently wrong).
        """
        # Forward slashes: proper disambiguation
        posix = ["src/tui/helpers.py", "src/utils/helpers.py"]
        assert shortest_unique_names(posix) == ["tui/helpers.py", "utils/helpers.py"]

        # Backslash paths: each is an opaque blob, both "filenames" differ,
        # so they come back as-is at depth 1 — no silent truncation
        win = ["src\\tui\\helpers.py", "src\\utils\\helpers.py"]
        assert shortest_unique_names(win) == [
            "src\\tui\\helpers.py",
            "src\\utils\\helpers.py",
        ]

    def test_heavy_overlap(self):
        paths = [
            "a/b/c/d/e/f.py",
            "a/X/c/d/e/f.py",
            "a/b/Y/d/e/f.py",
            "a/b/c/Z/e/f.py",
            "a/b/c/d/W/f.py",
            "a/b/c/d/e/g.py",
            "a/b/c/d/e/h.py",
            "z/b/c/d/e/f.py",
            "a/X/c/d/e/g.py",
            "a/b/c/d/e/f.txt",
        ]
        result = shortest_unique_names(paths)
        assert result == [
            "a/b/c/d/e/f.py",   # collides all the way up with z/b/c/d/e/f.py
            "X/c/d/e/f.py",     # "c/d/e/f.py" collides with b/Y/d and others
            "Y/d/e/f.py",       # "d/e/f.py" collides with Z/e/f.py etc
            "Z/e/f.py",         # "e/f.py" collides with W/f.py... no, W has different parent
            "W/f.py",           # unique at this depth
            "b/c/d/e/g.py",     # "e/g.py" collides with X/c/d/e/g.py
            "h.py",             # unique filename
            "z/b/c/d/e/f.py",   # collides all the way with a/b/c/d/e/f.py
            "X/c/d/e/g.py",     # "e/g.py" collides with b/c/d/e/g.py
            "f.txt",            # unique filename
        ]


class TestFormatAge:

    def test_just_now(self):
        assert format_age(0) == "just now"
        assert format_age(30) == "just now"
        assert format_age(59) == "just now"

    def test_minutes(self):
        assert format_age(60) == "1m"
        assert format_age(120) == "2m"
        assert format_age(3599) == "59m"

    def test_hours_and_minutes(self):
        assert format_age(3600) == "1h"
        assert format_age(3660) == "1h 1m"
        assert format_age(7380) == "2h 3m"

    def test_days(self):
        assert format_age(86400) == "1d"
        assert format_age(172800) == "2d"


class TestBuildFileTreeViews:

    def test_empty_raw(self):
        raw = RecentFilesRaw()
        views = build_file_tree_views(raw)
        assert len(views) == 3
        assert all(len(v.entries) == 0 for v in views)

    def test_modified_files_appear_in_recently_modified(self):
        now = time.time()
        raw = RecentFilesRaw(modified=[
            RecentFileEntry(path="src/app.py", worktree="main", mtime=now - 30, additions=3, deletions=1),
            RecentFileEntry(path="src/store.py", worktree="main", mtime=now - 120, additions=1, deletions=0),
        ])
        views = build_file_tree_views(raw)
        modified = views[1]  # index 1 = Recently Modified
        assert modified.label == "Recently Modified"
        assert len(modified.entries) == 2
        assert modified.entries[0].display_path == "app.py"
        assert modified.entries[1].display_path == "store.py"

    def test_deleted_files_appear_in_deleted(self):
        raw = RecentFilesRaw(deleted=[
            RecentFileEntry(path="old.py", worktree="main", status=FileStatus.DELETED, deletions=20),
        ])
        views = build_file_tree_views(raw)
        deleted = views[2]  # index 2 = Deleted
        assert deleted.label == "Deleted"
        assert len(deleted.entries) == 1
        assert deleted.entries[0].display_path == "old.py"
        assert deleted.entries[0].age_display == ""  # no mtime for deleted

    def test_conflicted_files_appear_first(self):
        now = time.time()
        raw = RecentFilesRaw(
            conflicted=[
                RecentFileEntry(path="merge.py", worktree="main", mtime=now, status=FileStatus.CONFLICTED),
            ],
            modified=[
                RecentFileEntry(path="app.py", worktree="main", mtime=now, additions=1, deletions=0),
            ],
        )
        views = build_file_tree_views(raw)
        assert views[0].label == "Conflicted"
        assert len(views[0].entries) == 1
        assert views[1].label == "Recently Modified"
        assert len(views[1].entries) == 1

    def test_worktree_filter(self):
        now = time.time()
        raw = RecentFilesRaw(modified=[
            RecentFileEntry(path="src/app.py", worktree="main", mtime=now, additions=1, deletions=0),
            RecentFileEntry(path="src/app.py", worktree="feature", mtime=now, additions=2, deletions=0),
        ])
        views = build_file_tree_views(raw, worktree="main")
        modified = views[1]
        assert len(modified.entries) == 1
        assert modified.entries[0].worktree == "main"

    def test_age_display_on_modified(self):
        now = time.time()
        raw = RecentFilesRaw(modified=[
            RecentFileEntry(path="a.py", worktree="main", mtime=now - 30, additions=1, deletions=0),
        ])
        views = build_file_tree_views(raw)
        assert views[1].entries[0].age_display == "just now"

    def test_diff_display_formatting(self):
        now = time.time()
        raw = RecentFilesRaw(modified=[
            RecentFileEntry(path="a.py", worktree="main", mtime=now, additions=5, deletions=2),
        ])
        views = build_file_tree_views(raw)
        entry = views[1].entries[0]
        assert "+5" in entry.diff_display
        assert "-2" in entry.diff_display
        assert entry.diff_style == "green"  # more additions than deletions


class TestBuildCommitViews:

    def test_empty_raw(self):
        raw = RecentCommitsRaw()
        views = build_commit_views(raw)
        assert views == []

    def test_commit_with_files(self):
        now = time.time()
        raw = RecentCommitsRaw(commits=[
            CommitEntry(
                hash="abc123def456",
                short_hash="abc123d",
                subject="fix recent files on Windows",
                author="Casey",
                timestamp=now - 120,
                worktree="main",
                files=[
                    CommitFileEntry(path="src/widget.py", additions=5, deletions=2),
                    CommitFileEntry(path="src/model.py", additions=1, deletions=0),
                ],
            ),
        ])
        views = build_commit_views(raw)
        assert len(views) == 1
        cv = views[0]
        assert cv.short_hash == "abc123d"
        assert cv.subject == "fix recent files on Windows"
        assert cv.worktree == "main"
        assert cv.age_display == "2m"
        assert len(cv.files) == 2
        assert cv.files[0].display_path == "widget.py"
        assert cv.files[1].display_path == "model.py"
        assert "+5" in cv.files[0].diff_display

    def test_worktree_filter(self):
        now = time.time()
        raw = RecentCommitsRaw(commits=[
            CommitEntry(short_hash="aaa", subject="on main", timestamp=now, worktree="main"),
            CommitEntry(short_hash="bbb", subject="on feature", timestamp=now, worktree="feature"),
        ])
        views = build_commit_views(raw, worktree="main")
        assert len(views) == 1
        assert views[0].short_hash == "aaa"

    def test_file_disambiguation_within_commit(self):
        now = time.time()
        raw = RecentCommitsRaw(commits=[
            CommitEntry(
                short_hash="abc",
                subject="refactor",
                timestamp=now,
                worktree="main",
                files=[
                    CommitFileEntry(path="src/tui/helpers.py", additions=1, deletions=0),
                    CommitFileEntry(path="src/utils/helpers.py", additions=2, deletions=0),
                ],
            ),
        ])
        views = build_commit_views(raw)
        assert views[0].files[0].display_path == "tui/helpers.py"
        assert views[0].files[1].display_path == "utils/helpers.py"
