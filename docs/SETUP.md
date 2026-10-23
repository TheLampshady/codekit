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

`sdd-push` uses `gh` for everything on GitHub: repo defaults, PR create/edit/view. No token is stored by codekit.

### Plugin

Install with the commands in the [README](../README.md#install). Pick **user scope** in Claude Code to have it in every project.

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

### Linear API key

With SpecKit or no framework, specs aren't committed: the Linear issue holds the spec, plan, and research, so the key is **needed** there. With OpenSpec it's optional. Uploading files through the MCP would send every byte through the model, so `linear-docs` and the product docs use small standard-library Python scripts that call Linear's GraphQL API directly. They need a personal API key:

1. In Linear, go to **Settings → Security & access → Personal API keys** and create a key.
2. Export it in your shell profile (`~/.zshrc`, `~/.bashrc`), not in a project file:
   ```bash
   export LINEAR_API_KEY="lin_api_..."
   ```
3. Open a new shell. If the agent's session started before you added the key, the skill runs the script through your shell as a login, interactive shell (`$SHELL -lic`), so the key is still picked up. That shell gets no input, so a profile that prompts for something just skips it.

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
1. **Ask whether the repo uses Linear** (unless `.config/.gitconfig` already says), then **check prerequisites.** These are required, and init stops until they're fixed: `gh` installed and logged in, `uv` installed, and (only if you use Linear) the Linear MCP connected. It runs every check first and reports them together. Also checked, without stopping: a GitHub remote, `LINEAR_API_KEY` (set and accepted by Linear), and `python3`.
2. **Set up an SDD framework.** If the repo has none, it asks you to pick SpecKit, OpenSpec, or none. Then it installs the CLI if needed (`specify` through uv, `openspec` through npm) and runs `specify init` / `openspec init` non-interactively for your agent. If you pick none, `sdd-plan` writes plans by hand, and you can add a framework later by rerunning init.
3. **Ask for settings** that `.config/.gitconfig` doesn't already have: the base branch, the Linear team, the app's Linear project (which you create in Linear first), and (optionally) reviewers.
4. **Install** `.config/.gitconfig`, `.config/.commit-message-template`, and `.config/.pre-commit-config.yaml`, skipping any that exist. If the repo already has a root `.pre-commit-config.yaml` or another hook manager (husky, lefthook), it uses that instead. With Linear and SpecKit or no framework, it gitignores `specs/`, since the Linear issue holds the spec. codekit's own scratch files (review reports, working copies) go in the system temp folder, never the repo.
5. **Wire them in** with `git config --local --add include.path ../.config/.gitconfig`, and install pre-commit.
6. **Write the SDD context:** `.specify/memory/constitution.md` or `openspec/config.yaml`, built from codekit's constitution plus the Project Patterns found in your code. A file you've already filled in is never replaced.
7. **Set up the project docs.** It offers to build them now, which also adds the decisions from specs already merged to the Decision Log. With Linear (and a project picked) it offers the Action that keeps them current. Without Linear, `sdd-push` keeps them current and a pre-push hook warns when they fall behind. See [Project docs](#project-docs) below.

Commit `.config/`, `.gitignore`, the framework files (including the constitution or config), `docs/project/` if built, and `.github/workflows/codekit-docs.yml` if installed, so teammates share them. Each teammate runs `/codekit init` once per clone, which only performs the `include.path` and hook steps. Run it again to add a framework later.

### Project docs

Without Linear, the project docs are files in `docs/project/`, and `sdd-push` updates them inside each PR. Nothing else to set up. The rest of this section is for Linear.

`.github/workflows/codekit-docs.yml` keeps three documents in your Linear project current: the **Product Map** (what the app does and what its data and interfaces support, in product language, each entry linked to code), the **Decision Log** (what was decided and why, from each merged ticket's spec documents), and the **Glossary** (the team's vocabulary, which PMs edit in Linear). PMs read them, ask Linear Agent about the app, and file tickets in the same project. None of that needs a GitHub seat.

How it works: after every PR merged into the base branch, GitHub starts a runner, checks out the repo, installs Claude Code and this plugin, and runs `/codekit:project-docs --ci`. That pulls the current documents from Linear, updates the map for what the new commits changed, adds each merged ticket's decisions from its issue's spec documents, and pushes them back. The map records the commit it was last synced to, so a skipped or failed run is caught up by the next one. A PR that only touches docs, tests, CI config, or lockfiles doesn't start the workflow at all (its `paths-ignore` list, which you can edit). Those changes are covered by the next run. To rebuild from scratch, open the repo's **Actions** tab, pick **codekit project docs**, choose **Run workflow**, and check **full**.

It needs two repository secrets. Set them once in your own terminal (init tells you which are missing):

```bash
claude setup-token                                      # prints a token for your Claude Pro/Max plan
gh secret set CLAUDE_CODE_OAUTH_TOKEN                   # paste the token when prompted
gh secret set LINEAR_API_KEY --body "$LINEAR_API_KEY"   # reuses the key from your profile
```

Runs count against that Claude plan's usage. To use an Anthropic API key instead, change the workflow's `claude_code_oauth_token` line to `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` and set that secret.

## 3. Keeping current

```text
/codekit update      # Claude Code: /codekit:codekit update
```

Run this after updating the plugin, or whenever the tools feel stale. It will:
1. **Run the same prerequisite checks** as init.
2. **Upgrade the tools:** `uv self update`, `specify self upgrade`, `npm install -g @fission-ai/openspec@latest`, `uv tool upgrade pre-commit`, and gh through its package manager. It shows the commands first and runs them on your yes. Tools the repo doesn't use are skipped.
3. **Refresh the framework's project files:** `specify integration upgrade`, which never touches your constitution, or `openspec update`, which leaves `config.yaml` and specs alone. If SpecKit finds files you've edited, it asks before overwriting.
4. **Optionally bump pre-commit hook versions** (`pre-commit autoupdate`), and show the diff.
5. **Re-sync codekit's setup:** missing git wiring and installed files, new `[codekit]` config keys, `.gitignore` lines, principles a newer codekit added to its constitution (appended, never rewritten), and Project Patterns whose cited files have moved.

It ends with a before → after version table and the changed files. Nothing is committed for you.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Skills don't appear | Claude: `claude plugin list`, then `/reload-plugins`. Antigravity CLI: `agy plugin list`. Antigravity IDE: check that `~/.gemini/config/plugins/codekit/plugin.json` exists, then restart. |
| "Linear tools not available" | The MCP isn't authenticated. Run `/mcp` (Claude) or open the MCP panel (Antigravity). |
| `sdd-push`: "gh: not logged in" | `gh auth login` |
| Issue didn't move to In Review | codekit looks for a *started*-type state with "review" in its name. If the team has none, it only links the PR. Add one in Linear, or let the GitHub integration's automations move it. Draft PRs never move it. |
| SpecKit created a `001-…` branch | Its optional `git` extension is enabled. See [extensions/speckit.md](extensions/speckit.md#branches). |
