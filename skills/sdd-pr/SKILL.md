---
name: sdd-pr
description: 'Open or update a GitHub pull request for the current feature branch with the gh CLI. Confirms the plan, rebases on the base branch (resolving conflicts), pushes, creates the PR with a templated body that links the Linear issue, and moves the issue to In Review. Use when asked to: open a PR, create a pull request, push for review, submit for review, send it, update the PR.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[--draft] [base-branch]"
---

# SDD PR

The last step of the loop: a committed feature branch becomes a GitHub PR, linked to its Linear issue.

## Workflow

### 1. Preflight

1. **gh:** run `gh auth status`. If gh isn't installed or authenticated, stop and tell the user to run `! gh auth login`.
2. **Base branch (`<base-branch>`):** use the branch named in the prompt, else `git config codekit.basebranch`, else `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. Offer once to save a detected value: `git config --local codekit.basebranch <branch>`.
3. **Branch:** `git branch --show-current` must not be `<base-branch>`. If it is, stop.
4. **Uncommitted changes:** if `git status --porcelain` isn't empty, ask whether to commit first. On a yes, read [../sdd-commit/SKILL.md](../sdd-commit/SKILL.md) and follow it, then continue here.
5. **Commits:** `git rev-list --count origin/<base-branch>..HEAD` must be ≥1. If it's more than one, mention it. That's fine, so don't squash unasked.
6. **Existing PR:** run `gh pr view --json number,url,state,isDraft 2>/dev/null`. If an open PR exists, this run is an **update**. Skip creation in Step 4 and refresh the body instead.
7. **Ticket ID:** a Linear identifier (`[A-Za-z][A-Za-z0-9]+-\d+`) from the branch name, else from `git log -1 --pretty=%B`, uppercased. If there isn't one, run in no-ticket mode.

### 2. Confirm

Show one summary and ask whether to proceed:

```
Source:   <branch>  (<n> commit(s) ahead)
Target:   <base-branch>  (from <config | gh default | prompt>)
Rebase:   onto origin/<base-branch>
Push:     git push -u origin <branch>   [--force-with-lease if history was rewritten]
PR:       create (draft? yes/no)  |  update #<number>
Linear:   <ticket-id> → link PR + move to "<review-state>"  |  none
```

Options: **Proceed (recommended)**, **Proceed as draft**, **Cancel**.

`<review-state>` comes from `list_issue_statuses` for the issue's team: the `started`-type state whose name contains "review" (case-insensitive), e.g. *In Review* or *Code Review*. If there's none, or there are several and none is plainly the right one, show `Linear: link PR only` and skip the move.

### 3. Rebase and push

1. Run the `resolve-conflict` skill targeting `<base-branch>`. It fetches, rebases, and walks through any conflicts with the user. Continue only once it completes cleanly. If the user aborts, stop here.
2. Push:
   - If the branch has no upstream, or the rebase didn't rewrite pushed commits: `git push -u origin HEAD`
   - If pushed history was rewritten by an amend or rebase: `git push --force-with-lease -u origin HEAD`. Say why it's needed. Never use plain `--force`.

### 4. Create or update the PR

1. **Body:** use the repo's `.github/pull_request_template.md` (or `.github/PULL_REQUEST_TEMPLATE/*.md`) if one exists. Otherwise use [resources/pr-template.md](resources/pr-template.md). Fill it in from:
   - the Linear issue (`get_issue`, or the conversation)
   - the plan or spec files written by `sdd-plan`
   - `git log origin/<base-branch>..HEAD` and `git diff --stat origin/<base-branch>...HEAD`
   - the latest local review report (`.codekit/reviews/`), if any
2. **Linear link:** the body must include `Fixes <ticket-id>`. Linear's GitHub integration uses that phrase to link the PR and close the issue on merge. If the user says the PR only partly addresses the issue, use `Part of <ticket-id>` instead.
3. **Title:** the commit subject, if there's one commit. Otherwise `[<ticket-id>] <issue title>`.
4. **Create:**
   ```bash
   gh pr create --base <base-branch> --head <branch> --title "<title>" --body-file - [--draft] <<'EOF'
   <body>
   EOF
   ```
   **Update:** `gh pr edit <number> --body-file -` (same heredoc). Change the title only if the user asks.
5. Capture `<pr-url>` from the output, or from `gh pr view --json url -q .url`.

Reviewers: if `git config codekit.reviewers` holds a comma-separated list of GitHub handles, add `--reviewer <list>`. Otherwise rely on CODEOWNERS and don't prompt for reviewers.

### 5. Update Linear (ticket mode only)

Linear's GitHub integration, when installed, already attaches the PR and moves the issue on its own. These steps fill in for it when it isn't installed, and they're safe to run when it is.

1. `get_issue` with `fields: ["attachments", "status"]`. If `<pr-url>` isn't among the attachments, call `save_issue` with `id: <ticket-id>` and `links: [{ url: <pr-url>, title: "PR #<number>: <title>" }]`.
2. If the status isn't already `<review-state>` (or a later state), call `save_issue` with `state: <review-state>`. Skip this for draft PRs. Draft means the work isn't ready for review.
3. For a **new** PR, call `save_comment` (`issueId: <ticket-id>`) with:
   ```
   PR opened: <pr-url>

   <commit subject>
   ```
   Don't comment on updates, because the attachment already tracks them.
4. **Refresh the docs:** if the issue already has documents named after the plan files (from `get_issue`, or because `sdd-plan` published them), read [../linear-docs/SKILL.md](../linear-docs/SKILL.md) and follow it on the plan folder so the issue matches what shipped, with tasks checked off and the plan revised. Don't pass `--prune`. If the issue has no such documents, skip this step: publishing is opt-in at plan time.

If a Linear call fails, warn and continue. The PR is the deliverable and must not be rolled back.

### 6. Summary

- **PR:** `<pr-url>`, created or updated, draft or ready.
- **Rebase:** clean or conflicts resolved, plus whether the push needed `--force-with-lease`.
- **Linear:** link added, state moved, comment posted, docs refreshed, or each one that was skipped and why.
- **After merge:** for OpenSpec, run `/opsx:archive <change-id>` on the base branch to fold the spec deltas into `openspec/specs/`.
