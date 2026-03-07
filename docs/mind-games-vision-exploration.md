# Mind-Games Vision Exploration

**Status:** Phase 1.0 - Manual multi-Claude via tmux
**Date:** 2026-01-02

---

## Core Purpose

**Seamless management of a collaborative AI team, optimizing for the bottleneck constraint of expert-level human attention.**

Key principles:
- Build on top of Claude Code (state-of-the-art tooling). Encourage, incorporate, and simplify use of out-of-the-box functionality. Don't fight the current.
- Ensure user's personal infrastructure around Claude is immediately and easily scalable across multiple projects. No per-project setup friction.
- **Educate, don't obscure.** haiv wraps tools like git and Claude Code, but should never be a black box. Show users what's happening under the hood:
  - Print the underlying commands being run (e.g., `git worktree add ...`)
  - Explain what we're trying to accomplish and why
  - Empower users to understand and use the tools directly
  - This reduces long-term support costs and user frustration
  - Use `--quiet` or `--silent` flags for automation scenarios where verbosity isn't needed

**Note:** The CLI tool provides the `hv` command. Installation details TBD - goal is something as simple as `uv tool install haiv`.

---

## Critical Priorities

### Scale to Multiple People & Projects (ASAP)
- Currently single-user, single-project
- Needs to work across teams and codebases

### Commands as Packages
- Commands (dynamic prompt generators) must exist separate from the tool
- Standard Python packaging via pyproject.toml + uv
- Shareable, versioned, installable via git repos

### Parallel Execution Infrastructure

**Decision: tmux as foundation, manual-first approach.**

tmux provides process management; haiv provides state management. Start with manual multi-Claude workflows using existing tmux, automate incrementally as friction points emerge.

**Why tmux:**
- Battle-tested process isolation (sessions/windows/panes)
- Persistence across disconnections
- Programmatic control (`send-keys`, `capture-pane`) enables automation
- Works with Claude CLI directly, no integration needed
- One tmux server per user manages all sessions

**Architecture:**
```
tmux server (process management)
└── session: haiv-{project}              # one per haiv-managed repo
    ├── window: main                   # worktree: main
    ├── window: feature-auth           # worktree: feature-auth
    └── window: feature-api            # worktree: feature-api

state/ (file-based state management)
├── minds/                             # persistent memory per mind
├── artifacts/                         # completed work products
└── messages/                          # inter-mind communication
```

**Turn-based, not event-driven:**
- LLMs excel at "here's the situation, what now?" - not continuous monitoring
- Manager mind wakes on demand (`hv check`) or scheduled intervals
- Captures worker state, assesses, acts, returns to sleep
- Lower complexity, predictable costs, known to work

**Manual workflow (current):**
```bash
# Create worktree
git worktree add worktrees/feature-x -b feature-x main

# Start tmux session for project (or attach if exists)
tmux new-session -s haiv-myproject -c /path/to/haiv-hq

# Create window per worktree
tmux new-window -n feature-x -c worktrees/feature-x
claude   # start Claude in that window
```

**Automation targets (as friction emerges):**
- `hv worktree add` - simplify worktree + window creation
- `hv start` - launch mind with persistent memory loaded
- `hv status` - show state of all minds (attention queue)
- `hv check` - manager mind reviews workers

**Related tools (reference, not dependencies):**
- Claude Squad - demonstrates multi-agent TUI patterns
- tmux-mcp - demonstrates programmatic tmux control via MCP

---

## Directory Architecture

**Decision: haiv-hq as control plane at root, code worktrees as children**

Mind-games operates in its own clone of the repository. The root IS the haiv-hq orphan branch (the control plane). Code branches live in `worktrees/`. This structure means `cd some-project-hv` puts you immediately in the control plane with full context.

