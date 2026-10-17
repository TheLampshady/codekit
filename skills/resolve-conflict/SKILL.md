---
name: resolve-conflict
description: 'Rebase the current branch onto the base branch and resolve merge conflicts with the user, never silently picking a side. Also resumes a rebase or merge already in progress. Use when asked to: rebase on main, update my branch, resolve conflicts, fix merge conflicts, my PR has conflicts.'
user-invocable: true
argument-hint: "[base-branch]"
---

# Resolve Conflict

Brings the current branch up to date with `origin/<base-branch>` by rebasing, with the user deciding every conflict whose right answer depends on intent.

## Principles

- **Never lose work.** Stash or commit dirty state first. Flag anything that could discard changes.
- **Ask when intent matters.** Which side wins, keeping both, or a refactor on the base branch replacing local work: stop and ask.
- **Show, don't summarize.** Present the actual conflict markers with surrounding code.
- **Mind the sides.** During a rebase, `HEAD` / "ours" is the **base branch**, and "theirs" is the user's commit being replayed. Say this explicitly, because people routinely get it backwards.

## Preflight

1. **Base branch:** use the branch named in the prompt, else `git config codekit.basebranch`, else `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), else `main`. Say which one you're using and where it came from.
2. **Already in progress?** If `git status` shows `rebase in progress` or `UU` paths, say so and jump to [the conflict loop](#conflict-loop).
3. **Clean tree:** if `git status --porcelain` is non-empty, ask whether to stash (`git stash push -u -m "codekit: pre-rebase"`), commit (`sdd-commit`), or abort.
4. **Not on base:** if the current branch is `<base-branch>`, ask whether they meant `git pull --rebase` on it, or to switch branches.
5. **Fetch:** `git fetch origin <base-branch>`. Report `git rev-list --count HEAD..origin/<base-branch>` (how far behind), then proceed. If it's 0, say the branch is already up to date and stop.

## Rebase

```bash
git rebase origin/<base-branch>
```

If a hook or config blocks it, show the error verbatim and ask before working around it.

## Conflict loop

1. Run `git status` and list the conflicted files.
2. For each file, show the conflict regions with context and classify them:
   - **Trivial** (import order, formatting, both sides adding the same line): propose a resolution and ask yes/no.
   - **Semantic** (the same logic changed differently, a signature changed): stop. Show both versions, say what each does, and ask which to keep or whether to combine them.
   - **Structural** (deleted on one side, modified on the other; moved files): always ask. Never auto-resolve.
   - **Lockfiles / generated files** (`package-lock.json`, `uv.lock`, `poetry.lock`, `Cargo.lock`, ...): offer to take the base branch's version and regenerate it with the project's install command.
3. Apply the agreed resolution, check that no markers remain in the file (`grep -n '^<<<<<<<\|^=======\|^>>>>>>>' <file>`), then `git add <file>`.
4. When the step is fully resolved: `GIT_EDITOR=true git rebase --continue`.
5. Repeat until the rebase completes.

### Questions worth asking (pick the ones that fit)

- "`<base-branch>` changed `<fn>` to `<new signature>`, but your commit still calls the old one. Should I update your call sites?"
- "Both sides added entries to `<list>`. Keep both, or is one a duplicate?"
- "`<base-branch>` deleted `<file>`, but your commit modifies it. Keep yours, accept the deletion, or move your change elsewhere?"

### Escape hatches

Offer these at any conflict:
- `git rebase --abort` returns cleanly to the pre-rebase state.
- `git rebase --skip` drops the commit being replayed. It's rarely right, so ask first.
- Merge instead: `git rebase --abort && git merge origin/<base-branch>`. This is better when collaborators have already pulled the branch.

## Completion

1. Show `git log --oneline -10` to confirm the history looks right.
2. If you stashed in preflight, ask before running `git stash pop`, and handle any conflicts it produces with the same loop.
3. If the branch was already pushed, note that the next push needs `--force-with-lease`. `sdd-pr` handles this.

## Never

- Run `rebase --continue` while conflict markers remain.
- Use `checkout --ours` / `--theirs` without confirmation, because each silently discards one side.
- Amend, squash, or reorder commits unasked.
- Push, and especially force-push. Pushing belongs to `sdd-pr` or the user.
