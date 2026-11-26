# Linear

Through the bundled Linear MCP (`https://mcp.linear.app/mcp`).

## IDs

- **Reference:** an identifier matching `[A-Za-z][A-Za-z0-9]+-\d+` (`ENG-123`, `eng-123`). `<ticket-id>` is the identifier, uppercased.
- **URL:** `linear.app/<workspace>/issue/<ID>/...`. `<ticket-id>` is the `<ID>` path segment.
- **`<ticket-slug>`:** the identifier lowercased (`eng-123`).
- If `get_issue` can't find it, it was only text shaped like an ID.

## Next

Call `list_issues` with `assignee: "me"`, `state: "unstarted"`, and `fields: ["title", "priority", "status"]`, so descriptions aren't fetched for every issue. If `git config codekit.team` is set, pass it as `team`. If `git config codekit.project` is set, pass it as `project`. Order by priority, Urgent first and No priority last (Linear numbers it 0). If nothing is returned, retry with `state: "backlog"`.

## Fetch

Call `get_issue` with the `<ticket-id>`. Keep `title`, `description`, `url`, `gitBranchName`, `status`, `team`, `assignee`, `labels`, `project`, and `attachments`. Call `list_comments` for the issue as well.

## Start

1. If the issue is already in a `started`-type state, skip the move. If it's `completed` or `canceled`, ask before reopening it. Otherwise call `list_issue_statuses` for the issue's team and take the first state whose type is `started`, which is "In Progress" on most teams.
2. Call `save_issue` with `id: <ticket-id>`, `state: <that state>`, and `assignee: "me"` if it is unassigned.
3. If `git config codekit.team` is unset, offer to save the issue's team key: `git config -f .config/.gitconfig codekit.team <team-key>`, so the team shares it (`--local` if that file doesn't exist). The `next` flow uses it.

## Branch

`<branch-name>` is the issue's `gitBranchName`, used verbatim. That's deliberate: Linear's GitHub and GitLab integrations link any branch or PR that contains the identifier, and move the issue through its workflow automatically.

## Comment

Call `save_comment` with `issueId: <ticket-id>` and the filled template as `body`. To add a changed requirement to the description, call `save_issue` with `patch` and `append`.

## Errors

- **Not connected or tools missing:** in Claude Code, have the user run `/mcp` and authenticate `linear`. In Antigravity, have them open the MCP servers panel and sign in to `linear`.
- **401 / expired:** re-authenticate the same way.
- **Issue not found:** confirm the identifier and that the user's workspace can see the team.

After telling the user, stop and offer to continue on the local path with pasted ticket text instead.
