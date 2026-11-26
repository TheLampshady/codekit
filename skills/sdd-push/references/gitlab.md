# GitLab

Through the `glab` CLI, run from the repo root, so it works on the project the `origin` remote points at. For an issue in another project (`group/app#123`), add `-R group/app` to each `glab issue` command and put `projects/group%2Fapp` in place of `projects/:fullpath` in each `glab api` path. GitLab issues assume the code is on GitLab too.

## Branch

The issue number that starts the branch name's last path segment, followed by `-` (`123-add-login` → `#123`), but only if `glab issue view <n> --output json` finds the issue and the rest of the segment is the start of its title's slug (lowercase, other characters turned into `-`). A leading number alone proves little (`404-page`), and the PR would close that issue on merge. If the issue exists but the title doesn't match, run in no-ticket mode and say why in the summary.

## Issue

`glab issue view <n> --output json`: `title`, `description`, `state`, `labels`, and `web_url`.

## Review state

The board's review column. `glab api "projects/:fullpath/boards"` returns each board with its `lists` in order, each with a `label.name`. On the first board, it's the list whose label contains "review" (case-insensitive). If there's none, or there are several and none is plainly the right one, there's no review state.

## Closing line

`Fixes #123`, or `Fixes group/app#123` for another project's issue. GitLab links the merge request to the issue from that phrase, and closes the issue when the request merges into the project's **default** branch. If `<base-branch>` isn't the default branch (`default_branch` in `glab repo view --output json`), warn in the summary that the issue won't close on merge.

## After the PR

1. The closing line already links the merge request to the issue, so there's nothing to attach.
2. Unless the PR is a draft, and the issue doesn't already have the review label: `glab issue update <n> --label "<review label>" --unlabel "<the issue's other board-list labels>"`.
3. **Upload the spec:** run the `wiki-docs` skill on the plan folder. It puts the spec in the project wiki, under `specs/<folder>/`, through git.
