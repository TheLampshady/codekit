# GitLab

Through the `glab` CLI, run from the repo root. There `glab` works on the project and host the `origin` remote points at, so gitlab.com, a self-managed domain, and an IP address all work the same. For an issue in another project, add `-R <group/project>` to each `glab issue` command, and put `projects/<group%2Fproject>` in place of `projects/:fullpath` in each `glab api` path.

## IDs

| Form | Example | `<ticket-id>` | `<ticket-slug>` |
|------|---------|---------------|-----------------|
| Reference | `#123` | `#123` | `123` |
| Full reference | `group/app#123` | `#123` if `group/app` is this project, else `group/app#123` | `123`, or `app-123` for another project |
| URL | `https://<host>/group/app/-/issues/123` (or `/-/work_items/123`) | as the full reference | as the full reference |

The `#` matters: a bare number is an ID only when the user calls it an issue ("issue 123"). If `glab issue view` returns 404, it was only text shaped like an ID.

## Next

`glab api "issues?scope=assigned_to_me&state=opened&per_page=50"` lists the open issues assigned to the user in every project they can see. Show this project's first (`references.full` names each issue's project), then the rest with their full reference. Leave out issues that already carry the board's in-progress or review label (see **Start**). Free and CE have no priority field, so order by due date, then milestone due date, then most recently updated.

## Fetch

1. `glab issue view <n> --output json`: keep `title`, `description`, `web_url`, `state`, `assignees`, `labels`, and `milestone`.
2. `glab api "projects/:fullpath/issues/<n>/notes?sort=asc&per_page=100"`: the comments. Skip notes with `"system": true`, which are GitLab's own activity entries.

## Start

GitLab has no workflow states on Free or CE: an issue is open or closed, and a board's columns are labels. Read the columns from the board: `glab api "projects/:fullpath/boards"` returns each board with its `lists` in order, each with a `label.name`. Use the first board.

1. **In-progress column:** the first list whose label contains "progress", "doing", or "wip" (case-insensitive), else one containing "develop". If there's none, or more than one fits equally well, skip the move and say so.
2. If the issue already has that label, or the label of a list after it, it's started: skip the move. If `state` is `closed`, ask before reopening it (`glab issue reopen <n>`).
3. **Move:** `glab issue update <n> --label "<in-progress label>" --unlabel "<the issue's other board-list labels>"`, so it leaves its old column.
4. **Assign:** if `assignees` is empty, `glab issue update <n> --assignee "+<username>"`, with `<username>` from `glab api user`.

## Branch

1. **An existing branch:** if a branch whose last path segment starts with `<n>-` already exists, locally (`git branch --list`) or on the remote (`git ls-remote --heads origin`), GitLab or a teammate made it for this issue: use it. If there are several, ask which.
2. **Otherwise,** build it. The title slug is the title in lowercase, each run of other characters turned into `-`, trimmed, at most 50 characters.
   - If the project's branch name template (`issue_branch_template` in `glab api projects/:fullpath`) ends in `%{id}-%{title}`, alone or after a prefix such as `feature/`, follow it, so the team's convention holds: `%{id}` is the issue number, `%{title}` the title slug.
   - With any other template, or none, use GitLab's default, `<n>-<title-slug>`. Later skills read the issue number from the start of the branch name's last segment, so it has to lead.
   - For an issue in another project, use `<ticket-slug>-<title-slug>` (`app-123-add-login`), because a bare number in this project's branch names means this project's issue.

## Comment

Post one comment from stdin:

```bash
glab issue note <n> <<'EOF'
<filled template>
EOF
```

To add a changed requirement to the description, append it to the description from **Fetch** and write the whole text back with `glab issue update <n> --description-file -` (same heredoc). Keep everything that was there.

## Errors

- **`glab` missing:** install it (`brew install glab`, or see [gitlab.com/gitlab-org/cli](https://gitlab.com/gitlab-org/cli#installation)).
- **Not logged in to this host:** have the user run `! glab auth login --hostname <host>`, with `<host>` from `git remote get-url origin`. That works for self-managed hosts and IP addresses too.
- **404:** the number is wrong, or the issue is in a project the user can't see.

After telling the user, stop and offer to continue on the local path with pasted ticket text instead.
