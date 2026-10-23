---
name: sdd-commit
description: 'Commit the current feature work with a templated message that carries the ticket ID. Guards against committing to the base branch, stages changes, writes the message from the project''s commit template, amends when the branch already has its commit, and retries once after formatter hooks. Use when asked to: commit, commit my changes, wrap up, save changes, amend the commit.'
user-invocable: true
disable-model-invocation: true
---

# SDD Commit

One feature branch carries one evolving commit by default: the first run creates it and later runs amend it. That keeps the PR history clean without forcing a squash on merge. If the user wants a separate commit, they can say so and the skill will make a new one.

## Workflow

### 1. Branch safety

1. Resolve `<base-branch>`: `git config codekit.basebranch`, then `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), then whichever of `origin/main` / `origin/master` exists, then `main`.
2. If `git branch --show-current` equals `<base-branch>`, stop. Offer to create a feature branch (`/sdd-plan` for a ticket, or `git checkout -b <name>`). Never commit to the base branch.
3. If it prints nothing, HEAD is detached, usually by a rebase in progress. Stop: a commit here would land in the middle of the rebase. If `git status` shows a rebase in progress, `resolve-conflict` resumes it.

### 2. Stage and decide the strategy

1. `git status --porcelain`.
2. If there are changes, show the file list and stage it with `git add -A`. Leave out anything that looks like a secret (`.env*`, `*.pem`, `*.key`) or an accident (stray build output, large binaries), and say what you left out.
3. Count `<ahead>` = `git rev-list --count origin/<base-branch>..HEAD` (fall back to `<base-branch>..HEAD`).

| Changes staged? | `<ahead>` | Strategy |
|-----------------|-----------|----------|
| No | 0 | Stop: "Nothing to commit. The working tree is clean and matches `<base-branch>`." |
| No | ≥1 | **Reword** only if the user asked to fix the message. Otherwise stop. |
| Yes | 0 | **New** commit |
| Yes | ≥1 | **Amend**, unless the user asked for a separate commit or someone else has pushed to this branch (below) |

Amending rewrites the branch's last commit, so check two things first:
- **Someone else has pushed to this branch:** `git log --format=%ae origin/<base-branch>..origin/<branch>` lists an email other than `git config user.email`. Make a **new** commit instead, because rewriting a shared branch breaks their copy.
- **The commit is already pushed:** `git branch -r --contains HEAD` lists a branch. Amend anyway, and warn that `sdd-push` will push with `--force-with-lease`.

### 3. Resolve the template and ticket

**Template**, first match wins:
1. `git config commit.template`, if the file exists
2. `.config/.commit-message-template` or `.gitmessage` in the repo
3. [resources/.commit-message-template](resources/.commit-message-template)

**Ticket ID** (`<ticket-id>`). If `git config codekit.linear` is `false`, there's none. Otherwise, first match wins:
1. A ticket identifier (`[A-Za-z][A-Za-z0-9]+-\d+`) in the branch name, uppercased, e.g. `user/eng-123-title` → `ENG-123`. Version numbers and dates match the same pattern (`feature/upgrade-node-20` → `NODE-20`), so keep it only if the part before the `-` is the `git config codekit.linear-team` key or, with no team key set, if `get_issue` finds it. If Linear can't be reached, keep it and say it's unchecked.
2. When amending, the ID in the previous message.
3. The conversation.
4. None. Don't invent an ID.

**Ticket link** (`<ticket-url>`): the issue's `url` from `get_issue` (`fields: ["url"]`, or reuse the call that checked the ID), without the title slug after the ID: `https://linear.app/<workspace>/issue/ENG-123`. If Linear can't be reached, use the ID.

**Ticket slots.** Every commit names its ticket, whatever the template's placeholders say, so it can be traced back:
- **Subject tag:** the subject's leading `[...]` is the ticket slot, whatever the template writes there (`[TICKET_ID]`, `[TASK]`, `[ABC-000]`). Fill it with `[<ticket-id>]`, or `[TASK]` when there's no ticket.
- **Link line:** with a ticket, fill the template's `Linear:` line with `<ticket-url>`. If the template has none, add `Linear: <ticket-url>` as the message's last line. With no ticket, drop the line.

For the summary, use the ticket title from the conversation or the spec as raw material. Describe the change, not the ticket.

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
- If the commit fails because a pre-commit hook reformatted files, re-stage the files you staged in Step 2 (`git add <files>`) and retry **once**. Not `git add -u`: it would also stage tracked files you left out.
- If it fails on a lint, type or test error, show the output verbatim and stop. Never pass `--no-verify` unless the user explicitly asks.

### 6. Review and summary

1. Run the local review, unless the user said to skip it. Its instructions are in [../code-review-local/SKILL.md](../code-review-local/SKILL.md). If you can start a subagent (Claude Code's Agent tool, `general-purpose`), give it that file's path and `<base-branch>`, and tell it to follow the file. That way the review comes from a reviewer that hasn't seen this conversation. Otherwise, follow the file here. Surface any **Blockers** prominently.
2. End with the short hash, the subject, new or amended, and the review result. Next is `/sdd-push`, or fixing blockers and running `/sdd-commit` again, which amends.
