---
name: sdd-push
description: 'Open or update the pull request (GitHub, with gh) or merge request (GitLab, with glab) for the current feature branch. Asks for the base branch only the first time, then rebases on it (resolving conflicts), archives OpenSpec changes, updates the project docs in docs/project/ when the repo has no tracker, pushes, opens the request with a templated body that closes the issue, uploads the spec to the tracker, and moves the issue to In Review. Use when asked to: open a PR, open an MR, create a pull request, create a merge request, push for review, submit for review, send it, update the PR.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[--draft] [base-branch]"
---

# SDD Push

The last step of the loop: a committed feature branch becomes a pull request on GitHub or a merge request on GitLab, linked to its issue. Below, *PR* means either.

## Code host

`<host>` is the host in `git remote get-url origin` (`https://<host>/…`, `git@<host>:…`, `ssh://git@<host>:<port>/…`). `github.com` is GitHub and `gitlab.com` is GitLab. For any other host, a domain or an IP address, it's GitLab if `glab auth status --hostname <host>` succeeds, and GitHub (Enterprise) if `gh auth status --hostname <host>` does. If neither does, stop: say the host isn't logged in, and give both logins, `! glab auth login --hostname <host>` and `! gh auth login --hostname <host>`, so the user runs the one for their host.

Use that host's column wherever a step names a command:

| | GitHub (`gh`) | GitLab (`glab`) |
|--|--|--|
| Logged in | `gh auth status` | `glab auth status --hostname <host>` |
| Default branch | `gh repo view --json defaultBranchRef -q .defaultBranchRef.name` | `default_branch` in `glab repo view --output json` |
| Open PR for the branch | `gh pr view --json number,url,state,isDraft` | `glab mr list --source-branch <branch> --output json`: `iid`, `web_url`, `draft` |
| Repo's own template | `.github/pull_request_template.md`, or `.github/PULL_REQUEST_TEMPLATE/*.md` | `.gitlab/merge_request_templates/Default.md` |
| Create | `gh pr create --base <base-branch> --head <branch> --title "<title>" --body-file - [--draft]` | `glab mr create --source-branch <branch> --target-branch <base-branch> --title "<title>" --description-file - --yes [--draft]` |
| Update the body | `gh pr edit <number> --body-file -` | `glab mr update <number> --description-file - --yes` |
| Back to draft / mark ready | `gh pr ready <number> --undo` / `gh pr ready <number>` | `glab mr update <number> --draft` / `glab mr update <number> --ready` |
| Reviewers | `--reviewer <list>` on create | `--reviewer <list>` on create |
| URL | from the create output, or `gh pr view --json url -q .url` | from the create output, or `web_url` from the open-PR command |

Feed the body through a heredoc (`<<'EOF'`), so quoting can't break it.

## Tracker

`git config codekit.tracker` names it. With `none`, or unset, run in **no-ticket mode**: skip everything marked *ticket mode*. Otherwise read its file and use it wherever a step says *the tracker file*:

| `codekit.tracker` | Tracker file |
|-------------------|--------------|
| `linear` | [references/linear.md](references/linear.md) |
| `gitlab` | [references/gitlab.md](references/gitlab.md) |

## Workflow

### 1. Preflight

