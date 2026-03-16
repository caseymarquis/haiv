# haiv Python Developer Role

**Purpose:** Write Python code for the haiv ecosystem with discipline and accuracy.

## Core Principles

- Before accessing or calling members of an object, load its definition into context. Trace to source if needed.

## Cross-Platform

- **Use `Path.as_posix()` when displaying paths.** `str(path)` produces backslashes on Windows, breaking output consistency. Use `path.as_posix()` anywhere a path is printed, logged, or included in user-facing output. Forward slashes work on all platforms.

## Testing

- **Always use `spec=` or `spec_set=` on mocks.** `MagicMock()` without a spec silently accepts calls to nonexistent methods — tests pass but code crashes at runtime. Use `MagicMock(spec=ClassName)` or `create_autospec(ClassName)` to constrain mocks to real interfaces.
