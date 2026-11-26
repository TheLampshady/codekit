# Setup

A one-time setup for each machine, then for each project.

## 1. Machine

### Code host CLI

Install the CLI for wherever your code lives. codekit picks it from each repo's `origin` remote, so a machine can have both.

**GitHub:**
```bash
brew install gh          # Debian/Ubuntu: https://github.com/cli/cli/blob/trunk/docs/install_linux.md
gh auth login            # choose GitHub.com (or your GitHub Enterprise host), HTTPS, and authenticate in the browser
gh auth status           # verify
```

**GitLab**, on gitlab.com or your own instance, including Community Edition and hosts reached by IP address:
```bash
brew install glab        # other systems: https://gitlab.com/gitlab-org/cli#installation
glab auth login --hostname gitlab.example.com   # your host, or gitlab.com
glab auth status --hostname gitlab.example.com  # verify
```

`sdd-push` uses it for the pull or merge request: repo defaults, create, edit, view. With GitLab issues, `glab` also reads and updates the issues. No token is stored by codekit.

### Plugin

Install with the commands in the [README](../README.md#install). Pick **user scope** in Claude Code to have it in every project.

Check it's installed: `claude plugin list` or `agy plugin list`. In Claude Code, typing `/codekit:` lists the skills.

To keep codekit current in Claude Code, enable auto-update for `codekit-marketplace` under `/plugin` → **Marketplaces** (it's off by default for marketplaces outside Anthropic's), or run `claude plugin update codekit@codekit-marketplace`.

### Linear MCP (with Linear)

The plugin bundles Linear's hosted MCP server (`https://mcp.linear.app/mcp`) in `.mcp.json` (Claude) and `mcp_config.json` (Antigravity). It authenticates with OAuth, so there's no API key to manage.

| Client | Connect |
|--------|---------|
| Claude Code | Run `/mcp`, select **linear**, and authenticate in the browser |
| Antigravity | Open the MCP servers panel → **linear** → sign in |

Check it works by asking: *"list my Linear issues"*.

The skills use these Linear tools: `get_issue`, `list_issues`, `list_comments`, `list_issue_statuses`, `list_teams`, `save_issue`, and `save_comment`.

### Context7 MCP

Also bundled: Context7 (`https://mcp.context7.com/mcp`) serves current, version-specific library documentation. `sdd-plan` uses it to check the APIs a plan relies on, and `sdd-implement` uses it before writing code against a library. It works with no setup. If you hit rate limits, get a free key at [context7.com](https://context7.com) and add it to your client's MCP config for `context7`. Don't put the key in this repo's `.mcp.json`.

### Linear API key (with Linear)

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

The agent never reads or prints the key. `--check` prints only the key owner and workspace. With `git config codekit.team` set, the script refuses issues on other teams.

### GitLab wiki (with GitLab issues)

With GitLab issues, the specs and the project docs live in the project's wiki. A GitLab wiki is a git repo next to the code, so `wiki-docs` and `project-docs` reach it through git with the login you already use for the code: there's no key to create. `/codekit init` checks that it can reach the wiki. If it can't, turn the wiki on (**Settings → General → Visibility, project features, permissions → Wiki**). A wiki that has never had a page may need its first one created in the browser (**Plan → Wiki → Create your first page**).

Board columns aren't configured. codekit reads them from the project's first issue board: the column whose label contains "progress", "doing", or "wip" is *In Progress*, and the one with "review" is *In Review*. Without such columns, issues are only assigned, linked, and closed on merge.

### Linear ↔ GitHub or GitLab integration (recommended with Linear)

In Linear: **Settings → Integrations → GitHub** (or **GitLab**). Connect your org and enable the repos. Then:

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
1. **Ask where the repo's tickets live** (Linear, GitLab issues, or none, unless `.config/.gitconfig` already says), then **check prerequisites.** These are required, and init stops until they're fixed: your code host's CLI (`gh` or `glab`) installed and logged in, `uv` installed, and (only if you use Linear) the Linear MCP connected. It runs every check first and reports them together. Also checked, without stopping: an `origin` remote, `LINEAR_API_KEY` with Linear (set and accepted), the wiki with GitLab issues, and `python3`.
2. **Set up an SDD framework.** If the repo has none, it asks you to pick SpecKit, OpenSpec, or none. Then it installs the CLI if needed (`specify` through uv, `openspec` through npm) and runs `specify init` / `openspec init` non-interactively for your agent. If you pick none, `sdd-plan` writes plans by hand, and you can add a framework later by rerunning init.
3. **Ask for settings** that `.config/.gitconfig` doesn't already have: the base branch, (optionally) reviewers, and with Linear the team and the app's Linear project (which you create in Linear first). GitLab needs no settings: everything comes from the remote and the board.
4. **Install** `.config/.gitconfig`, `.config/.commit-message-template`, and `.config/.pre-commit-config.yaml`, skipping any that exist. If the repo already has a root `.pre-commit-config.yaml` or another hook manager (husky, lefthook), it uses that instead. With a tracker and SpecKit or no framework, it gitignores `specs/`, since the tracker holds the spec. codekit's own scratch files (review reports, working copies) go in the system temp folder, never the repo.
5. **Wire them in** with `git config --local --add include.path ../.config/.gitconfig`, and install pre-commit.
6. **Write the SDD context:** `.specify/memory/constitution.md` or `openspec/config.yaml`, built from codekit's constitution plus the Project Patterns found in your code. A file you've already filled in is never replaced.
7. **Set up the project docs.** It offers to build them now, which also adds the decisions from specs already merged to the Decision Log. With a tracker it offers the CI job that keeps them current. Without one, `sdd-push` keeps them current and a pre-push hook warns when they fall behind. See [Project docs](#project-docs) below.

Commit `.config/`, `.gitignore`, the framework files (including the constitution or config), `docs/project/` if built, and the CI job's files if installed (`.github/workflows/codekit-docs.yml`, or `.gitlab/ci/codekit-docs.yml` and `.gitlab-ci.yml`), so teammates share them. Each teammate runs `/codekit init` once per clone, which only performs the `include.path` and hook steps. Run it again to add a framework later.

### Project docs

Without a tracker, the project docs are files in `docs/project/`, and `sdd-push` updates them inside each PR. Nothing else to set up. The rest of this section is for Linear and GitLab issues.

The `codekit-docs` CI job keeps three documents current where your tickets live: the **Product Map** (what the app does and what its data and interfaces support, in product language, each entry linked to code), the **Decision Log** (what was decided and why, from each merged ticket's spec), and the **Glossary** (the team's vocabulary, which PMs edit where it lives). With Linear they're documents in your Linear project, so PMs can read them, ask Linear Agent about the app, and file tickets there without a code-host seat. With GitLab issues they're pages in the project's wiki, next to the board.

How it works: after every merge into the base branch, a CI runner checks out the repo, fetches Claude Code and this plugin, and first runs the plugin's `collect_git.sh`, so Claude needs no `git` permission, then runs `/codekit:project-docs --ci --git-dir …`. That pulls the current documents, updates the map for what the new commits changed, adds each merged ticket's decisions from its spec, and pushes them back. The map records the commit it was last synced to, so a skipped or failed run is caught up by the next one. A merge that only touches docs, tests, CI config, or lockfiles is skipped (GitHub: the workflow's `paths-ignore` list; GitLab: the same list in the job's script). Those changes are covered by the next run. The job fails unless the log ends with `CODEKIT-RESULT: published <sha>`; a `blocked` line gives the reason.

**GitHub** (with Linear): `.github/workflows/codekit-docs.yml`. To rebuild from scratch, open the repo's **Actions** tab, pick **codekit project docs**, choose **Run workflow**, and check **full**. It needs two repository secrets. Set them once in your own terminal (init tells you which are missing):

```bash
claude setup-token                                      # prints a token for your Claude Pro/Max plan
gh secret set CLAUDE_CODE_OAUTH_TOKEN                   # paste the token when prompted
gh secret set LINEAR_API_KEY --body "$LINEAR_API_KEY"   # reuses the key from your profile
```

To use an Anthropic API key instead, change the workflow's `claude_code_oauth_token` line to `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` and set that secret.

**GitLab** (with GitLab issues or Linear): `.gitlab/ci/codekit-docs.yml`, included from `.gitlab-ci.yml`, which also gives it a regular stage: GitLab creates no pipeline whose only jobs are in `.post`, and after a merge it's often the only job. If your pipeline has `workflow: rules:`, they must let push pipelines run on the base branch. To rebuild from scratch, run a pipeline for the base branch (**Build → Pipelines → Run pipeline**) with the variable `CODEKIT_FULL` set to `true`. It needs two CI/CD variables, masked and protected, so only protected branches such as the base branch can read them. Set them once in your own terminal:

```bash
claude setup-token        # prints a token for your Claude Pro/Max plan; then paste it here:
read -rs t && printf %s "$t" | glab variable set CLAUDE_CODE_OAUTH_TOKEN --masked --protected; unset t

# GitLab issues: a token that can push to the wiki (a CI job's own token can't).
# Create a project access token (Settings → Access tokens, role Developer, scope
# write_repository), or a personal access token on gitlab.com's Free tier. Paste it here:
read -rs t && printf %s "$t" | glab variable set CODEKIT_WIKI_TOKEN --masked --protected; unset t

# Linear: reuses the key from your profile.
printf %s "$LINEAR_API_KEY" | glab variable set LINEAR_API_KEY --masked --protected
```

To use an Anthropic API key instead, set `ANTHROPIC_API_KEY` in place of `CLAUDE_CODE_OAUTH_TOKEN`. The runner needs to reach npm, the Anthropic API, and github.com, where it fetches this plugin. If it can't reach github.com, set the job's `CODEKIT_PLUGIN_REPO` variable to a mirror of the plugin. On an instance with a self-signed certificate, the job trusts the runner's own CA.

Runs count against that Claude plan's usage.

## 3. Keeping current

```text
/codekit update      # Claude Code: /codekit:codekit update
```

Run this after updating the plugin, or whenever the tools feel stale. It will:
1. **Run the same prerequisite checks** as init.
2. **Upgrade the tools:** `uv self update`, `specify self upgrade`, `npm install -g @fission-ai/openspec@latest`, `uv tool upgrade pre-commit`, and gh or glab through its package manager. It shows the commands first and runs them on your yes. Tools the repo doesn't use are skipped.
3. **Refresh the framework's project files:** `specify integration upgrade`, which never touches your constitution, or `openspec update`, which leaves `config.yaml` and specs alone. If SpecKit finds files you've edited, it asks before overwriting.
4. **Optionally bump pre-commit hook versions** (`pre-commit autoupdate`), and show the diff.
5. **Re-sync codekit's setup:** missing git wiring and installed files, new `[codekit]` config keys, `.gitignore` lines, principles a newer codekit added to its constitution (appended, never rewritten), and Project Patterns whose cited files have moved.

It ends with a before → after version table and the changed files. Nothing is committed for you.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Skills don't appear | Claude: `claude plugin list`, then `/reload-plugins`. Antigravity CLI: `agy plugin list`. Antigravity IDE: check that `~/.gemini/config/plugins/codekit/plugin.json` exists, then restart. |
| "Linear tools not available" | The MCP isn't authenticated. Run `/mcp` (Claude) or open the MCP panel (Antigravity). |
| `sdd-push`: "not logged in" | `gh auth login`, or `glab auth login --hostname <host>` |
| A self-managed host isn't recognized | codekit tells GitHub from GitLab by which CLI is logged in to the remote's host. Run `glab auth status --hostname <host>` (or `gh auth status --hostname <host>`) to see which one is. |
| Issue didn't move to In Review | Linear: codekit looks for a *started*-type state with "review" in its name. If the team has none, it only links the PR. Add one in Linear, or let the integration's automations move it. GitLab: it looks for a column on the project's first board whose label contains "review". Draft PRs never move it. |
| GitLab issue didn't close on merge | GitLab closes issues from `Fixes #123` only when the merge request targets the project's default branch. `sdd-push` warns when the base branch isn't it. |
| `wiki-docs`: can't reach the wiki | Turn the project's wiki on, check that you can push to the code, and for a brand-new wiki create its first page in the browser. In CI, check that `CODEKIT_WIKI_TOKEN` is set and the base branch is protected. |
| SpecKit created a `001-…` branch | Its optional `git` extension is enabled. See [extensions/speckit.md](extensions/speckit.md#branches). |
