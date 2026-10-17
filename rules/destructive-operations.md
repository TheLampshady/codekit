# Destructive Operations

**Activation: Always On**

Confirm with the user before running any command that deletes or overwrites work that isn't trivially recoverable, or that acts on a shared system.

## Always confirm first

| Operation | Why |
|-----------|-----|
| `rm -rf` anything | No undo, and glob mistakes are silent |
| Deleting `specs/`, `openspec/`, or `.specify/memory/` | The plan and constitution other steps depend on |
| `git push --force-with-lease` | Rewrites the remote branch a PR points at |
| `git reset --hard`, `git checkout --` over uncommitted work | Discards changes with no reflog entry |
| Reassigning a Linear issue that belongs to someone else | Takes work out of a teammate's queue |
| Closing, merging, or deleting a GitHub PR or branch | Outward-facing and visible to the whole team |

State what will be affected, then wait. Read the target first (`ls`, `git status`, `gh pr view`), so the question you ask describes what's really there.

## Never do without an explicit request

- Plain `git push --force`. Use `--force-with-lease` instead.
- Rewrite history on the base branch
- Delete a branch that isn't merged
- Replace a Linear issue description wholesale. Append or patch it instead.
- Pass `--no-verify` to skip commit hooks

## Overwriting is deleting

Writing a file that already exists destroys its contents. Before overwriting, read the file. If it has content you didn't author, append or edit rather than replacing. If replacing is genuinely right, say what you're discarding.
