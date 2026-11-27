# AGENTS.md

Guidance for coding agents working in this repository. This is the only context file: Claude Code (v2.1.277 and later) and Antigravity both read `AGENTS.md`. **Don't add a `CLAUDE.md` or `GEMINI.md`.** If Claude Code finds a `CLAUDE.md`, it reads that instead of this file, and two files means two places to drift.

## What This Repo Is

codekit is a **Claude Code + Antigravity plugin** that runs spec-driven development from a ticket (a Linear or GitLab issue) to a pull request (on GitHub) or merge request (on GitLab). The core loop is four skills: `sdd-plan` → `sdd-implement` → `sdd-commit` → `sdd-push`. They're backed by `codekit` (the setup hub, with `init` and `update` modes), `project-docs` (the Product Map, Decision Log, and Glossary, for PMs), `code-review-local`, `resolve-conflict`, `linear-docs`, and `wiki-docs`. `update-deps` sits beside the loop: it upgrades a project's dependencies and files follow-up features as issues.

External systems, and how each one is reached:
- **Trackers**, one per repo, picked by `codekit.tracker` (`linear`, `gitlab`, or `none`). A skill that touches the tracker keeps each tracker's calls in its own `references/<tracker>.md` (`sdd-plan`, `sdd-commit`, `sdd-push`, `update-deps`, `codekit`), and its `SKILL.md` names steps, not tools, so only the active tracker loads. Adding a tracker means one such file per skill, a docs home in `project-docs` and `collect_git.sh`, and its value in the README and `docs/USAGE_FLOW.md` tables.
- **Linear**, via the hosted Linear MCP (`https://mcp.linear.app/mcp`, OAuth), bundled in `.mcp.json` and `mcp_config.json`. Skills call tools by name: `get_issue`, `list_issues`, `list_comments`, `list_issue_statuses`, `list_teams`, `list_projects`, `save_issue`, `save_comment`.
  **Exception:** bulk document reads and writes go through the scripts in `skills/linear-docs/scripts/`: `linear_docs.py` (a spec folder's spec, plan, and research ↔ issue documents) and `project_docs.py` (the project docs ↔ Linear project documents, which imports from `linear_docs.py`). They call Linear's GraphQL API with `LINEAR_API_KEY`, because sending file contents through the MCP costs their full size in tokens. Keep both standard-library only and safe to re-run (they match documents by title and compare words). Large writes to Linear go through a script; small ones go through the MCP.
- **GitLab**, via the `glab` CLI only, run from the repo root so it works on the project and host `origin` points at: gitlab.com, self-managed by domain or IP address, any tier, Community Edition included. There's no GitLab MCP: its URL differs per instance, so it can't be bundled, and older or locked-down instances don't offer it. Workflow states are the board's label columns, read from the board lists API each run. Specs and project docs live in the project's wiki, which is a git repo next to the code, so `skills/wiki-docs/scripts/wiki_docs.py` syncs them with plain git and the login that already reaches the code (`CODEKIT_WIKI_TOKEN` in CI). Keep it standard-library only and safe to re-run. GitLab issues assume the code is on GitLab too.
- **Code in the repo, prose in the tracker.** With a tracker, in SpecKit and no-framework projects, `codekit init` gitignores `specs/`: specs stay local while working (SpecKit expects them there), `sdd-push` uploads the decision-bearing files to the tracker at PR time (the Linear issue, or the GitLab wiki), and the after-merge CI job turns them into the project's Decision Log. Don't add steps that commit spec text, and don't re-implement what SpecKit already does: codekit skills orchestrate. OpenSpec is the exception, because its living spec is committed by design.
- **Code hosts**: GitHub via the `gh` CLI only (no GitHub MCP), GitLab via `glab`. The host comes from `origin` on every run and is never configured: `github.com` and `gitlab.com` by name, any other host by whichever CLI is logged in to it. `codekit init` can install one CI job into a project that runs `/codekit:project-docs --ci` after each merge: the GitHub Action `codekit-docs.yml` (through `anthropics/claude-code-action`), or the GitLab job `codekit-docs.gitlab-ci.yml` (headless `claude -p --plugin-dir`). Both fetch this plugin when they run, so a change to `project-docs` reaches every project on its next run.
- **Google Drive** (optional): when `codekit.drive` names a folder, CI copies the project docs there as Google Docs, for people who can't open the tracker or the repo. They read them through their own Claude Drive connector. `skills/project-docs/scripts/drive_docs.py` does the copy, from a plain step after Claude in `codekit-docs`, or without a tracker from the `codekit-drive` job (`codekit-drive.yml`, `codekit-drive.gitlab-ci.yml`), which runs no Claude. It logs in with one OAuth refresh token stored as CI secrets, so it works the same for any Google account and both code hosts, and never runs on a developer's machine. The copy is one-way: nothing reads Drive back. Docs are found by title in the folder and replaced whole, so their links don't change. Keep the script standard-library only.
- **Library docs**, via the Context7 MCP (`https://mcp.context7.com/mcp`, no auth), bundled next to Linear. `sdd-plan` (plan phase) and `update-deps` call `resolve-library-id` → `query-docs` rather than relying on memory. Skills state a tool instruction once, where it matters, and never repeat it in another step.
- **SDD frameworks**: SpecKit (detected by `.specify/`) and OpenSpec (detected by `openspec/`), with a manual fallback when neither is present.

There's no build system and no compiled code: Markdown and JSON only. **The deliverable is prose an agent will execute**, so a change to a `SKILL.md` is a behavior change.

## Directory Map

| Path | Purpose |
|------|---------|
| `skills/<name>/SKILL.md` | Skill entry point: frontmatter plus numbered workflow steps |
| `skills/<name>/resources/` | Templates the skill fills in (commit message, PR body, issue comment, `.gitconfig`, the `codekit-docs` and `codekit-drive` CI jobs, the Product Map, Decision Log, and Glossary) |
| `skills/<name>/scripts/` | Executables a skill runs by absolute path from the project root (`linear-docs`, `wiki-docs`, and `project-docs`' `collect_git.sh`, which gathers git input so the `codekit-docs` job needs no `git` in its allowlist, and `drive_docs.py`, which the CI jobs run to copy the docs to Google Drive) |
| `skills/<name>/references/` | Detail that `SKILL.md` links to and loads only when that step runs (e.g. `codekit/references/init.md`, `update.md`, `sdd-context.md`, one per mode or step), and `<tracker>.md`, one tracker's calls for that skill |
| `skills/codekit/SKILL.md` | The hub. It holds only mode routing, the shared prerequisite checks, and the shared rules. A new step goes in the mode's reference file, not here. If init gains a new installed file or config key, `update` Step 5 must re-sync it too. |
| `skills/project-docs/` | **The project docs**: docs for people who don't read the code, kept current from it. Today that's the Product Map, Decision Log, and Glossary. They live where the tickets do: the Linear project, the GitLab wiki, or `docs/project/` with no tracker. A new project doc gets a template in `resources/` whose first `# ` heading is its title (Linear and the wiki name documents by it), its own step in `SKILL.md`, and a line in the get and publish steps. |
| `skills/codekit/resources/principles.md` | **The principles baseline**, the single source for both the SpecKit constitution and the condensed OpenSpec context. Change a principle here and in `openspec-config.yaml`'s one-line summary together. Rules only, no code blocks, so the constitution stays under 300 lines with Project Patterns: the WRONG/CORRECT examples go in `principles-examples.md`, which init installs as `docs/PRINCIPLES-EXAMPLES.md`. Stack-specific rules don't belong here; they're generated per project as Project Patterns. |
| `.claude-plugin/` | Claude `plugin.json` + `marketplace.json` |
| `pm/` | **The `codekit-board` plugin** (Claude only), a second plugin in the same marketplace declared only in `marketplace.json` (`strict: false`, own `version`), with no `plugin.json` of its own (don't add one: Cowork rejects the root plugin when it finds a nested manifest) and no bundled MCP (PMs connect their board in the UI). Its skills live in `pm/skills/<name>/`. Kept out of the root `skills/` because everything there is the developer plugin's and follows the `disable-model-invocation` rule; a PM skill must trigger on plain questions. Same rule applies: no company-specific content. |
| `plugin.json` | Antigravity manifest (`{"name": "codekit"}`). A different file and schema from Claude's. Don't merge them. Antigravity is two products, the IDE (installed by placing the folder in `~/.gemini/config/plugins/`) and the `agy` CLI (`agy plugin install`), with the same plugin contents. Its global config stays under `~/.gemini/`. Don't "correct" that path to `~/.agents/`. |
| `.mcp.json` / `mcp_config.json` | Claude / Antigravity MCP config (Linear, Context7). Keep them identical. |
| `rules/` | Antigravity always-on rules (guidance, not enforcement) |
| `docs/` | Setup, usage flow, SDD framework guides |
| `.config/` | This repo's own pre-commit config and commit template |

## Commands

Users install from GitHub with the commands in the README's install section, the single place they're written. The `make` targets are for developing codekit from a checkout. They install this working copy, so edits show up without a release:

```bash
make setup        # hooks + Antigravity + Claude plugin, all from this checkout
make claude       # register this checkout as a local marketplace and install from it
make antigravity  # Antigravity IDE symlink (live reload) + agy CLI install from this path
make status       # install status + gh/glab/uv/specify/openspec/LINEAR_API_KEY
make check        # pre-commit on all files
```

The marketplace name `codekit-marketplace` (`.claude-plugin/marketplace.json`) appears in users' install and update commands. Don't rename it.

There's no test suite. Verify a skill by installing the plugin and running it against a real repo with a real issue, on each tracker it touches.

## Conventions

- **Config lives in git config** under the `codekit.*` namespace (`basebranch`, `tracker`, `team`, `project`, `reviewers`, `drive`; `team` and `project` are Linear's). **A tracker is optional:** with `codekit.tracker = none`, every tracker step is skipped, specs stay committed, and the project docs live in `docs/project/`. A new tracker step goes in each tracker's `references/<tracker>.md`, never inline in `SKILL.md`. Prefer detecting a value over configuring it: workflow states and board columns are read from the tracker (`list_issue_statuses`, GitLab's board lists), the code host and the GitLab project from `origin`, and an issue's project from its reference. A new setting goes there and into the tables in `README.md` and `docs/USAGE_FLOW.md`, not into a new file.
- **Ticket IDs** are the tracker's own: Linear identifiers matched with `[A-Za-z][A-Za-z0-9]+-\d+` and uppercased, GitLab's `#123` (or `group/app#123` for another project). Each tracker file also gives the `<ticket-slug>` that prefixes branch and spec folder names (`eng-123`, `123`). Branches are Linear's `gitBranchName`, or the GitLab project's branch name template. Commits carry `[<ID>] ::` in the subject and a `Ticket: <url>` line, which later skills read the ticket from. PR bodies carry `Fixes <ID>`, which Linear, GitLab, and GitHub all treat as closing the issue.
- **Tracker writes are idempotent and non-blocking** in `sdd-push`: check before attaching or moving, warn on failure, and never roll back a PR because the tracker failed.
- **No client- or company-specific content.** No internal tool names, hosts, or emails. This is the generic kit.
- **Skill frontmatter:** `name`, `description` (under 1024 characters, with "Use when asked to:" triggers), `user-invocable: true`, an optional `argument-hint`, and `disable-model-invocation: true` on the user-run skills (`codekit`, `sdd-plan`, `sdd-implement`, `sdd-commit`, `sdd-push`, `update-deps`), which keeps their descriptions out of Claude Code's context until the user runs them. Skills that other skills start (`linear-docs`, `wiki-docs`, `code-review-local`, `project-docs`, `resolve-conflict`) set it to `false`. Except `resolve-conflict`, their descriptions are one or two sentences, name the skills that start them, and skip the "Use when asked to:" triggers, so they stay small in context and don't match everyday requests. Antigravity reads only `name` and `description` and ignores the rest, so the descriptions still have to work as triggers there.
- **Skill-to-skill hand-offs:** the parent runs a `false` child by name: *"run the `linear-docs` skill"*. Reading another skill's `SKILL.md` by path is a file-tool read in the plugin cache, outside the working directory, which prompts, or fails under `blockReadsOutsideWorkingDirectories`. The one exception is `sdd-commit`, which stays `true`: its callers read [../sdd-commit/SKILL.md](../sdd-commit/SKILL.md) and follow it. Skills reference their own resources by relative path.
- **Forked skills:** `code-review-local`, `linear-docs`, and `wiki-docs` set `context: fork` (with `agent: general-purpose` and `background: false`). In Claude Code, running them as `/name` starts an isolated subagent with no conversation history. Their instructions must stand alone, and they never stop to ask: a needed decision is returned to the caller (`linear-docs` § Decisions). Antigravity ignores these fields and runs them inline.
- Version bumps touch `.claude-plugin/plugin.json` and `pyproject.toml`. The PM plugin versions on its own, in its `marketplace.json` entry.

## Extra Rules

1. No tombstones. No "previous versions...".
2. Edit skills here, not in an installed copy.
3. NEVER commit without asking
