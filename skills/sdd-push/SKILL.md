---
name: sdd-push
description: 'Open or update a GitHub pull request for the current feature branch with the gh CLI. Confirms the plan, rebases on the base branch (resolving conflicts), archives OpenSpec changes, updates the project docs in docs/project/ when the repo does not use Linear, pushes, creates the PR with a templated body that links the Linear issue, and moves the issue to In Review. Use when asked to: open a PR, create a pull request, push for review, submit for review, send it, update the PR.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[--draft] [base-branch]"
---

# SDD Push

The last step of the loop: a committed feature branch becomes a GitHub PR, linked to its Linear issue.

## Workflow

### 1. Preflight

1. **gh:** run `gh auth status`. If gh isn't installed or authenticated, stop and tell the user to run `! gh auth login`.
2. **Base branch (`<base-branch>`):** use the branch named in the prompt, else `git config codekit.basebranch`, else `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`. Offer once to save a detected value: `git config -f .config/.gitconfig codekit.basebranch <branch>` (`--local` if that file doesn't exist).
3. **Branch:** `git branch --show-current` must not be `<base-branch>`. If it is, stop. If it prints nothing, HEAD is detached, usually by a rebase in progress. Stop too. If `git status` shows a rebase in progress, `resolve-conflict` resumes it.
4. **Uncommitted changes:** if `git status --porcelain` isn't empty, ask whether to commit first. On a yes, read [../sdd-commit/SKILL.md](../sdd-commit/SKILL.md) and follow it, then continue here.
5. **Commits:** `git rev-list --count origin/<base-branch>..HEAD` must be ≥1. If it's more than one, mention it. That's fine, so don't squash unasked.
6. **Existing PR:** run `gh pr view --json number,url,state,isDraft 2>/dev/null`. If an open PR exists, this run is an **update**. Skip creation in Step 4 and refresh the body instead.
7. **Ticket ID:** if `git config codekit.linear` is `false`, run in no-ticket mode. Otherwise, take it from the branch's commits (`git log --format=%B origin/<base-branch>..HEAD`, newest first), but only from a `[<ID>] ::` subject or a `Linear:` line (an ID, or the ID in an issue URL), which `sdd-commit` already checked. Never from elsewhere in a message: a body line like "read files as UTF-8" looks like an ID too. Failing that, use a Linear identifier (`[A-Za-z][A-Za-z0-9]+-\d+`) in the branch name, uppercased, but only if the part before the `-` is the `git config codekit.linear-team` key or, with no team key set, `get_issue` finds it. Version numbers and dates match the same pattern (`feature/upgrade-node-20` → `NODE-20`). If there's no ID, run in no-ticket mode.
8. **Issue (ticket mode):** call `get_issue` once with `fields: ["title", "description", "team", "status", "statusType"]`, and reuse the result in Steps 2 and 4. Step 5 fetches again, after the PR exists. If Linear says the issue doesn't exist, warn and run in no-ticket mode. If Linear can't be reached, keep the ID, warn, and expect the Linear steps to fail.

### 2. Confirm

Show one summary and confirm the target branch. A PR is always opened (or updated), so never ask whether to make one:

```
Source:   <branch>  (<n> commit(s) ahead)
Target:   <base-branch>  (from <config | gh default | prompt>)
Rebase:   onto origin/<base-branch>
Archive:  openspec/changes/<change-id> → openspec/specs/  |  already archived  |  n/a (not OpenSpec)
Docs:     update docs/project/ and amend  |  n/a (Linear, no docs/project/, or draft)
Push:     git push -u origin <branch>   [--force-with-lease if history was rewritten]
PR:       create into <base-branch>  |  update #<number>  [+ mark ready | + back to draft]
Linear:   <ticket-id> "<issue title>" → link PR + move to "<review-state>" + upload spec  |  none
```

The issue title is there so the user can catch a wrong ID before `Fixes` links it.

Options: **Proceed to `<base-branch>` (recommended)**, **Proceed as draft**, **Change target branch**, **Cancel**. On a change, ask for the branch, set `<base-branch>` to it, and show the summary again.

`<review-state>` comes from `list_issue_statuses` for the issue's team: the `started`-type state whose name contains "review" (case-insensitive), e.g. *In Review* or *Code Review*. If there's none, or there are several and none is plainly the right one, show `Linear: link PR only` and skip the move.

### 3. Rebase, archive, and push

1. Run the `resolve-conflict` skill targeting `<base-branch>`. It fetches, rebases, and walks through any conflicts with the user. Continue only once it completes cleanly. If the user aborts, stop here.
2. **OpenSpec only: archive the change** in this PR, so no follow-up PR is needed. It runs after the rebase, so it builds on every change already archived on `<base-branch>`. See [Archive](#archive) below. Skip it for draft PRs. SpecKit and no-framework specs aren't committed at all: the Linear issue holds them (Step 5), so there's nothing to archive.
3. **Project docs, without Linear:** only when `git config codekit.linear` is `false` and `docs/project/product-map.md` exists. Skip it for draft PRs. Read [../project-docs/SKILL.md](../project-docs/SKILL.md) and follow it. It runs after the rebase, so it builds on the docs every merged PR left. If it changed `docs/project/`, amend them into the branch's commit (`git add docs/project && git commit --amend --no-edit`), retrying once after a reformatting hook as the archive does.
4. Push:
   - If the branch has no upstream, or the rebase didn't rewrite pushed commits: `git push -u origin HEAD`
   - If pushed history was rewritten by an amend or rebase: `git push --force-with-lease -u origin HEAD`. Say why it's needed. Never use plain `--force`.

#### Archive

OpenSpec only. Run `/opsx:archive <change-id>`, else `openspec archive <change-id> --yes`. It merges the change's spec deltas into `openspec/specs/` and moves the folder to `openspec/changes/archive/<date>-<change-id>/`.

1. **Already archived?** If the change is under `openspec/changes/archive/`, skip. OpenSpec can't archive it again: it finds a change by its active folder, which the archive moved. If the spec has to change after archiving (e.g. after review feedback), ask the user whether to open a new change for it or edit `openspec/specs/` directly in this PR.
2. **Amend** it into the branch's commit (`git add -A openspec && git commit --amend --no-edit`), so the branch keeps one commit. If a pre-commit hook reformats files, run `git add -A openspec` and retry once. On any other failure, show it and stop. The push then needs `--force-with-lease` if the commit was already pushed.

If two PRs that both touch the same capability are open at once, whichever merges second conflicts on `openspec/specs/`. Running `/sdd-push` again rebases, and `resolve-conflict` walks through it.

### 4. Create or update the PR

1. **Body:** use the repo's `.github/pull_request_template.md` (or `.github/PULL_REQUEST_TEMPLATE/*.md`) if one exists. Otherwise use [resources/pr-template.md](resources/pr-template.md). Fill it in from:
   - the Linear issue (from preflight, or the conversation)
   - the plan or spec files written by `sdd-plan`
   - `git log origin/<base-branch>..HEAD` and `git diff --stat origin/<base-branch>...HEAD`
   - the latest local review report (`${TMPDIR:-/tmp}/codekit/<repo>/reviews/<branch-name-with-slashes-as-dashes>.md`), if it's still there
2. **Linear link:** the body must include `Fixes <ticket-id>`. Linear's GitHub integration uses that phrase to link the PR and close the issue on merge. If the user says the PR only partly addresses the issue, use `Part of <ticket-id>` instead. In no-ticket mode, drop the template's `Fixes` line.
3. **Title:** the commit subject, if there's one commit. Otherwise `[<ticket-id>] :: <issue title>`, or `[TASK] :: <summary of the commits>` in no-ticket mode.
4. **Create:**
   ```bash
   gh pr create --base <base-branch> --head <branch> --title "<title>" --body-file - [--draft] <<'EOF'
   <body>
   EOF
   ```
   **Update:** `gh pr edit <number> --body-file -` (same heredoc). Change the title only if the user asks. If the PR is a draft and the user chose **Proceed**, also run `gh pr ready <number>`. If it's ready and they chose **Proceed as draft**, run `gh pr ready <number> --undo`.
5. Capture `<pr-url>` from the output, or from `gh pr view --json url -q .url`.

Reviewers: if `git config codekit.reviewers` holds a comma-separated list of GitHub handles, add `--reviewer <list>`. Otherwise rely on CODEOWNERS and don't prompt for reviewers.

### 5. Update Linear (ticket mode only)

Linear's GitHub integration, when installed, already attaches the PR and moves the issue on its own. These steps fill in for it when it isn't installed, and they're safe to run when it is.

1. `get_issue` with `fields: ["attachments", "status"]`. If `<pr-url>` isn't among the attachments, call `save_issue` with `id: <ticket-id>` and `links: [{ url: <pr-url>, title: "PR #<number>: <title>" }]`.
2. If the status isn't already `<review-state>` (or a later state), call `save_issue` with `state: <review-state>`. Skip this for draft PRs. Draft means the work isn't ready for review.
3. **Upload the spec:** read [../linear-docs/SKILL.md](../linear-docs/SKILL.md) and follow it on the plan folder with `--issue <ticket-id>`, so the issue this PR links holds the spec, plan, and research as shipped. This is the only point where specs leave your machine: they stay local while you work, where SpecKit expects them. It isn't optional: for SpecKit and no-framework projects the issue is the spec's only copy, and the `codekit-docs` Action reads it after merge to build the Decision Log. After an OpenSpec archive, the plan folder is `openspec/changes/archive/<date>-<change-id>/`, so pass that path. Don't pass `--prune`. If no key is set, warn that the Decision Log will miss this ticket.

If a Linear call fails, warn and continue. The PR is the deliverable and must not be rolled back.

### 6. Summary

End with the PR URL (created or updated, draft or ready), and anything skipped or failed in the rebase, archive, or Linear steps.
