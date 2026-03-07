"""Mind resolution and helpers.

Minds are long-running agents with persistent state. Each mind has a folder
in users/{user}/state/minds/ containing work context and personal files.

Directory structure:
    minds/
    ├── wren/                    # Mind name = folder name
    │   ├── work/                # Assignment docs (cleared between assignments)
    │   │   ├── welcome.md       # [loaded on wake] Task assignment
    │   │   ├── immediate-plan.md  # [loaded on wake]
    │   │   ├── scratchpad.md    # [loaded on wake]
    │   │   └── docs/            # Not auto-loaded
    │   ├── home/                # Personal continuity (persists)
    │   │   └── journal.md       # [loaded on wake]
    │   └── references.toml      # [loaded on wake] External doc refs
    └── _staging/                # Organizational dirs start with _
        └── old-worker/

On wake, the mind receives: external docs from references.toml, plus all
top-level files in work/ and home/ (subdirectories are not auto-loaded).

Mind names cannot start with underscore. Directories starting with _ are
organizational and can contain minds.
"""

from __future__ import annotations

import os
import re
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from haiv.paths import MindPaths

if TYPE_CHECKING:
    from haiv.templates import TemplateRenderer


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
        - work/ directory exists
        - home/ directory exists
        - references.toml exists (at root)
        - work/docs/ directory exists

        Args:
            fix: If True, create missing directories/files.

        Returns:
            List of issues found (and whether they were fixed).
        """
        issues: list[MindStructureIssue] = []

        # Check work/ directory
        if not self.paths.work.root.exists():
            issue = MindStructureIssue(
                path=self.paths.work.root,
                message="Missing work/ directory",
            )
            if fix:
                self.paths.work.root.mkdir(parents=True)
                issue.fixed = True
            issues.append(issue)

        # Check home/ directory
        if not self.paths.home.root.exists():
            issue = MindStructureIssue(
                path=self.paths.home.root,
                message="Missing home/ directory",
            )
            if fix:
                self.paths.home.root.mkdir(parents=True)
                issue.fixed = True
            issues.append(issue)

        # Check references.toml at root
        if not self.paths.references_file.exists():
            issue = MindStructureIssue(
                path=self.paths.references_file,
                message="Missing references.toml",
            )
            if fix:
                self.paths.references_file.write_text("# External document references\n", encoding="utf-8")
                issue.fixed = True
            issues.append(issue)

        # Check work/docs/ directory
        if not self.paths.work.docs_dir.exists():
            issue = MindStructureIssue(
                path=self.paths.work.docs_dir,
                message="Missing work/docs/ directory",
            )
            if fix:
                self.paths.work.docs_dir.mkdir(parents=True)
                issue.fixed = True
            issues.append(issue)

        return issues

    def get_references(self) -> list[str]:
        """Get paths from references.toml.

        Returns list of path strings (relative to haiv root).
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
        """Get all files to load on wake.

        Returns absolute paths for:
        - External docs from references.toml (resolved to absolute paths)
        - Top-level files in work/
        - Top-level files in home/

        Raises:
            RuntimeError: If hv_root not set and references.toml has entries.
        """
        files: list[Path] = []

        # Add resolved reference paths first
        for ref_path in self.get_references():
            if self.paths.hv_root is None:
                raise RuntimeError(
                    f"Cannot resolve reference path '{ref_path}': hv_root not set on MindPaths"
                )
            files.append(self.paths.hv_root / ref_path)

        # Add top-level files from work/
        if self.paths.work.root.exists():
            for item in self.paths.work.root.iterdir():
                if item.is_file():
                    files.append(item)

        # Add top-level files from home/
        if self.paths.home.root.exists():
            for item in self.paths.home.root.iterdir():
                if item.is_file():
                    files.append(item)

        return sorted(files, key=lambda p: p.name)


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


def resolve_mind(name: str, minds_dir: Path, hv_root: Path) -> Mind:
    """Resolve a mind name to a Mind object.

    Args:
        name: The mind name to resolve.
        minds_dir: Path to the minds/ directory.
        hv_root: The haiv project root (needed to resolve references.toml paths).

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
            return Mind(paths=MindPaths(root=mind_path, hv_root=hv_root))

    raise MindNotFoundError(name, available)


def list_minds(minds_dir: Path, hv_root: Path) -> list[Mind]:
    """List all minds in the minds directory.

    Args:
        minds_dir: Path to the minds/ directory.
        hv_root: The haiv project root (needed to resolve references.toml paths).

    Returns:
        List of Mind objects sorted by name.

    Raises:
        DuplicateMindError: If duplicate names exist.
    """
    return [Mind(paths=MindPaths(root=path, hv_root=hv_root)) for _, path in list_mind_paths(minds_dir)]


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
        env={**os.environ, "DISABLE_PROMPT_CACHING": "1", "CLAUDECODE": ""},
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
    skip_existing: bool = False,
) -> Mind:
    """Create a new mind folder with proper structure.

    Creates at root level with:
    - work/welcome.md (template for creator to fill in)
    - work/immediate-plan.md
    - work/long-term-vision.md
    - work/my-process.md
    - work/scratchpad.md
    - work/docs/
    - home/
    - references.toml (at root)

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
    if not skip_existing and mind_exists(name, minds_dir):
        raise MindExistsError(name)

    # Create at root level
    mind_root = minds_dir / name
    paths = MindPaths(root=mind_root)

    # Create directories
    paths.work.root.mkdir(parents=True, exist_ok=True)
    paths.work.docs_dir.mkdir(parents=True, exist_ok=True)
    paths.home.root.mkdir(parents=True, exist_ok=True)

    # Write template files
    templates.write("minds/welcome.md.j2", paths.work.welcome_file, skip_existing=skip_existing, location=location or "")
    templates.write("minds/references.toml.j2", paths.references_file, skip_existing=skip_existing)

    def _write_if_missing(path: Path, content: str) -> None:
        if not skip_existing or not path.exists():
            path.write_text(content, encoding="utf-8")

    _write_if_missing(paths.work.immediate_plan_file, "# Immediate Plan\n")
    _write_if_missing(paths.work.long_term_vision_file, "# Long-Term Vision\n")
    _write_if_missing(paths.work.my_process_file, "# My Process\n")
    _write_if_missing(paths.work.scratchpad_file, "# Scratchpad\n")

    return Mind(paths=paths)