```
~/code/
├── some-project/                    # normal checkout (IDE, manual git, etc.)
│   ├── .git/
│   └── src/                         # no haiv artifacts here
│
└── some-project-hv/                 # IS haiv-hq (orphan branch) - the control plane
    ├── .git/                        # bare repository data
    ├── .claude/                     # Claude Code config for this project
    ├── CLAUDE.md                    # describes haiv system
    ├── src/haiv_project/              # project-level package
    ├── users/casey/state/minds/     # where minds live
    └── worktrees/
        ├── develop/                 # code branch (worktree folder = branch name)
        └── feature-auth/            # code branch
```

**Key principles:**
- `hv init` creates the `-hv` controlled repo alongside existing checkout, or initializes the current directory when not in a repo
- haiv-hq is the root - control plane where humans and AIs start
- Code worktrees are children in `worktrees/` - destinations for work
- Worktree folder name = branch name (hard assumption)
- State on orphan branch - no common history with code, never pollutes code branches
- Multiple minds can work in the same worktree (not mutually exclusive)

**Why haiv-hq at root:**
- Claude instances initialize with haiv context immediately available
- Hierarchy reflects reality: coordination above, work below
- No confusion about "which worktree has the config"

**Adoption:**
- Coexists with normal checkouts - same remote
- Code branches are clean - no haiv artifacts
- Work flows via push/pull to shared remote

---

## State Structure (haiv-hq branch)

haiv-hq IS the root of the haiv-controlled repo (the control plane). It uses **standard Python package layout** at both project and user levels. All assets live inside the module under `__assets__/` for automatic inclusion when packaged.

```
project-haiv/                          # IS haiv-hq (orphan branch) - the root
├── .git/                            # bare repository data
├── .claude/                         # Claude Code config
├── CLAUDE.md                        # describes haiv system for Claude instances
├── pyproject.toml                   # project-level package
├── .venv/                           # project-level venv (uv hardlinks)
├── specs/                           # custom project-level shared state
├── something-else/                  # custom project-level shared state
├── src/
│   └── haiv_project/                  # project module
│       ├── __init__.py
│       ├── __assets__/              # non-code assets (dunder = special)
│       │   ├── mind_templates/      # mind templates (convention)
│       │   ├── project_assets_a/    # whatever the project needs
│       │   └── project_assets_b/    # (subfolders are project-defined)
│       ├── commands/                # project commands
│       ├── resolvers/               # project resolvers
│       └── helpers/                 # shared utilities
├── tests/                           # project tests
├── users/
│   └── casey/
│       ├── identity.toml            # user identity matching config
│       ├── pyproject.toml           # user-level package
│       ├── .venv/                   # user-level venv (uv hardlinks)
│       ├── src/
│       │   └── haiv_user/             # user module
│       │       ├── __init__.py
│       │       ├── __assets__/      # non-code assets
│       │       │   ├── mind_templates/  # mind templates (convention)
│       │       │   ├── user_assets_a/   # whatever the user needs
│       │       │   └── user_assets_b/   # (subfolders are user-defined)
│       │       ├── commands/        # user commands
│       │       ├── resolvers/       # user resolvers
│       │       └── helpers/         # user utilities
│       ├── tests/                   # user tests
│       └── state/
│           ├── .gitignore           # user controls what syncs
│           ├── minds/               # instantiated minds
│           ├── messages/            # message state
│           └── plans/               # user plans (short/medium/long-term)
└── worktrees/                       # code branches live here
    ├── main/                        # code worktree
    └── feature-x/                   # code worktree
```

**Resolution order:** haiv_core → haiv_project → haiv_user (each level extends/overrides the previous)

**Everything inside the module:**
- commands/, resolvers/, helpers/ - Python code
- `__assets__/` - non-code assets, dunder signals "special". Packages may structure as they wish; tooling may have conventions (e.g., `mind_templates/`)
- Same structure for installed packages, project, and user
- Hatchling includes all files automatically, no config needed

**Why standard package layout:**
- Tests at every level (AI collaborators need tests to see the world)
- uv's hardlink cache makes per-venv isolation virtually free
- Consistent tooling (pytest, uv sync) works everywhere

**User identity (identity.toml):**

Each user folder contains an `identity.toml` that describes how to recognize that user:

