"""Recent commits — assembly and gathering tests."""

import time

from haiv.helpers.tui.TuiModel import CommitEntry, CommitFileEntry, RecentCommitsRaw, RecentFileEntry
from haiv.helpers.tui.recent_commits import parse_git_log_numstat
from haiv.helpers.tui.recent_files import file_sort_key
from haiv_tui.widgets.recent_files import build_commit_views, shortest_unique_names


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

    def test_multiple_commits_keep_files_separate(self):
        """Each commit's files must stay with their commit, not merge together."""
        now = time.time()
        raw = RecentCommitsRaw(commits=[
            CommitEntry(
                short_hash="aaa",
                subject="first commit",
                timestamp=now - 60,
                worktree="main",
                files=[
                    CommitFileEntry(path="a.py", additions=1, deletions=0),
                ],
            ),
            CommitEntry(
                short_hash="bbb",
                subject="second commit",
                timestamp=now - 120,
                worktree="main",
                files=[
                    CommitFileEntry(path="b.py", additions=2, deletions=1),
                    CommitFileEntry(path="c.py", additions=3, deletions=0),
                ],
            ),
        ])
        views = build_commit_views(raw)
        assert len(views) == 2
        assert len(views[0].files) == 1
        assert views[0].files[0].full_path == "a.py"
        assert len(views[1].files) == 2
        assert views[1].files[0].full_path == "b.py"
        assert views[1].files[1].full_path == "c.py"

    def test_commit_with_no_files_doesnt_steal_from_next(self):
        """A merge commit (no files) must not cause the next commit's files to shift."""
        now = time.time()
        raw = RecentCommitsRaw(commits=[
            CommitEntry(
                short_hash="merge1",
                subject="Merge branch 'feature'",
                timestamp=now - 60,
                worktree="main",
                files=[],
            ),
            CommitEntry(
                short_hash="aaa",
                subject="real work",
                timestamp=now - 120,
                worktree="main",
                files=[
                    CommitFileEntry(path="a.py", additions=5, deletions=0),
                ],
            ),
        ])
        views = build_commit_views(raw)
        assert len(views) == 2
        assert views[0].files == []
        assert views[0].subject == "Merge branch 'feature'"
        assert len(views[1].files) == 1
        assert views[1].files[0].full_path == "a.py"


class TestParseGitLogNumstat:
    """Tests for parsing the combined git log --numstat output."""

    def test_two_commits_with_files(self):
        output = (
            "\x00aaaa\x00aaa\x00first commit\x00Alice\x001700000000\n"
            "\n"
            "3\t1\tsrc/app.py\n"
            "1\t0\tsrc/model.py\n"
            "\x00bbbb\x00bbb\x00second commit\x00Bob\x001699999000\n"
            "\n"
            "5\t2\ttests/test_app.py\n"
        )
        commits = parse_git_log_numstat(output)
        assert len(commits) == 2

        assert commits[0].short_hash == "aaa"
        assert commits[0].subject == "first commit"
        assert len(commits[0].files) == 2
        assert commits[0].files[0].path == "src/app.py"
        assert commits[0].files[0].additions == 3
        assert commits[0].files[0].deletions == 1
        assert commits[0].files[1].path == "src/model.py"

        assert commits[1].short_hash == "bbb"
        assert len(commits[1].files) == 1
        assert commits[1].files[0].path == "tests/test_app.py"

    def test_merge_commit_no_files(self):
        """A merge commit with no files must not steal files from the next commit."""
        output = (
            "\x00mmmm\x00mmm\x00Merge branch 'feature'\x00Alice\x001700000000\n"
            "\n"
            "\x00aaaa\x00aaa\x00real work\x00Bob\x001699999000\n"
            "\n"
            "5\t0\tsrc/feature.py\n"
        )
        commits = parse_git_log_numstat(output)
        assert len(commits) == 2
        assert commits[0].subject == "Merge branch 'feature'"
        assert commits[0].files == []
        assert commits[1].subject == "real work"
        assert len(commits[1].files) == 1
        assert commits[1].files[0].path == "src/feature.py"

    def test_empty_output(self):
        assert parse_git_log_numstat("") == []
        assert parse_git_log_numstat("   ") == []

    def test_single_commit_no_files(self):
        output = "\x00aaaa\x00aaa\x00empty commit\x00Alice\x001700000000\n\n"
        commits = parse_git_log_numstat(output)
        assert len(commits) == 1
        assert commits[0].files == []

    def test_binary_files_dash_stats(self):
        """Binary files show '-' for additions/deletions in numstat."""
        output = (
            "\x00aaaa\x00aaa\x00add image\x00Alice\x001700000000\n"
            "\n"
            "-\t-\tlogo.png\n"
            "3\t1\tREADME.md\n"
        )
        commits = parse_git_log_numstat(output)
        assert len(commits[0].files) == 2
        assert commits[0].files[0].path == "logo.png"
        assert commits[0].files[0].additions == 0
        assert commits[0].files[0].deletions == 0


