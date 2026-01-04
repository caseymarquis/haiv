```index
@memory-persistence
Memory persistence for long-running minds. Defines directory conventions,
references.toml format, and mg wake/start/mine commands.
```

```toml
version_specced = "0.1.2"
version_implemented = "none"
```

# Memory Persistence Specification

## Change Log

### 0.1.2
- Added @memory-persistence ref-id

### 0.1.1
- Added `docs/` folder to mind directory structure
- Updated examples to use proper paths (minds/{mind}/docs/) instead of temp folders
- Added common reference targets section

### 0.1.0
- Initial specification

---

## Context

Long-running minds need to reload context after compaction or fresh starts. This spec defines the directory conventions and commands for mind startup.

---

## Directory Structure

### Mind Folders

```
users/casey/state/minds/
├── wren/
│   ├── startup/
│   │   ├── references.toml
│   │   ├── identity.md
│   │   └── current-focus.md
│   └── docs/
│       └── problems.md
├── _new/
│   └── reed/
│       └── startup/
│           └── references.toml
└── _archived/
    └── old-worker/
```

### Naming Convention

<input>
Directory name: wren
</input>

<output>
Valid mind name
</output>

<input>
Directory name: _new
</input>

<output>
Organizational directory (not a mind)
</output>

<input>
Directory name: _archived
</input>

<output>
Organizational directory (not a mind)
</output>

Mind names cannot start with underscore. Directories starting with `_` are organizational.

---

## references.toml

### Format

```toml
[[references]]
path = "src/mg_project/__assets__/roles/coo.md"

[[references]]
path = "users/casey/state/minds/wren/docs/problems.md"
```

Paths are relative to the mg-state root.

### Common Reference Targets

- `src/mg_project/__assets__/roles/` - shared roles
- `minds/{mind}/docs/` - mind-specific documents (specs, problem backlogs, etc.)
- `minds/{mind}/startup/` - documents loaded directly (identity, current focus)

---

## mg wake

Outputs a list of files for the mind to read.

### Basic Usage

<input>
Command: mg wake wren

minds/wren/startup/ contains:
  - references.toml (points to roles/coo.md, docs/problems.md)
  - identity.md
  - current-focus.md
</input>

<output>
Read the following files in their entirety:
- src/mg_project/__assets__/roles/coo.md
- users/casey/state/minds/wren/docs/problems.md
- users/casey/state/minds/wren/startup/identity.md
- users/casey/state/minds/wren/startup/current-focus.md
</output>

### Mind in Organizational Directory

<input>
Command: mg wake reed

minds/_new/reed/startup/ contains:
  - references.toml (points to roles/analyst.md)
</input>

<output>
Read the following files in their entirety:
- src/mg_project/__assets__/roles/analyst.md
- users/casey/state/minds/_new/reed/startup/references.toml
</output>

### Mind Not Found

<input>
Command: mg wake unknown
</input>

<output>
Error: Mind 'unknown' not found in minds/ or any organizational subdirectory.
</output>

### Resolution Order

When searching for a mind:
1. Check `minds/{mind}/`
2. Check `minds/_*/{mind}/` (organizational subdirectories)

If found in multiple locations, error.

<input>
Command: mg wake reed

minds/reed/ exists
minds/_new/reed/ exists
</input>

<output>
Error: Mind 'reed' found in multiple locations:
- minds/reed/
- minds/_new/reed/
</output>

---

## mg start

Launches Claude with a mind's context.

### Current Terminal (no --tmux)

<input>
Command: mg start wren
</input>

<output>
Terminal is cleared.
Claude is started.
Initial prompt injected: "Run `mg wake wren`"
</output>

### New tmux Window (--tmux)

<input>
Command: mg start wren --tmux
</input>

<output>
New tmux window created, named "wren".
Terminal is cleared.
Claude is started in that window.
Initial prompt injected: "Run `mg wake wren`"
</output>

### Mind Not Found

<input>
Command: mg start unknown
</input>

<output>
Error: Mind 'unknown' not found in minds/ or any organizational subdirectory.
</output>

---

## mg mine

Displays important locations for the calling mind.

### Basic Usage

<input>
Command: mg mine
Environment: MG_MIND=wren
</input>

<output>
Mind: wren
Location: users/casey/state/minds/wren/

Startup context:
  users/casey/state/minds/wren/startup/
  Files loaded on wake. Add references.toml for external docs.

Role:
  src/mg_project/__assets__/roles/coo.md
  (from references.toml)
</output>

### No Mind Set

<input>
Command: mg mine
Environment: MG_MIND not set
</input>

<output>
Error: MG_MIND environment variable not set. Run via `mg start {mind}`.
</output>

---

## Startup Folder Contents

### references.toml

Required. Points to external documents.

### Other Files

Any other files in `startup/` are included in the wake output. Common patterns:

- `identity.md` - who this mind is, responsibilities, accumulated knowledge
- `current-focus.md` - active tasks, recent decisions, blockers, next steps

---

## Environment

### MG_MIND

Set by `mg start`. Contains the mind name.

<input>
Command: mg start wren
</input>

<output>
MG_MIND=wren is set in the Claude process environment.
</output>

Used by `mg mine` and potentially other commands that need to know the current mind.
