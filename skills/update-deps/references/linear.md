# Linear

Through the bundled Linear MCP. Use the team from `git config codekit.team`. If that's unset, call `list_teams`, ask once, and offer to save it with `git config -f .config/.gitconfig codekit.team <team-key>` (`--local` if that file doesn't exist).

1. Call `list_issues` with that `team` and the title as `query`. If an open issue with the same title exists, reuse it.
2. Otherwise call `save_issue` with `team`, `project` (from `git config codekit.project`, if set), `title`, and `description`.
3. If the branch name carries a Linear ID (`[A-Za-z][A-Za-z0-9]+-\d+`, uppercased) whose prefix is the team key, or that `get_issue` finds, pass it as `relatedTo`. Version numbers match the same pattern, and a `relatedTo` that doesn't exist fails the whole filing.
