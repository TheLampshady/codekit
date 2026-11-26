# Linear

Issues and the project docs live in Linear, through the bundled Linear MCP (OAuth) and a personal API key for the docs scripts. The code can be on GitHub or GitLab.

## Checks

**Required:**

| Check | Command | If missing |
|-------|---------|------------|
| Linear MCP | Is a Linear tool (e.g. `list_teams`) available? | Claude Code: `/mcp` → authenticate `linear`. Antigravity: the MCP panel → sign in to `linear`. `sdd-plan` can't fetch issues without it. |

**Optional:**

| Check | Command | If missing |
|-------|---------|------------|
| Linear API key | `python3 <plugin>/skills/linear-docs/scripts/linear_docs.py --check`, run the way [linear-docs](../../linear-docs/SKILL.md) runs its script: directly when `LINEAR_API_KEY` is in the environment, else through `"$SHELL" -lic '…' </dev/null`. It prints the key owner and workspace, or why the key failed. It never prints the key itself. | **Needed for SpecKit and no-framework projects**, where the Linear issue holds the spec, so flag it prominently (it isn't a blocker, since the framework may not be chosen yet): `sdd-push` uploads it at PR time, and the `codekit-docs` job reads it. Also used by `project-docs`. For OpenSpec it's optional. Give the steps from [docs/SETUP.md](../../../docs/SETUP.md#linear-api-key): create a personal key in Linear (**Settings → Security & access → Personal API keys**) and `export LINEAR_API_KEY=...` in the shell profile. If Linear rejects it (401), the key was revoked or mistyped. Never read the key yourself, ask for it, or write it to a file. If the workspace it reports isn't the one the Linear MCP is signed in to, point that out. |

## Settings

Init Step 3 asks for these, in the same message as the base branch. Both are optional.

- **Team** (`codekit.team`): call `list_teams` and offer the teams. Scopes `sdd-plan next`, guards the docs script against other teams' issues, and is where `update-deps` files issues.
- **Project** (`codekit.project`): the project this app's tickets and docs live in. Call `list_projects` (scoped to the team, if one was picked), offer them by name, and store the chosen project's **ID**. The user creates the project in Linear; never create one. If they don't have it yet, leave it empty: `/codekit update` asks again while it's empty.

## Project docs

Documents in the Linear project, so skip init Step 7 while `codekit.project` is empty, and say `/codekit update` offers it once it's set. The first build needs the API key check above to pass.

The `codekit-docs` job keeps them current. On top of the Claude login, it needs one more secret:

| Secret | How the user sets it |
|--------|----------------------|
| `LINEAR_API_KEY` | GitHub: `gh secret set LINEAR_API_KEY --body "$LINEAR_API_KEY"`. GitLab: `printf %s "$LINEAR_API_KEY" \| glab variable set LINEAR_API_KEY --masked --protected`. Both reuse the key already exported in their profile. |
