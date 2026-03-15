# haiv Wishlist

Issues and improvements to pass along to haiv minds.

---

- **`hv sessions <id>` detail view** — Currently only list and remove. Would be useful to see mind name, task, description, worktree, parent session, and status for a single session.
- **`hv minds stage` should explain the two audiences** — `--task`/`--description` are management labels for the staging mind. `welcome.md` is what the new mind actually reads. The tool should surface this distinction so managers don't have to learn it by trial and error.
- **`hv pop` AAR path should explain why it points elsewhere** — When pop tells a mind to write an AAR in another mind's directory, it should briefly explain that AARs belong to the assigning mind. Without this, the working mind's instinct is to assume it's a bug and write the AAR in its own directory instead.
- **Persistent async communication between minds** — Current `hv minds prompt` is like shouting down the hall — ephemeral, requires the recipient to be running. We need the equivalent of sending an email: a message that persists until the recipient reads it. Use case: escalating findings (e.g., "this needs a Jira ticket") from one mind to another without requiring synchronous sessions.
- **Control over the journey example and templates** — The example journey in haiv-core's assets shapes how explorers write. We need project-level control over the example journey (incoming haiv update) and over the journal entry templates (observation/inference structure, thin-file guidance, etc.).
- **`hv chart explore --clear` or debug command** — Exploration state is stored in `work/exploration.json` in the mind's directory. If a journey is abandoned or the state gets stale, there's no way to clear it or inspect it without manually finding and deleting the file. A `--clear` flag or a `hv chart debug` command that shows the current state and offers to reset it would help.