1. **Host CLI:** run the host's logged-in check. If the CLI isn't installed or logged in, stop and give the login from [Code host](#code-host).
2. **Base branch (`<base-branch>`):** use the branch named in the prompt, else `git config codekit.basebranch`. Either one is used without asking. If neither is set, detect it with the host's default-branch command and ask once, with options **Use `<detected>` and save (recommended)** and **Use another branch**. Save the chosen branch with `git config -f .config/.gitconfig codekit.basebranch <branch>` (`--local` if that file doesn't exist), so later runs don't ask.
3. **Branch:** `git branch --show-current` must not be `<base-branch>`. If it is, stop. If it prints nothing, HEAD is detached, usually by a rebase in progress. Stop too. If `git status` shows a rebase in progress, `resolve-conflict` resumes it.
4. **Uncommitted changes:** if `git status --porcelain` isn't empty, list the changed files and ask once, with options **Push only what's committed (recommended)** and **Stop so I can run `/sdd-commit`**. To push only what's committed, stash the changes (`git stash push -u -m "codekit: sdd-push"`) so the rebase and amends leave them out, and restore them in Step 6. Never commit them here.
5. **Commits:** `git rev-list --count origin/<base-branch>..HEAD` must be ≥1. If it's more than one, mention it. That's fine, so don't squash unasked.
6. **Existing PR:** run the host's open-PR command. If an open PR exists, this run is an **update**. Skip creation in Step 4 and refresh the body instead.
7. **Ticket ID (ticket mode):** take it from the branch's commits (`git log --format=%B origin/<base-branch>..HEAD`, newest first), but only from a `[<ID>] ::` subject or a `Ticket:` line (an ID or an issue URL), which `sdd-commit` already checked. Never from elsewhere in a message: a body line like "read files as UTF-8" looks like an ID too. A `Ticket:` URL wins over the subject, because it names the issue's project. Failing that, read the branch name as the tracker file's **Branch** says. If there's no ID, run in no-ticket mode.
8. **Issue (ticket mode):** fetch it once as the tracker file's **Issue** says, and reuse the result in Steps 2 and 4. Step 5 fetches again, after the PR exists. If the tracker says the issue doesn't exist, warn and run in no-ticket mode. If the tracker can't be reached, keep the ID, warn, and expect the tracker steps to fail.

### 2. Summary

Show one summary, then continue without asking. A PR is always opened (or updated), and the target was settled in preflight. It's a draft only when the prompt says so (`--draft`):

```
Source:   <branch>  (<n> commit(s) ahead)
Target:   <base-branch>  (from <config | prompt | just saved>)
Rebase:   onto origin/<base-branch>
Archive:  openspec/changes/<change-id> → openspec/specs/  |  already archived  |  n/a (not OpenSpec)
Docs:     update docs/project/ and amend  |  n/a (tracker keeps them, no docs/project/, or draft)
Push:     git push -u origin <branch>   [--force-with-lease if history was rewritten]
PR:       create into <base-branch>  |  update #<number>  [+ mark ready | + back to draft]   (on <GitHub | GitLab>)
Ticket:   <ticket-id> "<issue title>" → close on merge + move to "<review-state>" + upload spec  |  none
```

The issue title is there so the user can catch a wrong ID before `Fixes` links it.

`<review-state>` comes from the tracker file's **Review state**. If it finds none, show `Ticket: <ticket-id> → close on merge only` and skip the move.

### 3. Rebase, archive, and push