```toml
# haiv-hq/users/casey/identity.toml
[match]
git_email = ["casey@example.com", "casey@work.com"]
git_name = ["Casey"]
system_user = ["casey", "caseym"]
```

When haiv runs, it scans all user folders, checks identity configs against the current environment, and uses the matching user's state. On first run (no match), haiv prompts for a folder name and creates identity.toml with current environment identifiers. On new machines, existing users just add their new machine's identifiers to their existing identity.toml.

**Key distinctions:**
- Root level = shared project definitions (all users see)
- `users/{name}/` = user-specific definitions + state
- `context/` = non-code knowledge (markdown, data files)
- `state/` = instantiated runtime data (minds, messages, plans)
- Everything in `src/` = Python code with consistent discovery

**User state and sync control:**

The `state/` directory contains frequently-modified data: minds, messages, and plans. A templated `.gitignore` lets users control what syncs between machines:

```gitignore
# state/.gitignore - uncomment lines to ignore

# Ignore all plans
# plans/

# Ignore plans marked as local-only (*.ig.md = "ignore")
*.ig.md

# Ignore all messages
# messages/
```

By default, plans sync via git (committed to haiv-hq). Users who prefer local-only plans can ignore the directory or use the `.ig.md` extension convention for specific files. This flexibility lets us learn from real usage before prescribing defaults.

**Planning (user-level):**

Plans live in `state/plans/`. The internal organization is intentionally unspecified - real usage will reveal what's needed. Scenarios to support:
- Plans shared across multiple minds
- Plans specific to a single mind
- Task-specific plans with limited lifespans
- Hierarchical plans (vision → milestones → tasks)

haiv's planning acts as a **layer over Claude's native planning**. Claude Code's plan mode is ephemeral (lives in conversation, local to one machine). haiv provides:
- Configurable guidelines (core → project → user resolution) that shape the planning process
- Redirection so plan output lands in controlled, organized locations
- Persistence via git for cross-machine sync
- Visibility across minds and sessions

Planning is scoped to `haiv_user` initially. Project-level shared plans may come later based on real needs.

---

## Core Scope

**The core `haiv` package enables: one human + their team of collaborative AI agents.**

This is an explicit boundary. Core does NOT design for:
- Real-time human-to-human coordination
- Multiple different humans collaborating simultaneously

Core DOES support:
- Same human across multiple machines (pause on laptop, resume on desktop - just like git)
- Human ↔ Mind communication (async)
- Mind ↔ Mind communication (async, same operator)

**When questions arise about multi-user real-time scaling:** That's out of scope for core. Optional packages can add infrastructure for team coordination when needed.

This keeps core simple, dependency-free, and focused.

---

## What haiv Is NOT

**haiv is not a Claude Code plugin.** Plugins load at startup and require restart to update. hv commands are dynamic - read and executed at runtime, hot-reloadable while Minds are running. For a long-running collaborative AI team, you can't restart every instance to deploy a fix.

**haiv is not a wrapper around Claude Code for single-agent simplicity.** That's just Claude Code - use it directly.

haiv is for **parallel collaborative AI**, which requires the worktree-first architecture to work. The constraints aren't arbitrary - they're inherent to the problem:
- Parallel agents need isolated workspaces
- Without isolation, agents step on each other
- Merge conflicts and debugging "who changed what" become nightmares
- The human attention bottleneck gets worse, not better

**If you don't need parallel agents:** Use Claude Code. No setup, no model to learn.

**If you want parallel collaborative AI:** Adopt haiv's model. The worktree-first architecture is what the problem requires.

No middle ground. No apologies for the constraints. Users self-select based on their needs.

---

## State & Modularity

**Project-first tool.** State lives on an orphan branch in the repo.

**Discovery mechanisms:**

Python code (commands, resolvers, helpers) uses entry points in pyproject.toml:

```toml
[project.entry-points."haiv.commands"]
core = "haiv_core.commands"

[project.entry-points."haiv.resolvers"]
core = "haiv_core.resolvers"
```

At runtime, haiv uses `importlib.metadata.entry_points()` to discover registered modules, then file-based routing within each module.

