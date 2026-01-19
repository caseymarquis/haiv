"""Mind resolution and helpers.

Minds are long-running agents with persistent state. Each mind has a folder
in users/{user}/state/minds/ containing startup context and documents.

Directory structure:
    minds/
    ├── wren/                    # Mind name = folder name
    │   ├── startup/             # Loaded on wake
    │   │   ├── references.toml  # External doc references
    │   │   ├── identity.md      # Who this mind is
    │   │   └── current-focus.md # Active tasks
    │   └── docs/                # Mind-specific documents
    ├── _new/                    # Organizational dirs start with _
    │   └── reed/
    └── _archived/
        └── old-worker/

Mind names cannot start with underscore. Directories starting with _ are
organizational and can contain minds.
"""

from __future__ import annotations

import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from mg.paths import MindPaths

if TYPE_CHECKING:
    from mg.templates import TemplateRenderer


# Valid name pattern: starts with letter, then alphanumeric/hyphen/underscore
_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]*$")


class MindNotFoundError(Exception):
    """Raised when a mind cannot be found."""

    def __init__(self, name: str, available: list[str]):
        self.name = name
        self.available = available
        if available:
            available_str = ", ".join(sorted(available))
            super().__init__(
                f"Mind '{name}' not found.\n"
                f"Available minds: {available_str}"
            )
        else:
            super().__init__(
                f"Mind '{name}' not found in minds/ or any organizational subdirectory."
            )


class DuplicateMindError(Exception):
    """Raised when duplicate mind names exist."""

    def __init__(self, name: str, locations: list[Path]):
        self.name = name
        self.locations = locations
        locations_str = "\n".join(f"  - {loc}" for loc in locations)
        super().__init__(
            f"Duplicate mind '{name}' found in multiple locations:\n{locations_str}\n"
            f"Each mind name must be unique across all directories."
        )


@dataclass
class MindStructureIssue:
    """An issue found during mind structure validation."""

    path: Path
    message: str
    fixed: bool = False


@dataclass
class Mind:
    """A resolved mind with its paths and metadata."""

    paths: MindPaths

    @property
    def name(self) -> str:
        """The mind's name (derived from folder name)."""
        return self.paths.root.name

    def ensure_structure(self, *, fix: bool = True) -> list[MindStructureIssue]:
        """Ensure the mind has valid structure, optionally fixing issues.

        Checks for:
        - startup/ directory exists
        - startup/references.toml exists
        - docs/ directory exists

        Args:
            fix: If True, create missing directories/files.

        Returns:
            List of issues found (and whether they were fixed).
        """
        issues: list[MindStructureIssue] = []

        # Check startup/ directory
        if not self.paths.startup_dir.exists():
            issue = MindStructureIssue(
                path=self.paths.startup_dir,
                message="Missing startup/ directory",
            )
            if fix:
                self.paths.startup_dir.mkdir(parents=True)
                issue.fixed = True
            issues.append(issue)

        # Check startup/references.toml
        if not self.paths.references_file.exists():
            issue = MindStructureIssue(
                path=self.paths.references_file,
                message="Missing startup/references.toml",
            )
            if fix:
                # Ensure parent exists first
                self.paths.startup_dir.mkdir(parents=True, exist_ok=True)
                self.paths.references_file.write_text("# External document references\n")
                issue.fixed = True
            issues.append(issue)

        # Check docs/ directory
        if not self.paths.docs_dir.exists():
            issue = MindStructureIssue(
                path=self.paths.docs_dir,
                message="Missing docs/ directory",
            )
            if fix:
                self.paths.docs_dir.mkdir(parents=True)
                issue.fixed = True
            issues.append(issue)

        return issues

    def get_references(self) -> list[str]:
        """Get paths from references.toml.

        Returns list of path strings (relative to mg root).
        """
        if not self.paths.references_file.exists():
            return []

        with open(self.paths.references_file, "rb") as f:
            data = tomllib.load(f)

        refs = []
        for ref in data.get("references", []):
            path = ref.get("path")
            if path:
                refs.append(path)

        return refs

    def get_startup_files(self) -> list[Path]:
        """Get all files in startup/ except references.toml.

        Returns absolute paths sorted by name.
        """
        if not self.paths.startup_dir.exists():
            return []

        files = []
        for item in sorted(self.paths.startup_dir.iterdir()):
            if item.is_file() and item.name != "references.toml":
                files.append(item)
        return files


def list_mind_paths(minds_dir: Path) -> list[tuple[str, Path]]:
    """List all valid mind directories as (name, path) tuples.

    A valid mind directory:
    - Does not start with underscore
    - Parent is either minds_dir itself OR parent starts with underscore

    Args:
        minds_dir: Path to the minds/ directory.

    Returns:
        List of (name, path) tuples sorted by name.

    Raises:
        DuplicateMindError: If same name exists in multiple locations.
    """
    if not minds_dir.exists():
        return []

    # Collect all candidate directories
    results: list[tuple[str, Path]] = []

    for item in minds_dir.iterdir():
        if not item.is_dir():
            continue

        if item.name.startswith("_"):
            # Organizational directory - check children
            for subitem in item.iterdir():
                if subitem.is_dir() and not subitem.name.startswith("_"):
                    results.append((subitem.name, subitem))
        else:
            # Top-level mind
            results.append((item.name, item))

    # Check for duplicates
    seen: dict[str, list[Path]] = {}
    for name, path in results:
        if name not in seen:
            seen[name] = []
        seen[name].append(path)

    for name, paths in seen.items():
        if len(paths) > 1:
            raise DuplicateMindError(name, paths)

    return sorted(results, key=lambda x: x[0])