1. Run the `resolve-conflict` skill targeting `<base-branch>`. It fetches, rebases, and walks through any conflicts with the user. Continue only once it completes cleanly. If the user aborts, stop here.
2. **OpenSpec only: archive the change** in this PR, so no follow-up PR is needed. It runs after the rebase, so it builds on every change already archived on `<base-branch>`. See [Archive](#archive) below. Skip it for draft PRs. SpecKit and no-framework specs aren't committed when there's a tracker: the tracker holds them (Step 5), so there's nothing to archive.
3. **Project docs, without a tracker:** only in no-ticket mode because `codekit.tracker` is `none`, and only when `docs/project/product-map.md` exists. Skip it for draft PRs. Run the `project-docs` skill. It runs after the rebase, so it builds on the docs every merged PR left. If it changed `docs/project/`, amend them into the branch's commit (`git add docs/project && git commit --amend --no-edit`), retrying once after a reformatting hook as the archive does.
4. Push:
   - If the branch has no upstream, or the rebase didn't rewrite pushed commits: `git push -u origin HEAD`
   - If pushed history was rewritten by an amend or rebase: `git push --force-with-lease -u origin HEAD`. Say why it's needed. Never use plain `--force`.

#### Archive

OpenSpec only. Run `/opsx:archive <change-id>`, else `openspec archive <change-id> --yes`. It merges the change's spec deltas into `openspec/specs/` and moves the folder to `openspec/changes/archive/<date>-<change-id>/`.

1. **Already archived?** If the change is under `openspec/changes/archive/`, skip. OpenSpec can't archive it again: it finds a change by its active folder, which the archive moved. If the spec has to change after archiving (e.g. after review feedback), ask the user whether to open a new change for it or edit `openspec/specs/` directly in this PR.
2. **Amend** it into the branch's commit (`git add -A openspec && git commit --amend --no-edit`), so the branch keeps one commit. If a pre-commit hook reformats files, run `git add -A openspec` and retry once. On any other failure, show it and stop. The push then needs `--force-with-lease` if the commit was already pushed.

If two PRs that both touch the same capability are open at once, whichever merges second conflicts on `openspec/specs/`. Running `/sdd-push` again rebases, and `resolve-conflict` walks through it.

### 4. Create or update the PR

1. **Body:** use the repo's own template, from the host table, if one exists. Otherwise use [resources/pr-template.md](resources/pr-template.md). Fill it in from:
   - the issue (from preflight, or the conversation)
   - the plan or spec files written by `sdd-plan`
   - `git log origin/<base-branch>..HEAD` and `git diff --stat origin/<base-branch>...HEAD`
   - the latest local review report (`${TMPDIR:-/tmp}/codekit/<repo>/reviews/<branch-name-with-slashes-as-dashes>.md`), if it's still there
2. **Closing line (ticket mode):** the body must include `Fixes <ticket-id>`, written as the tracker file's **Closing line** says. That phrase links the PR to the issue and closes the issue on merge. If the user says the PR only partly addresses the issue, use `Part of <ticket-id>` instead. In no-ticket mode, drop the template's `Fixes` line.
3. **Title:** the commit subject, if there's one commit. Otherwise `[<ticket-id>] :: <issue title>`, or `[TASK] :: <summary of the commits>` in no-ticket mode.
4. **Create** or **update** with the host's commands. On update, change the title only if the user asks. If the PR is ready and the prompt says `--draft`, move it back to draft. If it's a draft and the prompt asks to mark it ready, mark it ready. Otherwise leave its state.
5. Capture `<pr-url>`.

Reviewers: if `git config codekit.reviewers` holds a comma-separated list of usernames on the host, add them on create. Otherwise rely on CODEOWNERS and don't prompt for reviewers.

### 5. Update the ticket (ticket mode only)

Follow the tracker file's **After the PR**: link the PR to the issue if the closing line doesn't already, move the issue to `<review-state>` unless the PR is a draft (draft means the work isn't ready for review), and upload the spec.

**Upload the spec** so the issue this PR closes has the spec, plan, and research as shipped. This is the only point where specs leave your machine: they stay local while you work, where SpecKit expects them. It isn't optional: for SpecKit and no-framework projects the tracker holds the spec's only copy, and the after-merge `codekit-docs` job reads it to build the Decision Log. The plan folder is the one `sdd-plan` named for the ticket. After an OpenSpec archive it's `openspec/changes/archive/<date>-<change-id>/`, so pass that path. Don't prune.

If a tracker call fails, warn and continue. The PR is the deliverable and must not be rolled back.

### 6. Summary

If Step 1 stashed changes, run `git stash pop`, even when an earlier step stopped. If it conflicts, leave the stash in place and say so.

End with the PR URL (created or updated, draft or ready), and anything skipped or failed in the rebase, archive, or ticket steps, including any warning from the tracker file's **Closing line**.

Then add **How to test**: 3 to 5 numbered steps someone who doesn't read code can follow in the app, drawn from the issue, the spec's acceptance criteria, and the diff. Each step is one short sentence saying what to do and what they should see, like "Open Settings and turn on dark mode. The page turns dark." Use the words the app shows on screen, not file, function, or API names. Never more than 5 steps, however much changed: pick the ones a user would notice most, and end with one line naming what's left out, like "Also changed: export and search." If the change has nothing anyone can see, say that in one line instead.
