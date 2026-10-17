# Setup

A one-time setup for each machine, then for each project.

## 1. Machine

### GitHub CLI

```bash
# macOS
brew install gh
# Debian/Ubuntu: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
gh auth login            # choose GitHub.com, HTTPS, and authenticate in the browser
gh auth status           # verify
```

`sdd-pr` uses `gh` for everything on GitHub: repo defaults, PR create/edit/view. No token is stored by codekit.

### Plugin

| Where | Install |
|-------|---------|
| Claude Code (session) | `/plugin install codekit --marketplace TheLampshady/codekit`, then choose **user scope** |
| Claude Code (shell) | `claude plugin install codekit --marketplace TheLampshady/codekit` |
| Antigravity CLI | `agy plugin install https://github.com/TheLampshady/codekit` |
| Antigravity IDE | `git clone https://github.com/TheLampshady/codekit.git ~/.gemini/config/plugins/codekit`, then restart. The IDE loads plugins from that folder and has no marketplace. |

Check it's installed: `claude plugin list` or `agy plugin list`. In Claude Code, typing `/codekit:` lists the skills.

To keep codekit current in Claude Code, enable auto-update for `codekit-marketplace` under `/plugin` → **Marketplaces** (it's off by default for marketplaces outside Anthropic's), or run `claude plugin update codekit@codekit-marketplace`.

### Linear MCP

The plugin bundles Linear's hosted MCP server (`https://mcp.linear.app/mcp`) in `.mcp.json` (Claude) and `mcp_config.json` (Antigravity). It authenticates with OAuth, so there's no API key to manage.

| Client | Connect |
|--------|---------|
| Claude Code | Run `/mcp`, select **linear**, and authenticate in the browser |
| Antigravity | Open the MCP servers panel → **linear** → sign in |

Check it works by asking: *"list my Linear issues"*.

The skills use these Linear tools: `get_issue`, `list_issues`, `list_comments`, `list_issue_statuses`, `list_teams`, `save_issue`, and `save_comment`.

### Context7 MCP

Also bundled: Context7 (`https://mcp.context7.com/mcp`) serves current, version-specific library documentation. `sdd-plan` uses it to check the APIs a plan relies on, and `sdd-implement` uses it before writing code against a library. It works with no setup. If you hit rate limits, get a free key at [context7.com](https://context7.com) and add it to your client's MCP config for `context7`. Don't put the key in this repo's `.mcp.json`.

### Linear API key (optional, for `linear-docs`)

Uploading spec files through the MCP would send every byte of every file through the model. `linear-docs` avoids that with a small standard-library Python script that calls Linear's GraphQL API directly. The script needs a personal API key:

1. In Linear, go to **Settings → Security & access → Personal API keys** and create a key.
2. Export it in your shell profile (`~/.zshrc`, `~/.bashrc`), not in a project file:
   ```bash
   export LINEAR_API_KEY="lin_api_..."
   ```
3. Open a new shell. The skill runs the script through `bash -lc`, so the key is picked up even in a session that started before you added it.

4. Verify it: `/codekit init` and `/codekit update` both check the key and report, for example:
   ```
   LINEAR_API_KEY ok: Jane Doe <jane@example.com> in Acme (linear.app/acme)
   ```

The agent never reads or prints the key. `--check` prints only the key owner and workspace. With `git config codekit.linear-team` set, the script refuses issues on other teams.

### Linear ↔ GitHub integration (recommended)

In Linear: **Settings → Integrations → GitHub**. Connect your org and enable the repos. Then:

- Branches and PRs containing an issue identifier (`ENG-123`) are linked automatically.
- `Fixes ENG-123` in a PR body closes the issue on merge.
- Workflow automations move issues on PR open, review, and merge.

codekit uses Linear's `gitBranchName` for branches and writes `Fixes <ID>` into PR bodies, so it works with the integration rather than duplicating it.

## 2. Project

In the project repo, run:

```text
/codekit init        # Claude Code: /codekit:codekit init
```

It will:
1. **Check prerequisites.** These are required, and init stops until they're fixed: `gh` installed and logged in, the Linear MCP connected, and `uv` installed. It runs every check first and reports them together. Also checked, without stopping: a GitHub remote, `LINEAR_API_KEY` (set and accepted by Linear), and `python3`.
2. **Set up an SDD framework.** If the repo has none, it asks you to pick SpecKit, OpenSpec, or none. Then it installs the CLI if needed (`specify` through uv, `openspec` through npm) and runs `specify init` / `openspec init` non-interactively for your agent. If you pick none, `sdd-plan` writes plans by hand, and you can add a framework later by rerunning init.
3. **Ask for settings:** the base branch, the Linear team, and (optionally) reviewers.
4. **Install** `.config/.gitconfig`, `.config/.commit-message-template`, and `.config/.pre-commit-config.yaml`, skipping any that exist, and add `.codekit/` to `.gitignore`.
5. **Wire them in** with `git config --local --add include.path ../.config/.gitconfig`, and install pre-commit.
6. **Write the SDD context:** `.specify/memory/constitution.md` or `openspec/config.yaml`, built from codekit's constitution plus the Project Patterns found in your code. A file you've already filled in is never replaced.

Commit `.config/`, `.gitignore`, and the framework files (including the constitution or config) so teammates share them. Each teammate runs `/codekit init` once per clone, which only performs the `include.path` and hook steps. Run it again to add a framework later.

## 3. Keeping current

```text
/codekit update      # Claude Code: /codekit:codekit update
```

Run this after updating the plugin, or whenever the tools feel stale. It will:
1. **Run the same prerequisite checks** as init.
2. **Upgrade the tools:** `uv self update`, `specify self upgrade`, `npm install -g @fission-ai/openspec@latest`, `uv tool upgrade pre-commit`, and gh through its package manager. It shows the commands first and runs them on your yes. Tools the repo doesn't use are skipped.
3. **Refresh the framework's project files:** `specify integration upgrade`, which never touches your constitution, or `openspec update`, which leaves `config.yaml` and specs alone. If SpecKit finds files you've edited, it asks before overwriting.
4. **Optionally bump pre-commit hook versions** (`pre-commit autoupdate`), and show the diff.
5. **Re-sync codekit's setup:** missing git wiring, new `[codekit]` config keys, `.gitignore` lines, principles a newer codekit added to its constitution (appended, never rewritten), and Project Patterns whose cited files have moved.

It ends with a before → after version table and the changed files. Nothing is committed for you.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Skills don't appear | Claude: `claude plugin list`, then `/reload-plugins`. Antigravity CLI: `agy plugin list`. Antigravity IDE: check that `~/.gemini/config/plugins/codekit/plugin.json` exists, then restart. |
| "Linear tools not available" | The MCP isn't authenticated. Run `/mcp` (Claude) or open the MCP panel (Antigravity). |
| `sdd-pr`: "gh: not logged in" | `gh auth login` |
| Issue didn't move to In Review | codekit looks for a *started*-type state with "review" in its name. If the team has none, it only links the PR. Add one in Linear, or let the GitHub integration's automations move it. Draft PRs never move it. |
| SpecKit created a `001-…` branch | Its optional `git` extension is enabled. See [extensions/speckit.md](extensions/speckit.md#branches). |
