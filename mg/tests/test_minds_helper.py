"""Tests for mg.helpers.minds module."""

import pytest
from pathlib import Path

from mg.helpers.minds import (
    Mind,
    MindPaths,
    MindNotFoundError,
    DuplicateMindError,
    MindStructureIssue,
    list_mind_paths,
    resolve_mind,
    list_minds,
)


class TestMindPaths:
    """Tests for MindPaths dataclass."""

    def test_startup_path(self, tmp_path):
        """startup property returns root/startup."""
        paths = MindPaths(root=tmp_path / "wren")
        assert paths.startup_dir == tmp_path / "wren" / "startup"

    def test_docs_path(self, tmp_path):
        """docs property returns root/docs."""
        paths = MindPaths(root=tmp_path / "wren")
        assert paths.docs_dir == tmp_path / "wren" / "docs"

    def test_references_file_path(self, tmp_path):
        """references_file property returns startup/references.toml."""
        paths = MindPaths(root=tmp_path / "wren")
        assert paths.references_file == tmp_path / "wren" / "startup" / "references.toml"


class TestMind:
    """Tests for Mind dataclass."""

    def test_name_derived_from_path(self, tmp_path):
        """name property returns folder name."""
        mind = Mind(paths=MindPaths(root=tmp_path / "wren"))
        assert mind.name == "wren"

    def test_get_references_empty_when_no_file(self, tmp_path):
        """get_references returns empty list when file doesn't exist."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()
        mind = Mind(paths=MindPaths(root=mind_dir))

        assert mind.get_references() == []

    def test_get_references_parses_toml(self, tmp_path):
        """get_references parses references.toml correctly."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "references.toml").write_text('''
[[references]]
path = "src/mg_project/__assets__/roles/coo.md"

[[references]]
path = "users/casey/state/minds/wren/docs/problems.md"
''')

        mind = Mind(paths=MindPaths(root=mind_dir))
        refs = mind.get_references()

        assert len(refs) == 2
        assert "src/mg_project/__assets__/roles/coo.md" in refs
        assert "users/casey/state/minds/wren/docs/problems.md" in refs

    def test_get_references_skips_entries_without_path(self, tmp_path):
        """get_references skips entries missing path key."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "references.toml").write_text('''
[[references]]
path = "valid/path.md"