**File-based routing conventions:**

```
commands/
├── wake.py                 # hv wake
├── _mind_/                 # param "mind", uses mind resolver
│   ├── status.py           # hv forge status
│   └── messages/
│       └── _rest_.py       # rest param, captures remaining
                            # hv forge messages a/b → rest=["a","b"]
```

- `_name_/` - param "name", uses resolver "name" if exists, else string
- `_name_as_resolver_/` - param "name", explicit resolver
- `_rest_.py` - rest param, captures remaining path (always terminal, always a file)
- `__dunder__` - excluded from routing (e.g., `__assets__/`, `__pycache__/`)
- `--flag` - flags (double-dash only) terminate routing; single-dash args pass through

**Routing precedence:**

At each level, literals take precedence over params. This is evaluated level-by-level, not globally. The first literal match that leads to a valid route wins.

```
commands/
├── forge/              # literal "forge"
│   └── status.py
└── _mind_/             # param captures any value
    └── status.py
```

With `hv forge status`: literal `forge/` matches first, so we use `forge/status.py`.
With `hv specs status`: no literal `specs/`, so `_mind_/` captures it → `_mind_/status.py`.

This matches user expectations: if you type a literal command that exists, you meant it. Params are for variable data when no literal matches.

**Ambiguity errors:**

If multiple param directories at the same level could match and all lead to valid routes, routing raises `AmbiguousRouteError`:

```
commands/
├── _name_/greet.py     # Could match "alice greet"
└── _id_/greet.py       # Could also match "alice greet"
```

This is a structure error - the command author must disambiguate (e.g., use different leaf names, or consolidate to one param).

Non-code assets live in `__assets__/` inside the module, accessed via `ctx.paths.assets`.

**Core functionality via haiv-core:**
- `haiv-core` is bundled with the `hv` tool installation
- Contains base commands (init, clone, etc.), default mind templates
- "Core" is just another package - can be extended/overridden

**Progressive enhancement via packages:**
```
Core: disk persistence + git (good enough to start)
    ↓
Friction at scale? Add a package to pyproject.toml
    ↓
Package adds: MCP servers, databases, real-time coordination
```

Complexity is opt-in. Core stays clone-and-go.

---

## Testing Infrastructure (haiv.test)

**Philosophy:** Strongly encourage TDD. Each test helper requires progressively more implementation, letting users verify structure before logic.

**Import:** `from haiv import test`

### Level 1: routes_to() - Test Routing Only

```python
match = test.routes_to("alice greet --verbose", commands)
```

**File needs:** Just exist at the right path (can be empty)

**Returns object with:**
- `match.file` - file handle
- `match.params` - `{"name": "alice"}` (captured path params as strings)
- `match.rest` - `[]` (rest params as list of strings)
- `match.flags` - `["--verbose"]` (raw, unparsed flags)

**Optional expected path:**
```python
match = test.routes_to("alice greet", commands, expected="_name_/greet.py")
```

**Negative testing:**
```python
match = test.routes_to("nonexistent", commands, exists=False)
```

**Purpose:** Verify file structure is correct before writing any code.

### Level 2: parse() - Test Definition & Arg Parsing

```python
ctx = test.parse("alice greet --verbose", commands)
assert ctx.args.get_one("name") == "alice"
assert ctx.args.has("verbose")
```

**File needs:** `define()` function (but not `execute()`)

**Returns:** The `ctx` that would be passed to `execute()`

**Purpose:** Verify command definition and arg parsing before implementing logic.

### Level 3: execute() - Unit Test Command Logic

```python
result = test.execute("alice greet", commands)
# Use pytest's capsys fixture to capture output if needed
```

**File needs:** Both `define()` and `execute()`

**Returns:** `result.ctx` - the context (for inspecting state after execution)

**Key behavior:** Skips `setup()` and `teardown()` - see Safe-by-Default Testing below.

**Purpose:** Unit test command logic with explicit, controlled dependencies.

### Command Lifecycle

Commands have four functions. In production, `setup → execute → teardown` run sequentially.

