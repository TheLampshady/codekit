---
name: sdd-commit
description: 'Commit the current feature work with a templated message that carries the Linear issue ID. Guards against committing to the base branch, stages changes, writes the message from the project''s commit template, amends when the branch already has its commit, and retries once after formatter hooks. Use when asked to: commit, commit my changes, wrap up, save changes, amend the commit.'
user-invocable: true
disable-model-invocation: true
---

# SDD Commit

One feature branch carries one evolving commit by default: the first run creates it and later runs amend it. That keeps the PR history clean without forcing a squash on merge. If the user wants a separate commit, they can say so and the skill will make a new one.

## Workflow

### 1. Branch safety

1. Resolve `<base-branch>`: `git config codekit.basebranch`, then `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), then whichever of `origin/main` / `origin/master` exists, then `main`.
2. If `git branch --show-current` equals `<base-branch>`, stop. Offer to create a feature branch (`/sdd-plan` for a Linear issue, or `git checkout -b <name>`). Never commit to the base branch.

### 2. Stage and decide the strategy

1. `git status --porcelain`.
2. If there are changes, show the file list and stage it with `git add -A`. Leave out anything that looks like a secret (`.env*`, `*.pem`, `*.key`) or an accident (stray build output, large binaries), and say what you left out.
3. Count `<ahead>` = `git rev-list --count origin/<base-branch>..HEAD` (fall back to `<base-branch>..HEAD`).

| Changes staged? | `<ahead>` | Strategy |
|-----------------|-----------|----------|
| No | 0 | Stop: "Nothing to commit. The working tree is clean and matches `<base-branch>`." |
| No | ≥1 | **Reword** only if the user asked to fix the message. Otherwise stop. |
| Yes | 0 | **New** commit |
| Yes | ≥1 | **Amend**, unless the user asked for a separate commit or the last commit is already on the remote and others may have pulled it. If `git status -sb` shows the branch tracking a remote with an open PR, amend still works, but warn that `sdd-pr` will need `--force-with-lease`. |

### 3. Resolve the template and ticket

**Template**, first match wins:
1. `git config commit.template`, if the file exists
2. `.config/.commit-message-template` or `.gitmessage` in the repo
3. [resources/.commit-message-template](resources/.commit-message-template)

**Ticket ID** (`<ticket-id>`):
1. A Linear identifier (`[A-Za-z][A-Za-z0-9]+-\d+`) in the branch name, uppercased. Linear branch names look like `user/eng-123-title`.
2. When amending, the ID in the previous message.
3. The conversation.
4. If none, drop the ticket fields from the template. Don't invent one.

For the summary, use the Linear issue title from the conversation, or `get_issue`, as raw material. Describe the change, not the ticket.

### 4. Write the message

- Follow the template's structure exactly. Replace every placeholder. Remove any section that has nothing true to say, such as `Testing:` when nothing was tested.
- **Subject** ≤ 72 characters, imperative mood. **Body** wrapped at 72.
- The bullets describe what changed and why. They don't restate the diff line by line.
- **Amend:** rewrite the message so it describes the whole commit (previous work plus new changes), not just the delta. Keep existing trailers (`Co-authored-by:`, `Signed-off-by:`).
- Show the message to the user before committing. Commit straight away unless they asked to review it first.

### 5. Commit

Use a heredoc so quoting can't break:

```bash
git commit -F - <<'EOF'
<message>
EOF
```

Use `git commit --amend -F -` for amend or reword.

**Hook handling:**
- If the commit fails because a pre-commit hook reformatted files, run `git add -u` and retry **once**.
- If it fails on a lint, type or test error, show the output verbatim and stop. Never pass `--no-verify` unless the user explicitly asks.

### 6. Review and summary

1. Run the local review, unless the user said to skip it. Its instructions are in [../code-review-local/SKILL.md](../code-review-local/SKILL.md). If you can start a subagent (Claude Code's Agent tool, `general-purpose`), give it that file's path and `<base-branch>`, and tell it to follow the file. That way the review comes from a reviewer that hasn't seen this conversation. Otherwise, follow the file here. Surface any **Blockers** prominently.
2. Report the short hash, the branch, the subject, new or amended, and the review result.
3. **Next:** if the review found no blockers, run `/sdd-pr`. If it found blockers, fix them and run `/sdd-commit` again, which amends. If this skill was called by another workflow, return to it instead.
