---
name: codekit
description: 'Set up and maintain a repo for the codekit workflow. init: picks the tracker (Linear, GitLab issues, or none), checks gh or glab, uv, and the tracker; installs SpecKit or OpenSpec, the commit template, pre-commit, and shared git config; writes the constitution or OpenSpec config. update: upgrades the tools, refreshes the framework''s files, and re-syncs codekit''s config and constitution. Also sets up the project docs (see project-docs). Never overwrites files. Use when asked to: initialize the project, set up codekit or this repo, update codekit, upgrade the tools or speckit/openspec/uv, refresh the framework, write or update the constitution, set up the OpenSpec config, set up the project docs or their CI job.'
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

The user can also ask for one piece directly. *"Write the constitution"* or *"set up the OpenSpec context"* runs only init Step 6, through [references/sdd-context.md](references/sdd-context.md). *"Set up the project docs"* or *"set up the docs CI job"* runs only init Step 7. *"Upgrade speckit"* runs only that tool's row in update Step 2.

## Prerequisites

`init` and `update` run every check below.

**Tracker.** Read `git config -f .config/.gitconfig codekit.tracker`. Only if it's unset, ask where the repo's tickets live, recommending GitLab when the code host (below) is GitLab, and Linear otherwise:
- **Linear**
- **GitLab issues**, in the GitLab project the code is in
- **None:** work from spec files or pasted text. Specs and the project docs stay committed in the repo.

Then read the tracker's file for its checks, settings, and project docs: [references/linear.md](references/linear.md) for `linear`, [references/gitlab.md](references/gitlab.md) for `gitlab`. With `none`, skip every tracker row.

**Code host.** `<host>` is the host in `git remote get-url origin` (`https://<host>/…`, `git@<host>:…`, `ssh://git@<host>:<port>/…`). `github.com` is GitHub, which uses `gh`, and `gitlab.com` is GitLab, which uses `glab`. For any other host, a domain or an IP address, it's GitLab if `glab auth status --hostname <host>` succeeds, and GitHub (Enterprise) if `gh auth status --hostname <host>` does. If neither does, ask once whether `<host>` is GitLab or GitHub. The answer only picks which CLI to check below, so don't save it. With no `origin` remote yet, skip the host CLI row and note it.

Run **every** check first, then report them all in one table, so the user can fix everything in one pass instead of one problem at a time.

**Required.** If any of these fail, stop after the report. Don't continue until the user says they're fixed, then re-run only the failed checks.

| Check | Command | If missing |
|-------|---------|------------|
| Git repo | `git rev-parse --show-toplevel` | Offer `git init`. |
| Host CLI, logged in | GitHub: `gh --version` and `gh auth status --hostname <host>`. GitLab: `glab --version` and `glab auth status --hostname <host>`. | Install it: `brew install gh` or [cli.github.com](https://cli.github.com/); `brew install glab` or [gitlab.com/gitlab-org/cli](https://gitlab.com/gitlab-org/cli#installation). Then `! gh auth login --hostname <host>` or `! glab auth login --hostname <host>`, which works for self-managed hosts and IP addresses too. `sdd-push` can't open a pull or merge request without it. |
| The tracker's required checks | From the tracker file | From the tracker file |
| uv | `uv --version` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` or `brew install uv`, then open a new shell. Installs SpecKit and pre-commit. |

**Optional.** Report these and continue:

| Check | Command | If missing |
|-------|---------|------------|
| `origin` remote | `git remote get-url origin` | Note it. `sdd-push` needs one before the first PR, and it decides the code host. |
| The tracker's optional checks | From the tracker file | From the tracker file |
| python3 ≥ 3.10 | `python3 --version` | Runs the docs scripts (`linear-docs`, `wiki-docs`), so it's needed wherever the tracker holds the specs and docs. |

## Rules

- **Never overwrite.** Skip a file that exists, or append to it. Treat a framework's unfilled template as missing. The project docs are the exception: [project-docs](../project-docs/SKILL.md) regenerates the Product Map and follows its own rules.
- **Confirm before installing or upgrading anything.** Show the exact commands as one batch and run them on a yes.
- **Never commit.** End with `git status --short` and tell the user what to review and commit.