class TestFileSort:

    def _entry(self, path: str, worktree: str = "main") -> RecentFileEntry:
        return RecentFileEntry(path=path, worktree=worktree)

    def test_sorts_by_leaf_not_directory(self):
        """app.py in tests/ sorts next to app.py in src/, not after all src/ files."""
        entries = [
            self._entry("src/zebra.py"),
            self._entry("tests/app.py"),
            self._entry("src/app.py"),
        ]
        entries.sort(key=file_sort_key)
        assert [e.path for e in entries] == [
            "src/app.py",
            "tests/app.py",
            "src/zebra.py",
        ]

    def test_case_insensitive(self):
        entries = [
            self._entry("src/Zebra.py"),
            self._entry("src/alpha.py"),
            self._entry("src/Beta.py"),
        ]
        entries.sort(key=file_sort_key)
        assert [e.path for e in entries] == [
            "src/alpha.py",
            "src/Beta.py",
            "src/Zebra.py",
        ]

    def test_underscore_ignored(self):
        """_private.py sorts near 'p', not before everything."""
        entries = [
            self._entry("_private.py"),
            self._entry("alpha.py"),
            self._entry("zebra.py"),
        ]
        entries.sort(key=file_sort_key)
        assert [e.path for e in entries] == [
            "alpha.py",
            "_private.py",
            "zebra.py",
        ]

    def test_forward_slash_paths(self):
        """Git's forward-slash paths: leaf is extracted correctly."""
        entries = [
            self._entry("deeply/nested/dir/beta.py"),
            self._entry("alpha.py"),
        ]
        entries.sort(key=file_sort_key)
        assert [e.path for e in entries] == [
            "alpha.py",
            "deeply/nested/dir/beta.py",
        ]

    def test_backslash_paths_no_leaf_extraction(self):
        """Backslash paths don't split — whole path becomes the leaf.

        This is expected: git always gives forward slashes. If backslash
        paths sneak in, they sort as opaque strings rather than crashing.
        """
        entries = [
            self._entry("src\\zebra.py"),
            self._entry("src\\alpha.py"),
        ]
        entries.sort(key=file_sort_key)
        # Sorted as opaque strings (no leaf extraction)
        assert [e.path for e in entries] == [
            "src\\alpha.py",
            "src\\zebra.py",
        ]

    def test_mixed_worktrees_sort_separately(self):
        entries = [
            self._entry("zebra.py", worktree="main"),
            self._entry("alpha.py", worktree="feature"),
            self._entry("alpha.py", worktree="main"),
        ]
        entries.sort(key=file_sort_key)
        assert [(e.worktree, e.path) for e in entries] == [
            ("feature", "alpha.py"),
            ("main", "alpha.py"),
            ("main", "zebra.py"),
        ]
