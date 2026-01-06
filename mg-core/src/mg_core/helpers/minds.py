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

import tomllib
import tomli_w
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


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
class MindPaths:
    """Paths for a mind's directory structure."""

    root: Path

    @property
    def startup(self) -> Path:
        """Path to the startup/ directory."""
        return self.root / "startup"

    @property
    def docs(self) -> Path:
        """Path to the docs/ directory."""
        return self.root / "docs"

    @property
    def references_file(self) -> Path:
        """Path to references.toml."""
        return self.startup / "references.toml"

    @property
    def sessions_file(self) -> Path:
        """Path to sessions.ig.toml (ignored by git)."""
        return self.root / "sessions.ig.toml"


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
        if not self.paths.startup.exists():
            issue = MindStructureIssue(
                path=self.paths.startup,
                message="Missing startup/ directory",
            )
            if fix:
                self.paths.startup.mkdir(parents=True)
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
                self.paths.startup.mkdir(parents=True, exist_ok=True)
                self.paths.references_file.write_text("# External document references\n")
                issue.fixed = True
            issues.append(issue)

        # Check docs/ directory
        if not self.paths.docs.exists():
            issue = MindStructureIssue(
                path=self.paths.docs,
                message="Missing docs/ directory",
            )
            if fix:
                self.paths.docs.mkdir(parents=True)
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
        if not self.paths.startup.exists():
            return []

        files = []
        for item in sorted(self.paths.startup.iterdir()):
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


# --- Session Management ---

MAX_SESSIONS = 20


@dataclass
class Session:
    """A tracked Claude session for a mind."""

    id: str
    task: str
    started: datetime


def load_sessions(sessions_file: Path) -> list[Session]:
    """Load sessions from TOML file.

    Returns sessions ordered most-recent-first.
    """
    if not sessions_file.exists():
        return []

    with open(sessions_file, "rb") as f:
        data = tomllib.load(f)

    sessions = []
    for entry in data.get("sessions", []):
        sessions.append(
            Session(
                id=entry["id"],
                task=entry["task"],
                started=entry["started"],
            )
        )
    return sessions


def save_session(sessions_file: Path, session: Session) -> None:
    """Prepend a new session to the file (most recent first).

    Keeps at most MAX_SESSIONS entries, dropping oldest.
    """
    existing = load_sessions(sessions_file)
    all_sessions = [session] + existing

    # Keep only the most recent MAX_SESSIONS
    all_sessions = all_sessions[:MAX_SESSIONS]

    data = {
        "sessions": [
            {"id": s.id, "task": s.task, "started": s.started}
            for s in all_sessions
        ]
    }

    with open(sessions_file, "wb") as f:
        tomli_w.dump(data, f)


def get_most_recent_session(sessions_file: Path) -> Session | None:
    """Get the most recently started session."""
    sessions = load_sessions(sessions_file)
    return sessions[0] if sessions else None


def find_session(sessions_file: Path, session_id: str) -> Session | None:
    """Find session by ID (supports partial matching)."""
    sessions = load_sessions(sessions_file)
    for session in sessions:
        if session.id.startswith(session_id):
            return session
    return None
