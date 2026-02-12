"""Integration tests for mg minds stage command.

Tests the full execute() behavior including:
- Directory structure creation
- Name generation when not provided
- Name validation
- Template creation
- Output prompts
- Worktree creation
- Clean working tree enforcement
"""

from unittest.mock import patch

import pytest

from mg import test
from mg.errors import CommandError
from mg.helpers.sessions import load_sessions
from mg.test import Sandbox
from mg.wrappers.git import Git


# Store original Git.run before any patching
_original_git_run = Git.run


def _intercept_worktree_list(worktree_output: str):
    """Return a Git.run replacement that intercepts 'worktree list --porcelain'."""
    def mock_run(self, cmd, *, intent=None):
        if cmd == "worktree list --porcelain":
            return worktree_output
        return _original_git_run(self, cmd, intent=intent)
    return mock_run


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sandbox():
    """Sandbox with git repo initialized."""
    sb = test.create_sandbox()
    root = sb.ctx.paths.root
    git = Git(root, quiet=True)

    # Initialize git repo with explicit main branch
    git.run("init -b main")
    git.run("config user.email test@test.com")
    git.run("config user.name Test")

    # Create initial commit (required for worktrees)
    (root / "README.md").write_text("# Test\n")
    git.run("add .")
    git.run("commit -m 'Initial commit'")

    return sb


# =============================================================================
# Command Routing Tests
# =============================================================================


class TestRouting:
    """Test command routes correctly."""

    def test_routes_to_minds_stage(self):
        """mg minds stage routes to correct file."""
        match = test.require_routes_to("minds stage")
        assert match.file.name == "stage.py"
        assert "minds" in str(match.file.parent)


# =============================================================================
# Name Handling Tests
# =============================================================================