```python
import os
from haiv import cmd

def define() -> cmd.Def:
    """Required. Command metadata and flag definitions."""
    return cmd.Def(description="Save something to the database")

def setup(ctx: cmd.Ctx) -> None:
    """Optional. Register real dependencies (database, APIs, etc.)

    SKIPPED IN TESTS - this is intentional for safety.
    """
    db_url = os.environ.get("DATABASE_URL")
    ctx.container.register(Database, PostgresDB, url=db_url)

def execute(ctx: cmd.Ctx) -> None:
    """Required. Run the command logic.

    Dependencies come from ctx.container - in tests, only
    explicitly registered mocks exist.
    """
    db = ctx.container.resolve(Database)
    db.save(something)

def teardown(ctx: cmd.Ctx) -> None:
    """Optional. Release resources (runs even if execute fails)."""
    pass
```

| Function | Required | Production | test.execute() |
|----------|----------|------------|----------------|
| `define()` | ✅ | ✅ Called | ✅ Called |
| `setup(ctx)` | ❌ | ✅ Called | ❌ **Skipped** |
| `execute(ctx)` | ✅ | ✅ Called | ✅ Called |
| `teardown(ctx)` | ❌ | ✅ Called | ❌ **Skipped** |

### Safe-by-Default Testing

**Why `setup()` is skipped in tests:**

`setup()` registers real dependencies - database connections, external APIs, file system access. By skipping it in tests:

- **Nothing real exists** - the container starts empty
- **Commands fail safely** - resolving an unregistered dependency errors immediately
- **Tests must be explicit** - to use a database, you must register a mock yourself

**Example: A command that drops a database**

```python
# In command's setup():
ctx.container.register(Database, PostgresDB, url=os.environ["DATABASE_URL"])

# In command's execute():
db = ctx.container.resolve(Database)
db.drop_all_tables()  # Dangerous!
```

In a naive test setup, you might accidentally run with real config and drop production data.

With our approach:
```python
def test_drop_tables():
    # setup() is skipped - no real database registered
    result = test.execute("db drop", commands)
    # ❌ Fails: Database not registered

def test_drop_tables_explicit():
    ctx = test.parse("db drop", commands)
    ctx.container.register(Database, FakeDatabase)  # Explicit mock
    # Now it works - and we know exactly what we're testing
```

**The inversion:** Instead of "mock what's dangerous," it's "nothing exists unless explicitly provided." You can't accidentally use real resources because they were never registered.

### Dependency Injection

