# Venv Relay

## Problem

Commands can live in external packages (e.g., haiv-mail) that have their own venvs and dependencies. The `hv` CLI runs in haiv-cli's venv, which doesn't have those dependencies installed. We need to detect when a command requires a different venv and re-launch with the correct one.

## Design

A `VenvResolver` protocol abstracts venv detection. Given a command file path, it returns the venv that command should execute in, or `None` if the current venv is correct.

When the CLI routes to a command file and the resolver says "different venv needed," the CLI re-launches the full `hv` invocation using `uv run --project <path>`. The re-launched process re-routes from scratch — zero coupling, zero state transfer across the boundary.

The loop guard is the venv check itself: if you're already in the right venv, proceed normally.

## Integration Tests

There are integration tests in `haiv-lib/tests/integration/` that prove venv detection works end-to-end. These tests:

- Create temporary projects with their own venvs
- Route commands that land in those projects
- Verify the resolver detects the venv mismatch
- Verify re-launch targets the correct project

**These tests are slow and require real venv creation. They do not run as part of the normal test suite.** Run them explicitly:

```
uv run pytest tests/integration/test_venv_relay.py -v
```

## Key Files

| File | Role |
|------|------|
| `haiv-lib/src/haiv/_infrastructure/venv_resolver.py` | Protocol + default implementation |
| `haiv-cli/src/haiv_cli/__init__.py` | Intercept point: check venv after routing, before loading |
| `haiv-lib/tests/integration/test_venv_relay.py` | Integration tests (run explicitly) |