class TestNameHandling:
    """Test name handling (provided vs generated)."""

    def test_uses_provided_name(self, sandbox: Sandbox):
        """Uses --name when provided."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert (sandbox.ctx.paths.user.minds_dir / "robin").is_dir()

    def test_generates_name_when_not_provided(self, sandbox: Sandbox):
        """Generates a name when --name not provided."""
        with patch("mg.helpers.minds.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "sparrow\n"
            mock_run.return_value.returncode = 0
            sandbox.run('minds stage --task "test" --from-branch main')
        # Check that a mind folder was created
        minds_dir = sandbox.ctx.paths.user.minds_dir
        assert minds_dir.exists()
        assert (minds_dir / "sparrow").is_dir()

    def test_rejects_duplicate_name(self, sandbox: Sandbox):
        """Rejects name that already exists."""
        # Create existing mind
        (sandbox.ctx.paths.user.minds_dir / "robin").mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            sandbox.run('minds stage --name robin --task "test" --from-branch main')

    def test_rejects_duplicate_in_organizational_folder(self, sandbox: Sandbox):
        """Rejects name that exists in organizational folder like _staging/."""
        (sandbox.ctx.paths.user.minds_dir / "_staging" / "robin").mkdir(parents=True)
        with pytest.raises(CommandError, match="already exists"):
            sandbox.run('minds stage --name robin --task "test" --from-branch main')


# =============================================================================
# Directory Structure Tests
# =============================================================================


class TestDirectoryStructure:
    """Test that correct directory structure is created."""

    def test_creates_at_root_level(self, sandbox: Sandbox):
        """Creates mind folder at root level of minds directory."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert (sandbox.ctx.paths.user.minds_dir / "robin").is_dir()

    def test_creates_work_directory(self, sandbox: Sandbox):
        """Creates work/ directory."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert (sandbox.ctx.paths.user.minds_dir / "robin" / "work").is_dir()

    def test_creates_home_directory(self, sandbox: Sandbox):
        """Creates home/ directory."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert (sandbox.ctx.paths.user.minds_dir / "robin" / "home").is_dir()

    def test_creates_work_docs_directory(self, sandbox: Sandbox):
        """Creates work/docs/ directory."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert (sandbox.ctx.paths.user.minds_dir / "robin" / "work" / "docs").is_dir()

    def test_creates_welcome_md(self, sandbox: Sandbox):
        """Creates work/welcome.md template."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        path = sandbox.ctx.paths.user.minds_dir / "robin" / "work" / "welcome.md"
        assert path.is_file()
        content = path.read_text()
        assert "Task Assignment" in content

    def test_creates_immediate_plan_md(self, sandbox: Sandbox):
        """Creates work/immediate-plan.md template."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        path = sandbox.ctx.paths.user.minds_dir / "robin" / "work" / "immediate-plan.md"
        assert path.is_file()

    def test_creates_long_term_vision_md(self, sandbox: Sandbox):
        """Creates work/long-term-vision.md template."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        path = sandbox.ctx.paths.user.minds_dir / "robin" / "work" / "long-term-vision.md"
        assert path.is_file()

    def test_creates_my_process_md(self, sandbox: Sandbox):
        """Creates work/my-process.md template."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        path = sandbox.ctx.paths.user.minds_dir / "robin" / "work" / "my-process.md"
        assert path.is_file()

    def test_creates_scratchpad_md(self, sandbox: Sandbox):
        """Creates work/scratchpad.md template."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        path = sandbox.ctx.paths.user.minds_dir / "robin" / "work" / "scratchpad.md"
        assert path.is_file()

    def test_creates_references_toml(self, sandbox: Sandbox):
        """Creates references.toml at root level."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        path = sandbox.ctx.paths.user.minds_dir / "robin" / "references.toml"
        assert path.is_file()
        content = path.read_text()
        assert "references" in content.lower()


# =============================================================================
# Output Tests
# =============================================================================


class TestOutput:
    """Test command output."""

    def test_outputs_mind_name(self, sandbox: Sandbox, capsys):
        """Output includes the mind name."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        output = capsys.readouterr().out
        assert "robin" in output

    def test_outputs_welcome_edit_instruction(self, sandbox: Sandbox, capsys):
        """Output instructs to edit welcome.md."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        output = capsys.readouterr().out
        assert "welcome.md" in output.lower()

    def test_outputs_role_instruction(self, sandbox: Sandbox, capsys):
        """Output includes role assignment instruction."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        output = capsys.readouterr().out
        assert "role" in output.lower()
        assert "references.toml" in output

    def test_outputs_start_command(self, sandbox: Sandbox, capsys):
        """Output includes the start command."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        output = capsys.readouterr().out
        assert "mg start robin" in output


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_creates_minds_dir_if_not_exists(self, sandbox: Sandbox):
        """Creates minds/ directory if it doesn't exist."""
        assert not sandbox.ctx.paths.user.minds_dir.exists()
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert sandbox.ctx.paths.user.minds_dir.exists()
        assert (sandbox.ctx.paths.user.minds_dir / "robin").is_dir()

    def test_name_validation_lowercase(self, sandbox: Sandbox):
        """Name must be lowercase."""
        with pytest.raises(CommandError, match="lowercase"):
            sandbox.run('minds stage --name Robin --task "test" --from-branch main')

    def test_name_validation_no_underscore_start(self, sandbox: Sandbox):
        """Name cannot start with underscore."""
        with pytest.raises(CommandError, match="underscore"):
            sandbox.run('minds stage --name _robin --task "test" --from-branch main')



# =============================================================================
# Worktree Creation Tests
# =============================================================================