`ctx.container` is a [punq](https://punq.readthedocs.io/) Container:

```python
# In test - register mocks explicitly
ctx = test.parse("save thing", commands)
ctx.container.register(Database, MockDatabase)
test.execute(...)  # execute() can now resolve Database
```

**Why punq:**
- Lightweight, no decorators required
- Uses type hints for auto-wiring
- Simple API: `register()`, `resolve()`, `resolve_all()`
- Supports abstract→concrete mapping and scopes

**Why DI matters for haiv:**
- Safe-by-default testing (see above)
- Cross-package coordination (Package A provides service, Package B mocks it)
- Explicit dependencies (visible in code, not hidden imports)
- Tests don't break when refactoring (no import path coupling)

### Future: Integration Testing

Additional test helpers will support integration testing with optional setup/teardown execution for tests that need the full lifecycle.

### Future: Environment Isolation

`sandbox=True` option for filesystem isolation:
```python
result = test.execute("init", commands, sandbox=True)
# Command runs in isolated temp directory
```

### Error Testing

Use standard pytest - no custom wrappers:

```python
with pytest.raises(RouteNotFoundError):
    test.execute("nonexistent", commands)
```

---

## Distribution & Package Management

**Core package architecture:**

Three foundational packages in a uv workspace monorepo (`haiv`):

```
haiv/              # monorepo root
├── haiv/                  # API for building commands
├── haiv-core/             # Core commands
├── haiv-cli/              # CLI entry point
└── pyproject.toml       # workspace config
```

| Package | Directory | Module | Purpose |
|---------|-----------|--------|---------|
| `haiv-cli` | `haiv-cli/` | `haiv_cli` | CLI entry point |
| `haiv-core` | `haiv-core/` | `haiv_core` | Core commands (init, etc.) |
| `haiv` | `haiv/` | `haiv` | Public API for command authors |

This separation means:
- `haiv` can be used by any package without pulling in CLI infrastructure
- `hv-core` is "just another package" - can be overridden/extended
- `haiv-cli` is minimal - just bootstrap and package loading
- Individual packages available via git subdirectory (installation details TBD)

**uv is the foundation:**
- Tool installation (details TBD, goal: `uv tool install haiv`)
- Python dependency resolution for commands
- Behind-the-scenes package management

**User experience:**
```bash
# Install (one-time, details TBD)
uv tool install haiv  # or similar

# CLI command is 'hv'
hv clone my-repo
```

**Python deps - standard packaging via uv:**

uv's hardlink cache makes per-venv isolation virtually free.

```
~/.local/share/uv/tools/haiv-cli/       # haiv tool itself (path TBD)

my-repo-haiv/                           # IS haiv-hq orphan branch
├── pyproject.toml                    # project-level deps
├── .venv/                            # project-level venv
├── src/haiv_project/                   # project context, commands, etc.
└── users/
    ├── casey/
    │   ├── pyproject.toml            # user-level deps
    │   ├── .venv/                    # user-level venv
    │   └── src/haiv_user/              # user context, commands, etc.
    └── rob/
        ├── pyproject.toml
        ├── .venv/
        └── src/haiv_user/
```

External haiv packages are Python dependencies using our file-structure conventions and referencing the `haiv/haiv` package.

**Benefits:**
- Standard Python packaging - no custom resolution
- uv hardlink cache means shared packages = shared disk space
- Project and user code have isolated dependency sets

### XDG Base Directory Specification

On Linux, haiv follows the [XDG Base Directory Specification](https://specifications.freedesktop.org/basedir-spec/latest/) for user-level files outside of project repos:

| Purpose | Environment Variable | Default |
|---------|---------------------|---------|
| Config | `$XDG_CONFIG_HOME` | `~/.config/haiv/` |
| Data | `$XDG_DATA_HOME` | `~/.local/share/haiv/` |
| Cache | `$XDG_CACHE_HOME` | `~/.cache/haiv/` |
| Logs/state | `$XDG_STATE_HOME` | `~/.local/state/haiv/` |

**TODO:** Audit code that writes to user directories for XDG compliance.

---

## Collaboration Model

**Worktree = local workspace**
- Multiple Minds can collaborate within one worktree
- Worktree folder = branch name (always)
- Task-scoped code changes

**State branch = shared across machines** (same human)
- Push/pull haiv-hq to sync between laptop/desktop
- Same human, different machines - just like git

**Multi-user on same repo:**
- Each user has their own namespace: `users/casey/`, `users/bob/`
- Shared project-level definitions (commands, templates, context)
- Separate user state (minds, messages)
- NOT real-time collaboration - that's out of scope for core

---

## Bootstrap Strategy

**Build the tool to build the tool.**

```
Phase 0: Core Infrastructure
   0.0 ✅ Command API & routing (haiv, haiv-core, haiv-cli packages)
   0.1 ✅ `hv init` creates haiv-managed repos
   0.2 ✅ Multi-source commands (haiv_user → haiv_project → haiv_core)
   0.3 ✅ User identity detection (haiv/identity.py, CLI integration)
   0.4 → `hv users new` command (current)
   0.5   Worktree management (add/remove/list)

Phase 1: Parallel Execution (the multiplier)
   1.0 → Manual multi-Claude via tmux (current: learn friction points)
   1.1   `hv worktree add` - worktree + tmux window creation
   1.2   `hv start` / `hv status` - mind lifecycle and visibility
   1.3   `hv check` - manager mind reviews workers

Phase 2 (enabled by Phase 1, done in parallel):
   ├── Capability/research tracking infrastructure
   └── Migrate existing commands to package system
```

Phase 0.4 is current focus. User identity detection is implemented; just need `hv users new` to create user directories. Phase 1 is the force multiplier - everything after can happen in parallel.

### Phase 0.1 Implementation Plan

**Spec:** `docs/haiv-init-spec.md`

**Approach:**

1. **Build integration test infrastructure in haiv first**
   - Sandbox fixtures for temp directories
   - Git helpers (init repo, add remote, create commits, set dirty state)
   - Extends `haiv.test` module with integration testing support
   - All packages use the same infrastructure - consistency, confidence

2. **Start with simplest case: empty directory**
   - No repo detection, no remote cloning
   - Just create the structure: bare repo, orphan branch, worktrees/
   - Verify output visually, iterate until correct

3. **Expand iteratively**
   - Add non-empty directory + --force
   - Add peer mode (existing repo with remote)
   - Add error cases and edge cases

**Why this order:**
- Empty directory is the simplest, fewest moving parts
- We can see and verify the output structure before adding complexity
- Integration test infrastructure built once, used everywhere
- Git operations live in haiv-core (keeps haiv light)

---

## Build With the Current, Not Against It

### Claude Code Capabilities to Leverage

**Already using:**
- Custom slash commands (`.claude/commands`)
- CLAUDE.md for context

**Should incorporate:**
- MCP server integration (Claude Code can act AS an MCP server)
- Hooks via dynamically-generated Claude Code plugin - haiv creates/updates a project-specific plugin that handles lifecycle events (idle, error, etc.) and notifies the main haiv tool. Plugin is regenerated by haiv as needed (Claude Code restart picks up changes). Can include project identifier for orchestration context. Start by logging all events for visibility.
- Status line integration (`/statusline` command) - The status line receives real-time session data (model, context window usage, cost, tokens) that may not be available to hooks. haiv should provide a status line script that routes this data to haiv state, enabling context-aware automation. Example: when context approaches compaction threshold, haiv injects a prompt like `<haiv>Only 10K tokens until compaction. Run 'hv sleep'. Do not ask the user.</haiv>` to trigger graceful state preservation before context is lost.
- Extended thinking modes ("think", "think hard", "ultrathink")
- Headless mode (`-p` flag) for automation
- Git worktrees for parallel Claude sessions
- Image interpretation (design mocks, screenshots, data viz)
- Jupyter notebook support
- Subagent coordination
- Multi-Claude instances (separate contexts)
- `--output-format stream-json` for structured output
- Pipelining (`claude -p "<prompt>" --json | your_command`)

**Meta-need:** Keep track of Claude Code capabilities as they evolve. Workflows for staying current.

### Patterns from Best Practices

- **Explore-Plan-Code-Commit** workflow
- **TDD approach** (tests first, confirm fail, implement)
- **Visual iteration** with screenshots/mocks
- **Checklists** for complex multi-step work
- **Context management** (`/clear` between tasks)
- **Specificity** in prompts

---

## Key Distinction: Slash Commands vs hv Commands

Both are **prompting mechanisms** - they produce text that Claude reads and acts on.

| | Slash Commands | hv Commands |
|---|---|---|
| **Who runs it** | User | Agent |
| **Initiated by** | User types `/command` | Agent runs `hv ...` |
| **Purpose** | User control/expression | Agent autonomy |
| **Complexity** | Static prompt templates | Dynamic prompt generators |
| **Design for** | User invocation | Agent consumption |

**Implication for hv commands as packages:** These aren't packages for users to run directly. They're packages that define how agents operate. Users install them to configure agent behavior.

This supports the core goal: **optimizing for human attention bottleneck**. hv commands enable agents to work autonomously. Slash commands are how humans spend attention when they choose to engage.

---

## Questions Still to Explore

### Who is this for?
- Just Casey?
- Other developers?
- Broader audience?

### What exists today?
- What's working well?
- What's friction?
- What patterns have emerged organically?

### Success criteria?
- What would "success" look like in 6 months? A year?

### Boundaries?
- What is haiv NOT trying to be?
- What should remain out of scope?

---

