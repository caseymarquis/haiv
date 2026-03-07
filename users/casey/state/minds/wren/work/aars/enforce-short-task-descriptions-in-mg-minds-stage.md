# AAR: Enforce short task descriptions in hv minds stage

## Summary

Added character limit enforcement and help text conventions to `hv minds stage`. The `--task` flag now warns at >50 chars and rejects at >72, mirroring git commit subject conventions. Both `--task` and `--description` help text now explain their intended purpose with examples.

## Key Decisions

- Warn at 50, reject at 72 — matches git's convention (50 recommended, 72 hard limit)
- Conventional commit style encouraged via example in help text, not enforced programmatically
- `--description` help clarifies it's for brief high-level context, not full task instructions — avoids naming specific template files since those may change

## Open Items

- No existing tests for `minds stage` — validation logic is untested. Low risk given simplicity, but worth adding if a test harness for commands gets built out.

## Commits and Files Changed

- 8729849 feat(minds stage): enforce short task descriptions
- e43ed66 docs(minds stage): clarify --description flag purpose
  Key files: haiv-core/src/haiv_core/commands/minds/stage.py