class TestWorktreeCreation:
    """Test worktree creation."""

    def test_creates_mind_and_worktree(self, sandbox: Sandbox):
        """Creates both mind and worktree."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert (sandbox.ctx.paths.user.minds_dir / "robin").is_dir()
        assert (sandbox.ctx.paths.root / "worktrees" / "robin").is_dir()

    def test_welcome_has_location(self, sandbox: Sandbox):
        """welcome.md has location populated."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        path = sandbox.ctx.paths.user.minds_dir / "robin" / "work" / "welcome.md"
        content = path.read_text()
        assert "**Location:** `worktrees/robin/`" in content

    def test_rejects_existing_nonempty_worktree_dir(self, sandbox: Sandbox):
        """Error when worktree directory exists and is not empty."""
        worktree_dir = sandbox.ctx.paths.root / "worktrees" / "robin"
        worktree_dir.mkdir(parents=True)
        (worktree_dir / "some-file.txt").write_text("content")

        with pytest.raises(CommandError, match="already exists and is not empty"):
            sandbox.run('minds stage --name robin --task "test" --from-branch main --allow-dirty')

    def test_outputs_worktree_location(self, sandbox: Sandbox, capsys):
        """Output includes worktree location."""
        sandbox.run('minds stage --name robin --task "test" --from-branch main')
        output = capsys.readouterr().out
        assert "worktrees/robin/" in output


# =============================================================================
# Mind Reuse Tests
# =============================================================================


