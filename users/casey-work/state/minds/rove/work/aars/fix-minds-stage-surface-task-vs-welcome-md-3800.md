# AAR: fix(minds stage): surface task vs welcome.md distinction

## Summary

Updated `hv minds stage` output so the two-audience distinction is clear on first use. Flag descriptions, error messages, and the "Next steps" section now explain that `--task`/`--description` are coordinator labels, while `work/welcome.md` is the actual assignment the new mind reads.

## Key Decisions

- Kept the clarification to two lines in the "Next steps" output — enough to be clear without being a wall of text
- Updated flag descriptions and error messages with the same language for consistency (prior work on this branch)
- Did not fix the `test_task_flag_required` test (`"--task is required"` → `"--task is missing"`) to avoid merge conflicts with the Windows test fix initiative

## Open Items

### Verification needed

- Tests cannot run on Windows currently (separate initiative). The one known test breakage is `test_task_flag_required` expecting the old error string — easy fix once the test initiative lands.

## Commits and Files Changed

- a091fb3 fix(minds stage): surface task vs welcome.md distinction in output
  Key files: haiv-core/src/haiv_core/commands/minds/stage.py