[[references]]
description = "missing path key"
''')

        mind = Mind(paths=MindPaths(root=mind_dir))
        refs = mind.get_references()

        assert refs == ["valid/path.md"]

    def test_get_startup_files_empty_when_no_dir(self, tmp_path):
        """get_startup_files returns empty list when startup/ doesn't exist."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()
        mind = Mind(paths=MindPaths(root=mind_dir))

        assert mind.get_startup_files() == []

    def test_get_startup_files_excludes_references_toml(self, tmp_path):
        """get_startup_files excludes references.toml."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "references.toml").write_text("# refs")
        (startup_dir / "identity.md").write_text("# identity")
        (startup_dir / "current-focus.md").write_text("# focus")

        mind = Mind(paths=MindPaths(root=mind_dir))
        files = mind.get_startup_files()

        assert len(files) == 2
        names = [f.name for f in files]
        assert "identity.md" in names
        assert "current-focus.md" in names
        assert "references.toml" not in names

    def test_get_startup_files_sorted_by_name(self, tmp_path):
        """get_startup_files returns files sorted by name."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "z-last.md").write_text("")
        (startup_dir / "a-first.md").write_text("")
        (startup_dir / "m-middle.md").write_text("")

        mind = Mind(paths=MindPaths(root=mind_dir))
        files = mind.get_startup_files()

        names = [f.name for f in files]
        assert names == ["a-first.md", "m-middle.md", "z-last.md"]

    def test_get_startup_files_excludes_directories(self, tmp_path):
        """get_startup_files only returns files, not directories."""
        mind_dir = tmp_path / "wren"
        startup_dir = mind_dir / "startup"
        startup_dir.mkdir(parents=True)
        (startup_dir / "identity.md").write_text("")
        (startup_dir / "subdir").mkdir()

        mind = Mind(paths=MindPaths(root=mind_dir))
        files = mind.get_startup_files()

        assert len(files) == 1
        assert files[0].name == "identity.md"


class TestMindEnsureStructure:
    """Tests for Mind.ensure_structure method."""

    def test_creates_missing_startup_dir(self, tmp_path):
        """Creates startup/ directory if missing."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()
        mind = Mind(paths=MindPaths(root=mind_dir))

        issues = mind.ensure_structure(fix=True)

        assert mind.paths.startup_dir.exists()
        startup_issues = [i for i in issues if "startup/ directory" in i.message]
        assert len(startup_issues) == 1
        assert startup_issues[0].fixed is True

    def test_creates_missing_references_toml(self, tmp_path):
        """Creates startup/references.toml if missing."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()
        mind = Mind(paths=MindPaths(root=mind_dir))

        issues = mind.ensure_structure(fix=True)

        assert mind.paths.references_file.exists()
        ref_issues = [i for i in issues if "references.toml" in i.message]
        assert len(ref_issues) == 1
        assert ref_issues[0].fixed is True

    def test_creates_missing_docs_dir(self, tmp_path):
        """Creates docs/ directory if missing."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()
        mind = Mind(paths=MindPaths(root=mind_dir))

        issues = mind.ensure_structure(fix=True)

        assert mind.paths.docs_dir.exists()
        docs_issues = [i for i in issues if "docs/ directory" in i.message]
        assert len(docs_issues) == 1
        assert docs_issues[0].fixed is True

    def test_no_issues_when_structure_complete(self, tmp_path):
        """Returns empty list when structure is complete."""
        mind_dir = tmp_path / "wren"
        (mind_dir / "startup").mkdir(parents=True)
        (mind_dir / "startup" / "references.toml").write_text("")
        (mind_dir / "docs").mkdir()
        mind = Mind(paths=MindPaths(root=mind_dir))

        issues = mind.ensure_structure(fix=True)

        assert issues == []

    def test_fix_false_reports_but_does_not_fix(self, tmp_path):
        """With fix=False, reports issues but doesn't create files."""
        mind_dir = tmp_path / "wren"
        mind_dir.mkdir()
        mind = Mind(paths=MindPaths(root=mind_dir))

        issues = mind.ensure_structure(fix=False)

        assert len(issues) == 3  # startup, references.toml, docs
        assert not mind.paths.startup_dir.exists()
        assert not mind.paths.docs_dir.exists()
        assert all(not i.fixed for i in issues)


class TestListMindPaths:
    """Tests for list_mind_paths function."""

    def test_empty_when_dir_not_exists(self, tmp_path):
        """Returns empty list when minds_dir doesn't exist."""
        result = list_mind_paths(tmp_path / "nonexistent")
        assert result == []

    def test_finds_top_level_minds(self, tmp_path):
        """Finds minds directly in minds_dir."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        (minds_dir / "wren").mkdir()
        (minds_dir / "forge").mkdir()

        result = list_mind_paths(minds_dir)

        assert len(result) == 2
        names = [name for name, _ in result]
        assert "wren" in names
        assert "forge" in names

    def test_finds_minds_in_organizational_dirs(self, tmp_path):
        """Finds minds inside underscore directories."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        (minds_dir / "_new" / "reed").mkdir(parents=True)
        (minds_dir / "_archived" / "old-worker").mkdir(parents=True)

        result = list_mind_paths(minds_dir)

        assert len(result) == 2
        names = [name for name, _ in result]
        assert "reed" in names
        assert "old-worker" in names

    def test_excludes_underscore_named_minds(self, tmp_path):
        """Excludes directories that start with underscore."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        (minds_dir / "wren").mkdir()
        (minds_dir / "_hidden").mkdir()  # Should be treated as organizational

        result = list_mind_paths(minds_dir)

        assert len(result) == 1
        assert result[0][0] == "wren"

    def test_excludes_underscore_minds_in_organizational_dirs(self, tmp_path):
        """Excludes underscore-named directories inside organizational dirs."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        (minds_dir / "_new" / "reed").mkdir(parents=True)
        (minds_dir / "_new" / "_template").mkdir(parents=True)  # Should be excluded

        result = list_mind_paths(minds_dir)

        assert len(result) == 1
        assert result[0][0] == "reed"

    def test_ignores_files(self, tmp_path):
        """Ignores files in minds_dir."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        (minds_dir / "wren").mkdir()
        (minds_dir / "README.md").write_text("# Minds")

        result = list_mind_paths(minds_dir)

        assert len(result) == 1
        assert result[0][0] == "wren"

    def test_sorted_by_name(self, tmp_path):
        """Returns results sorted by name."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        (minds_dir / "zara").mkdir()
        (minds_dir / "alice").mkdir()
        (minds_dir / "bob").mkdir()

        result = list_mind_paths(minds_dir)

        names = [name for name, _ in result]
        assert names == ["alice", "bob", "zara"]

    def test_raises_on_duplicate_names(self, tmp_path):
        """Raises DuplicateMindError when same name exists in multiple locations."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        (minds_dir / "reed").mkdir()
        (minds_dir / "_new" / "reed").mkdir(parents=True)

        with pytest.raises(DuplicateMindError) as exc_info:
            list_mind_paths(minds_dir)

        assert exc_info.value.name == "reed"
        assert len(exc_info.value.locations) == 2


class TestResolveMind:
    """Tests for resolve_mind function."""

    def test_resolves_top_level_mind(self, tmp_path):
        """Resolves mind directly in minds_dir."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "wren").mkdir(parents=True)

        mind = resolve_mind("wren", minds_dir)

        assert mind.name == "wren"
        assert mind.paths.root == minds_dir / "wren"

    def test_resolves_mind_in_organizational_dir(self, tmp_path):
        """Resolves mind inside underscore directory."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "_new" / "reed").mkdir(parents=True)

        mind = resolve_mind("reed", minds_dir)

        assert mind.name == "reed"
        assert mind.paths.root == minds_dir / "_new" / "reed"

    def test_raises_when_not_found(self, tmp_path):
        """Raises MindNotFoundError when mind doesn't exist."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "wren").mkdir(parents=True)

        with pytest.raises(MindNotFoundError) as exc_info:
            resolve_mind("unknown", minds_dir)

        assert exc_info.value.name == "unknown"
        assert "wren" in exc_info.value.available

    def test_raises_when_minds_dir_not_exists(self, tmp_path):
        """Raises MindNotFoundError when minds_dir doesn't exist."""
        with pytest.raises(MindNotFoundError) as exc_info:
            resolve_mind("wren", tmp_path / "nonexistent")

        assert exc_info.value.name == "wren"
        assert exc_info.value.available == []

    def test_raises_on_duplicate(self, tmp_path):
        """Raises DuplicateMindError when duplicate names exist."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "reed").mkdir(parents=True)
        (minds_dir / "_new" / "reed").mkdir(parents=True)

        with pytest.raises(DuplicateMindError):
            resolve_mind("reed", minds_dir)


class TestListMinds:
    """Tests for list_minds function."""

    def test_returns_mind_objects(self, tmp_path):
        """Returns list of Mind objects."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "wren").mkdir(parents=True)
        (minds_dir / "forge").mkdir()

        minds = list_minds(minds_dir)

        assert len(minds) == 2
        assert all(isinstance(m, Mind) for m in minds)
        names = [m.name for m in minds]
        assert "wren" in names
        assert "forge" in names

    def test_empty_when_no_minds(self, tmp_path):
        """Returns empty list when no minds exist."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()

        minds = list_minds(minds_dir)

        assert minds == []

    def test_empty_when_dir_not_exists(self, tmp_path):
        """Returns empty list when minds_dir doesn't exist."""
        minds = list_minds(tmp_path / "nonexistent")

        assert minds == []


# =============================================================================
# Mind Creation Tests
# =============================================================================

from unittest.mock import patch

from mg.helpers.minds import (
    InvalidMindNameError,
    MindExistsError,
    validate_mind_name,
    generate_mind_name,
    mind_exists,
    scaffold_mind,
)


class TestValidateMindName:
    """Tests for validate_mind_name function."""

    def test_valid_simple_name(self):
        """Accepts simple lowercase name."""
        validate_mind_name("wren")  # Should not raise

    def test_valid_name_with_numbers(self):
        """Accepts name with numbers (not at start)."""
        validate_mind_name("wren2")  # Should not raise

    def test_valid_name_with_hyphen(self):
        """Accepts name with hyphens."""
        validate_mind_name("my-mind")  # Should not raise

    def test_valid_name_with_underscore(self):
        """Accepts name with underscores (not at start)."""
        validate_mind_name("my_mind")  # Should not raise

    def test_rejects_empty_name(self):
        """Rejects empty string."""
        with pytest.raises(InvalidMindNameError) as exc_info:
            validate_mind_name("")
        assert "empty" in exc_info.value.reason.lower()

    def test_rejects_uppercase(self):
        """Rejects names with uppercase letters."""
        with pytest.raises(InvalidMindNameError) as exc_info:
            validate_mind_name("Wren")
        assert "lowercase" in exc_info.value.reason.lower()

    def test_rejects_underscore_start(self):
        """Rejects names starting with underscore."""
        with pytest.raises(InvalidMindNameError) as exc_info:
            validate_mind_name("_wren")
        assert "underscore" in exc_info.value.reason.lower()

    def test_rejects_number_start(self):
        """Rejects names starting with number."""
        with pytest.raises(InvalidMindNameError) as exc_info:
            validate_mind_name("123wren")
        assert "letter" in exc_info.value.reason.lower()

    def test_rejects_special_chars(self):
        """Rejects names with special characters."""
        with pytest.raises(InvalidMindNameError) as exc_info:
            validate_mind_name("wren@home")
        assert "alphanumeric" in exc_info.value.reason.lower()


class TestMindExists:
    """Tests for mind_exists function."""

    def test_returns_false_when_dir_not_exists(self, tmp_path):
        """Returns False when minds_dir doesn't exist."""
        assert mind_exists("wren", tmp_path / "nonexistent") is False

    def test_returns_false_when_mind_not_exists(self, tmp_path):
        """Returns False when mind doesn't exist."""
        minds_dir = tmp_path / "minds"
        minds_dir.mkdir()
        assert mind_exists("wren", minds_dir) is False

    def test_returns_true_for_top_level_mind(self, tmp_path):
        """Returns True for mind at top level."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "wren").mkdir(parents=True)
        assert mind_exists("wren", minds_dir) is True

    def test_returns_true_for_mind_in_org_dir(self, tmp_path):
        """Returns True for mind in organizational directory."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "_new" / "robin").mkdir(parents=True)
        assert mind_exists("robin", minds_dir) is True


class TestGenerateMindName:
    """Tests for generate_mind_name function."""

    def test_returns_generated_name(self):
        """Returns name from subprocess."""
        with patch("mg.helpers.minds.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "sparrow\n"
            mock_run.return_value.returncode = 0

            name = generate_mind_name(existing=[])

        assert name == "sparrow"

    def test_avoids_existing_names(self):
        """Passes existing names to avoid duplicates."""
        with patch("mg.helpers.minds.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "robin\n"
            mock_run.return_value.returncode = 0

            generate_mind_name(existing=["wren", "forge"])

        # Check that existing names were passed in the user prompt (last arg)
        call_args = mock_run.call_args[0][0]
        user_prompt = call_args[-1]
        assert "wren" in user_prompt

    def test_raises_on_subprocess_failure(self):
        """Raises RuntimeError when subprocess fails."""
        with patch("mg.helpers.minds.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "error"

            with pytest.raises(RuntimeError):
                generate_mind_name(existing=[])


class TestScaffoldMind:
    """Tests for scaffold_mind function."""

    @pytest.fixture
    def templates(self):
        """Create TemplateRenderer for mg_core assets."""
        import mg_core
        from mg.paths import PkgPaths
        from mg.templates import TemplateRenderer

        pkg = PkgPaths.from_module(mg_core)
        return TemplateRenderer(pkg.assets_dir)

    def test_creates_mind_in_new_folder(self, tmp_path, templates):
        """Creates mind folder in _new/ organizational directory."""
        minds_dir = tmp_path / "minds"

        mind = scaffold_mind("robin", minds_dir, templates)

        assert mind.name == "robin"
        assert mind.paths.root == minds_dir / "_new" / "robin"
        assert mind.paths.startup_dir.is_dir()
        assert mind.paths.docs_dir.is_dir()

    def test_creates_startup_files(self, tmp_path, templates):
        """Creates all startup files."""
        minds_dir = tmp_path / "minds"

        mind = scaffold_mind("robin", minds_dir, templates)

        assert mind.paths.welcome_file.is_file()
        assert mind.paths.immediate_plan_file.is_file()
        assert mind.paths.long_term_vision_file.is_file()
        assert mind.paths.my_process_file.is_file()
        assert mind.paths.scratchpad_file.is_file()
        assert mind.paths.references_file.is_file()

    def test_raises_if_mind_exists(self, tmp_path, templates):
        """Raises MindExistsError if mind already exists."""
        minds_dir = tmp_path / "minds"
        (minds_dir / "robin").mkdir(parents=True)

        with pytest.raises(MindExistsError):
            scaffold_mind("robin", minds_dir, templates)
