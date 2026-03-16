# AAR: fix: 1 failing test in haiv-core on Windows

## Summary

Fixed the one remaining test failure in haiv-core after the Windows compatibility work. The `test_task_flag_required` test expected the old error string `"--task is required"` but the production code had been updated to `"--task is missing"`. Updated the test expectation to match.

## Key Decisions

- Updated the test rather than the production code — the new `"--task is missing"` message is more descriptive and was an intentional improvement in the Windows compatibility PR.

## Open Items

None. All tests pass across all packages (haiv-lib: 699 passed, haiv-core: 234 passed, haiv-cli: 18 passed).

## Commits and Files Changed

- 2f8e671 fix: update test expectation for --task error message
  Key files: haiv-core/tests/test_minds_stage.py