def resolve_mind(name: str, minds_dir: Path) -> Mind:
    """Resolve a mind name to a Mind object.

    Args:
        name: The mind name to resolve.
        minds_dir: Path to the minds/ directory.

    Returns:
        Mind object with resolved paths.

    Raises:
        MindNotFoundError: If mind not found.
        DuplicateMindError: If duplicate names exist.
    """
    all_minds = list_mind_paths(minds_dir)
    available = [n for n, _ in all_minds]

    for mind_name, mind_path in all_minds:
        if mind_name == name:
            return Mind(paths=MindPaths(root=mind_path))

    raise MindNotFoundError(name, available)


def list_minds(minds_dir: Path) -> list[Mind]:
    """List all minds in the minds directory.

    Returns:
        List of Mind objects sorted by name.

    Raises:
        DuplicateMindError: If duplicate names exist.
    """
    return [Mind(paths=MindPaths(root=path)) for _, path in list_mind_paths(minds_dir)]


# --- Mind Creation ---


class MindExistsError(Exception):
    """Raised when trying to create a mind that already exists."""

    def __init__(self, name: str):
        self.name = name
        super().__init__(f"Mind '{name}' already exists")


class InvalidMindNameError(Exception):
    """Raised when a mind name is invalid."""

    def __init__(self, name: str, reason: str):
        self.name = name
        self.reason = reason
        super().__init__(f"Invalid mind name '{name}': {reason}")


def validate_mind_name(name: str) -> None:
    """Validate that a mind name is valid.

    Args:
        name: The name to validate.

    Raises:
        InvalidMindNameError: If the name is invalid.
    """
    if not name:
        raise InvalidMindNameError(name, "Name cannot be empty")

    if name != name.lower():
        raise InvalidMindNameError(name, "Name must be lowercase")

    if name.startswith("_"):
        raise InvalidMindNameError(
            name, "Name cannot start with underscore (reserved for organizational directories)"
        )

    if not name[0].isalpha():
        raise InvalidMindNameError(name, "Name must start with a letter")

    if not _NAME_PATTERN.match(name):
        raise InvalidMindNameError(name, "Name must be alphanumeric with hyphens/underscores only")


def generate_mind_name(existing: list[str]) -> str:
    """Generate a unique mind name using Claude.

    Args:
        existing: List of existing mind names to avoid.

    Returns:
        A short, memorable, lowercase name not in existing.

    Raises:
        RuntimeError: If name generation fails.
    """
    if existing:
        avoid_clause = f" Do not use: {', '.join(existing)}."
    else:
        avoid_clause = ""

    system_prompt = (
        "You generate names for AI assistants. "
        "Output a single short, memorable, lowercase name (like wren, sage, spark). "
        "Output only the name, nothing else."
    )
    user_prompt = f"Generate a name.{avoid_clause}"

    result = subprocess.run(
        [
            "claude", "-p",
            "--model", "haiku",
            "--system-prompt", system_prompt,
            user_prompt,
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to generate name: {result.stderr}")

    return result.stdout.strip()


def mind_exists(name: str, minds_dir: Path) -> bool:
    """Check if a mind with the given name already exists.

    Args:
        name: The mind name to check.
        minds_dir: Path to the minds/ directory.

    Returns:
        True if the mind exists, False otherwise.
    """
    if not minds_dir.exists():
        return False

    existing = [n for n, _ in list_mind_paths(minds_dir)]
    return name in existing


def scaffold_mind(
    name: str,
    minds_dir: Path,
    templates: TemplateRenderer,
    *,
    location: str | None = None,
) -> Mind:
    """Create a new mind folder with proper structure.

    Creates in _new/ organizational directory with:
    - startup/welcome.md (template for creator to fill in)
    - startup/immediate-plan.md
    - startup/long-term-vision.md
    - startup/my-process.md
    - startup/scratchpad.md
    - startup/references.toml
    - docs/

    Args:
        name: The mind name (must be validated first).
        minds_dir: Path to the minds/ directory.
        templates: TemplateRenderer for writing template files.
        location: Optional worktree location (e.g., "worktrees/feature-x/").

    Returns:
        The created Mind object.

    Raises:
        MindExistsError: If a mind with this name already exists.
    """
    if mind_exists(name, minds_dir):
        raise MindExistsError(name)

    # Create in _new/ organizational directory
    mind_root = minds_dir / "_new" / name
    paths = MindPaths(root=mind_root)

    # Create directories
    paths.startup_dir.mkdir(parents=True)
    paths.docs_dir.mkdir(parents=True)

    # Write template files
    templates.write("minds/welcome.md.j2", paths.welcome_file, location=location or "")
    templates.write("minds/references.toml.j2", paths.references_file)
    paths.immediate_plan_file.write_text("# Immediate Plan\n")
    paths.long_term_vision_file.write_text("# Long-Term Vision\n")
    paths.my_process_file.write_text("# My Process\n")
    paths.scratchpad_file.write_text("# Scratchpad\n")

    return Mind(paths=paths)
