---
name: codekit
description: 'Set up and maintain a repository for the codekit workflow. init: requires gh, the Linear MCP, and uv; offers to install and initialize SpecKit or OpenSpec; installs the commit template, pre-commit, and shared codekit git config; writes the SpecKit constitution or OpenSpec config.yaml. update: upgrades uv, specify, openspec, pre-commit, and gh, refreshes the framework''s project files, and re-syncs codekit''s config and constitution with the current plugin. Never overwrites existing files. Use when asked to: initialize the project, set up codekit, set up this repo, update codekit, update or upgrade the tools, upgrade speckit/openspec/uv, refresh the framework, write or update the constitution, set up the OpenSpec config.'
user-invocable: true
disable-model-invocation: true
argument-hint: "[init | update]"
---

# codekit

Sets up a repo so that `sdd-plan` → `sdd-implement` → `sdd-commit` → `sdd-pr` run without prompting for configuration, and keeps the tools and generated files current afterwards. Both modes are safe to re-run: they skip what's already in place and never overwrite a file.

Resources and references live next to this file. Resolve [resources/](resources/) and [references/](references/) relative to this `SKILL.md`, not the user's repo. The plugin root (`<plugin>`) is two folders up.

## Choose the mode

| Argument | Mode |
|----------|------|
| `init` | [references/init.md](references/init.md) |
| `update` | [references/update.md](references/update.md) |
| none | **init** if the repo isn't set up yet (no `.config/.gitconfig` with a `[codekit]` section, or `git config codekit.basebranch` is empty). Otherwise **update**. Say which mode was picked and why. |

The user can also ask for one piece directly. *"Write the constitution"* or *"set up the OpenSpec context"* runs only init Step 6, through [references/sdd-context.md](references/sdd-context.md). *"Upgrade speckit"* runs only that tool's row in update Step 2.

## Prerequisites (both modes)

Run **every** check first, then report them all in one table, so the user can fix everything in one pass instead of one problem at a time.

**Required.** If any of these fail, stop after the report. Don't continue until the user says they're fixed, then re-run only the failed checks.

| Check | Command | If missing |
|-------|---------|------------|
| Git repo | `git rev-parse --show-toplevel` | Offer `git init`. |
| gh CLI, logged in | `gh --version` and `gh auth status` | Install gh: `brew install gh`, or see [cli.github.com](https://cli.github.com/). Then run `! gh auth login`. `sdd-pr` can't open PRs without it. |
| Linear MCP | Is a Linear tool (e.g. `list_teams`) available? | Claude Code: `/mcp` → authenticate `linear`. Antigravity: the MCP panel → sign in to `linear`. `sdd-plan` can't fetch issues without it. |
| uv | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` or `brew install uv`, then open a new shell. Installs SpecKit and pre-commit. |

**Optional.** Report these and continue:

| Check | Command | If missing |
|-------|---------|------------|
| GitHub remote | `git remote get-url origin` | Note it. `sdd-pr` will need one before the first PR. |
| Linear API key | `bash -lc 'python3 <plugin>/skills/linear-docs/scripts/linear_docs.py --check'`. It prints the key owner and workspace, or why the key failed. It never prints the key itself. | Only `linear-docs` needs it. Give the steps from [docs/SETUP.md](../../docs/SETUP.md#linear-api-key-optional-for-linear-docs): create a personal key in Linear (**Settings → Security & access → Personal API keys**) and `export LINEAR_API_KEY=...` in the shell profile. If Linear rejects it (401), the key was revoked or mistyped. Never read the key yourself, ask for it, or write it to a file. If the workspace it reports isn't the one the Linear MCP is signed in to, point that out. |
| python3 ≥ 3.10 | `python3 --version` | Only `linear-docs` needs it. |

## Rules (both modes)

- **Never overwrite.** Skip a file that exists, or append to it. Treat a framework's unfilled template as missing.
- **Confirm before installing or upgrading anything.** Show the exact commands as one batch and run them on a yes.
- **Never commit.** End with `git status --short` and tell the user what to review and commit.
