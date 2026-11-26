# Linear

Through the bundled Linear MCP.

## Branch

A Linear identifier (`[A-Za-z][A-Za-z0-9]+-\d+`) in the branch name, uppercased, but only if the part before the `-` is the `git config codekit.team` key or, with no team key set, `get_issue` finds it. Version numbers and dates match the same pattern (`feature/upgrade-node-20` → `NODE-20`).

## Issue

`get_issue` with `fields: ["title", "description", "team", "status", "statusType"]`.

## Review state

`list_issue_statuses` for the issue's team: the `started`-type state whose name contains "review" (case-insensitive), e.g. *In Review* or *Code Review*. If there's none, or there are several and none is plainly the right one, there's no review state.

## Closing line

`Fixes ENG-123`. Linear's GitHub and GitLab integrations use that phrase to link the PR and close the issue on merge.

## After the PR

Linear's GitHub or GitLab integration, when installed, already attaches the PR and moves the issue on its own. These steps fill in for it when it isn't, and they're safe to run when it is.

1. `get_issue` with `fields: ["attachments", "status"]`. If `<pr-url>` isn't among the attachments, call `save_issue` with `id: <ticket-id>` and `links: [{ url: <pr-url>, title: "PR #<number>: <title>" }]`.
2. Unless the PR is a draft, if the status isn't already `<review-state>` (or a later state), call `save_issue` with `state: <review-state>`.
3. **Upload the spec:** run the `linear-docs` skill on the plan folder with `--issue <ticket-id>`. It needs `LINEAR_API_KEY`. If no key is set, warn that the Decision Log will miss this ticket.
