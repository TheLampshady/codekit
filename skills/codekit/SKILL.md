---
name: codekit
description: 'Set up and maintain a repo for the codekit workflow. init: checks gh, uv, and (optionally) Linear; installs SpecKit or OpenSpec, the commit template, pre-commit, and shared git config; writes the constitution or OpenSpec config. update: upgrades the tools, refreshes the framework''s files, and re-syncs codekit''s config and constitution. Also sets up the project docs (see project-docs). Never overwrites files. Use when asked to: initialize the project, set up codekit or this repo, update codekit, upgrade the tools or speckit/openspec/uv, refresh the framework, write or update the constitution, set up the OpenSpec config, set up the project docs or their GitHub Action.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[init | update]"
---

# codekit

Sets up a repo so that `sdd-plan` → `sdd-implement` → `sdd-commit` → `sdd-push` run without prompting for configuration, and keeps the tools and generated files current afterwards. `init` and `update` are safe to re-run: they skip what's already in place and never overwrite a file. The project docs are their own skill, [project-docs](../project-docs/SKILL.md): `init` offers their first build and sets up what keeps them current.

Resources and references live next to this file. Resolve [resources/](resources/) and [references/](references/) relative to this `SKILL.md`, not the user's repo. The plugin root (`<plugin>`) is two folders up.

## Choose the mode

| Argument | Mode |
|----------|------|
| `init` | [references/init.md](references/init.md) |
| `update` | [references/update.md](references/update.md) |
| none | **init** if the repo isn't set up yet (no `.config/.gitconfig` with a `[codekit]` section, or `git config codekit.basebranch` is empty). Otherwise **update**. Say which mode was picked and why. |

The user can also ask for one piece directly. *"Write the constitution"* or *"set up the OpenSpec context"* runs only init Step 6, through [references/sdd-context.md](references/sdd-context.md). *"Set up the project docs"* or *"set up the docs Action"* runs only init Step 7. *"Upgrade speckit"* runs only that tool's row in update Step 2.

## Prerequisites

`init` and `update` run every check below.

**Linear is optional.** codekit works from a Linear issue, a spec file, or pasted text. Before running the checks, read `git config -f .config/.gitconfig codekit.linear`. Only if it's unset, ask: *"Use Linear with this repo?"* With **no** (`codekit.linear = false`), skip the Linear MCP and Linear API key rows entirely.

Run **every** check first, then report them all in one table, so the user can fix everything in one pass instead of one problem at a time.

**Required.** If any of these fail, stop after the report. Don't continue until the user says they're fixed, then re-run only the failed checks.

| Check | Command | If missing |
|-------|---------|------------|
| Git repo | `git rev-parse --show-toplevel` | Offer `git init`. |
| gh CLI, logged in | `gh --version` and `gh auth status` | Install gh: `brew install gh`, or see [cli.github.com](https://cli.github.com/). Then run `! gh auth login`. `sdd-push` can't open PRs without it. |
| Linear MCP (if using Linear) | Is a Linear tool (e.g. `list_teams`) available? | Claude Code: `/mcp` → authenticate `linear`. Antigravity: the MCP panel → sign in to `linear`. `sdd-plan` can't fetch issues without it. |
| uv | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` or `brew install uv`, then open a new shell. Installs SpecKit and pre-commit. |

**Optional.** Report these and continue:

| Check | Command | If missing |
|-------|---------|------------|
| GitHub remote | `git remote get-url origin` | Note it. `sdd-push` will need one before the first PR. |
| Linear API key (if using Linear) | `python3 <plugin>/skills/linear-docs/scripts/linear_docs.py --check`, run the way [linear-docs](../linear-docs/SKILL.md) runs its script: directly when `LINEAR_API_KEY` is in the environment, else through `"$SHELL" -lic '…' </dev/null`. It prints the key owner and workspace, or why the key failed. It never prints the key itself. | **Needed for SpecKit and no-framework projects**, where the Linear issue holds the spec, so flag it prominently (it isn't a blocker, since the framework may not be chosen yet): `sdd-push` uploads it at PR time, and the `codekit-docs` Action reads it. Also used by `project-docs`. For OpenSpec it's optional. Give the steps from [docs/SETUP.md](../../docs/SETUP.md#linear-api-key): create a personal key in Linear (**Settings → Security & access → Personal API keys**) and `export LINEAR_API_KEY=...` in the shell profile. If Linear rejects it (401), the key was revoked or mistyped. Never read the key yourself, ask for it, or write it to a file. If the workspace it reports isn't the one the Linear MCP is signed in to, point that out. |
| python3 ≥ 3.10 | `python3 --version` | Runs the `linear-docs` scripts, so it's needed wherever the Linear API key is. |

## Rules

- **Never overwrite.** Skip a file that exists, or append to it. Treat a framework's unfilled template as missing. The project docs are the exception: [project-docs](../project-docs/SKILL.md) regenerates the Product Map and follows its own rules.
- **Confirm before installing or upgrading anything.** Show the exact commands as one batch and run them on a yes.
- **Never commit.** End with `git status --short` and tell the user what to review and commit.