class TestMindReuse:
    """Test reusing available minds without active sessions."""

    def test_reuses_mind_without_session(self, sandbox: Sandbox, capsys):
        """Reuses existing mind that has no active session."""
        minds_dir = sandbox.ctx.paths.user.minds_dir
        (minds_dir / "robin" / "work").mkdir(parents=True)
        (minds_dir / "robin" / "home").mkdir(parents=True)
        (minds_dir / "robin" / "references.toml").write_text("")

        sandbox.run('minds stage --task "test" --from-branch main --allow-dirty')
        output = capsys.readouterr().out

        assert "robin" in output
        mind_dirs = [d for d in minds_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        assert len(mind_dirs) == 1
        assert mind_dirs[0].name == "robin"

    def test_creates_new_when_all_minds_have_sessions(self, sandbox: Sandbox):
        """Creates new mind when all existing minds have active sessions."""
        from mg.helpers.sessions import create_session

        minds_dir = sandbox.ctx.paths.user.minds_dir
        (minds_dir / "robin" / "work").mkdir(parents=True)
        (minds_dir / "robin" / "home").mkdir(parents=True)
        (minds_dir / "robin" / "references.toml").write_text("")

        sessions_file = sandbox.ctx.paths.user.sessions_file
        create_session(sessions_file, "test task", "robin")

        with patch("mg.helpers.minds.subprocess.run") as mock_run:
            mock_run.return_value.stdout = "sparrow\n"
            mock_run.return_value.returncode = 0
            sandbox.run('minds stage --task "test" --from-branch main')

        assert (minds_dir / "sparrow").is_dir()

    def test_reuses_random_from_multiple_available(self, sandbox: Sandbox):
        """Picks randomly from multiple available minds."""
        import random

        minds_dir = sandbox.ctx.paths.user.minds_dir
        for name in ["alpha", "beta", "gamma"]:
            (minds_dir / name / "work").mkdir(parents=True)
            (minds_dir / name / "home").mkdir(parents=True)
            (minds_dir / name / "references.toml").write_text("")

        random.seed(42)
        sandbox.run('minds stage --task "test" --from-branch main --allow-dirty')

        mind_dirs = [d for d in minds_dir.iterdir() if d.is_dir() and not d.name.startswith("_")]
        assert set(d.name for d in mind_dirs) == {"alpha", "beta", "gamma"}

    def test_skips_minds_with_sessions(self, sandbox: Sandbox, capsys):
        """Only considers minds without sessions for reuse."""
        from mg.helpers.sessions import create_session

        minds_dir = sandbox.ctx.paths.user.minds_dir

        for name in ["busy", "idle"]:
            (minds_dir / name / "work").mkdir(parents=True)
            (minds_dir / name / "home").mkdir(parents=True)
            (minds_dir / name / "references.toml").write_text("")

        sessions_file = sandbox.ctx.paths.user.sessions_file
        create_session(sessions_file, "working on stuff", "busy")

        sandbox.run('minds stage --task "test" --from-branch main --allow-dirty')
        output = capsys.readouterr().out

        assert "idle" in output
        assert "busy" not in output


# =============================================================================
# Session Tests
# =============================================================================


class TestSessionCreation:
    """Test session lifecycle during staging."""

    def test_task_flag_required(self, sandbox: Sandbox):
        """Error when --task not provided."""
        with pytest.raises(CommandError, match="--task is required"):
            sandbox.run("minds stage --name robin")

    def test_creates_session_with_staged_status(self, sandbox: Sandbox):
        """Session is created with status 'staged'."""
        sandbox.run('minds stage --name robin --task "build feature" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert len(sessions) == 1
        assert sessions[0].status == "staged"

    def test_session_has_task(self, sandbox: Sandbox):
        """Session stores the --task value."""
        sandbox.run('minds stage --name robin --task "build feature" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].task == "build feature"

    def test_session_has_mind(self, sandbox: Sandbox):
        """Session is linked to the mind."""
        sandbox.run('minds stage --name robin --task "build feature" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].mind == "robin"

    def test_session_has_branch(self, sandbox: Sandbox):
        """Session records the mind's branch."""
        sandbox.run('minds stage --name robin --task "build feature" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].branch == "robin"

    def test_session_has_base_branch(self, sandbox: Sandbox):
        """Session records the base branch."""
        sandbox.run('minds stage --name robin --task "build feature" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].base_branch == "main"

    def test_session_has_description(self, sandbox: Sandbox):
        """Session stores --description when provided."""
        sandbox.run(
            'minds stage --name robin --task "build feature" --from-branch main'
            ' --description "Detailed requirements here"'
        )
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].description == "Detailed requirements here"

    def test_session_description_empty_by_default(self, sandbox: Sandbox):
        """Session description is empty when --description not provided."""
        sandbox.run('minds stage --name robin --task "build feature" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].description == ""

    def test_session_parent_from_env(self, sandbox: Sandbox):
        """Session parent is set from MG_SESSION env var."""
        with patch.dict("os.environ", {"MG_SESSION": "parent-session-123"}):
            sandbox.run('minds stage --name robin --task "sub-task" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].parent == "parent-session-123"

    def test_session_parent_empty_without_env(self, sandbox: Sandbox):
        """Session parent is empty when MG_SESSION not set."""
        with patch.dict("os.environ", {}, clear=True):
            sandbox.run('minds stage --name robin --task "root task" --from-branch main')
        sessions = load_sessions(sandbox.ctx.paths.user.sessions_file)
        assert sessions[0].parent == ""

    def test_output_includes_session_id(self, sandbox: Sandbox, capsys):
        """Output shows the session short_id."""
        sandbox.run('minds stage --name robin --task "build feature" --from-branch main')
        output = capsys.readouterr().out
        assert "staged" in output


# =============================================================================
# Base Branch Detection Tests
# =============================================================================


class TestBaseBranchDetection:
    """Test auto-detection of base branch from parent session."""

    def test_errors_without_mg_session(self, sandbox: Sandbox):
        """Errors when MG_SESSION is not set and --from-branch not provided."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(CommandError, match="MG_SESSION is not set"):
                sandbox.run('minds stage --name robin --task "test"')

    def test_uses_parent_session_branch(self, sandbox: Sandbox):
        """Uses parent session's branch as base branch."""
        from mg.helpers.sessions import create_session

        # Create a "wren" branch so git worktree can use it as base
        git = Git(sandbox.ctx.paths.root, quiet=True)
        git.run("branch wren")

        sessions_file = sandbox.ctx.paths.user.sessions_file
        parent = create_session(
            sessions_file, "parent task", "wren",
            branch="wren", base_branch="main",
        )

        with patch.dict("os.environ", {"MG_SESSION": parent.id}):
            sandbox.run('minds stage --name robin --task "test"')

        sessions = load_sessions(sessions_file)
        robin_session = [s for s in sessions if s.mind == "robin"][0]
        assert robin_session.base_branch == "wren"

    def test_falls_back_to_default_when_parent_has_no_branch(self, sandbox: Sandbox):
        """Falls back to default_branch when parent session has no branch."""
        from mg.helpers.sessions import create_session

        sessions_file = sandbox.ctx.paths.user.sessions_file
        parent = create_session(sessions_file, "parent task", "wren")

        with patch.dict("os.environ", {"MG_SESSION": parent.id}):
            sandbox.run('minds stage --name robin --task "test" --allow-dirty')

        sessions = load_sessions(sessions_file)
        robin_session = [s for s in sessions if s.mind == "robin"][0]
        assert robin_session.base_branch == "main"

    def test_from_branch_overrides_parent(self, sandbox: Sandbox):
        """--from-branch takes priority over parent session's branch."""
        from mg.helpers.sessions import create_session

        # Create branches so git worktree can reference them
        git = Git(sandbox.ctx.paths.root, quiet=True)
        git.run("branch wren")

        sessions_file = sandbox.ctx.paths.user.sessions_file
        parent = create_session(
            sessions_file, "parent task", "wren",
            branch="wren", base_branch="main",
        )

        # --from-branch main should override the parent's branch (wren)
        with patch.dict("os.environ", {"MG_SESSION": parent.id}):
            sandbox.run('minds stage --name robin --task "test" --from-branch main --allow-dirty')

        sessions = load_sessions(sessions_file)
        robin_session = [s for s in sessions if s.mind == "robin"][0]
        assert robin_session.base_branch == "main"


# =============================================================================
# Clean Working Tree Tests
# =============================================================================


class TestCleanWorkingTree:
    """Test that staging refuses to run with uncommitted changes."""

    def _worktree_output(self, root):
        """Build mock worktree list output pointing main at the sandbox root."""
        return (
            f"worktree {root}\n"
            f"HEAD 264bca4d3a8ef1b31bc266ecda47626bc3d1a937\n"
            f"branch refs/heads/main\n"
            f"\n"
        )

    def test_rejects_unstaged_changes(self, sandbox: Sandbox):
        """Refuses to stage when base branch has unstaged modifications."""
        root = sandbox.ctx.paths.root
        (root / "README.md").write_text("modified\n")

        output = self._worktree_output(root)
        with patch.object(Git, "run", _intercept_worktree_list(output)):
            with pytest.raises(CommandError, match="uncommitted changes"):
                sandbox.run('minds stage --name robin --task "test" --from-branch main')

    def test_rejects_staged_changes(self, sandbox: Sandbox):
        """Refuses to stage when base branch has staged changes."""
        root = sandbox.ctx.paths.root
        git = Git(root, quiet=True)
        (root / "README.md").write_text("modified\n")
        git.run("add README.md")

        output = self._worktree_output(root)
        with patch.object(Git, "run", _intercept_worktree_list(output)):
            with pytest.raises(CommandError, match="uncommitted changes"):
                sandbox.run('minds stage --name robin --task "test" --from-branch main')

    def test_rejects_untracked_files(self, sandbox: Sandbox):
        """Untracked files also count as dirty."""
        root = sandbox.ctx.paths.root
        (root / "new_file.txt").write_text("new\n")

        output = self._worktree_output(root)
        with patch.object(Git, "run", _intercept_worktree_list(output)):
            with pytest.raises(CommandError, match="uncommitted changes"):
                sandbox.run('minds stage --name robin --task "test" --from-branch main')

    def test_skips_check_when_branch_not_checked_out(self, sandbox: Sandbox):
        """Skips check when base branch has no worktree (not checked out)."""
        root = sandbox.ctx.paths.root
        # Dirty the tree, but mock worktree list to show a different branch
        (root / "README.md").write_text("modified\n")

        output = (
            f"worktree {root}\n"
            f"HEAD 264bca4d3a8ef1b31bc266ecda47626bc3d1a937\n"
            f"branch refs/heads/other-branch\n"
            f"\n"
        )
        with patch.object(Git, "run", _intercept_worktree_list(output)):
            sandbox.run('minds stage --name robin --task "test" --from-branch main')
        assert (sandbox.ctx.paths.user.minds_dir / "robin").is_dir()

