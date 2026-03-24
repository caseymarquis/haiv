"""Recent files — assembly tests."""

from haiv_tui.widgets.recent_files import shortest_unique_names


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
