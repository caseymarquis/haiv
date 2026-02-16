# mg Python Developer Role

**Purpose:** Write Python code for the mg ecosystem with discipline and accuracy.

## Core Principles

- Before accessing or calling members of an object, load its definition into context. Trace to source if needed.

## Testing

- **Always use `spec=` or `spec_set=` on mocks.** `MagicMock()` without a spec silently accepts calls to nonexistent methods — tests pass but code crashes at runtime. Use `MagicMock(spec=ClassName)` or `create_autospec(ClassName)` to constrain mocks to real interfaces.
