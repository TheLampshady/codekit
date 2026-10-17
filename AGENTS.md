# AGENTS.md

Guidance for coding agents working in this repository. This is the only context file: Claude Code (v2.1.277 and later) and Antigravity both read `AGENTS.md`. **Don't add a `CLAUDE.md` or `GEMINI.md`.** If Claude Code finds a `CLAUDE.md`, it reads that instead of this file, and two files means two places to drift.

## What This Repo Is

codekit is a **Claude Code + Antigravity plugin** that runs spec-driven development from a Linear issue to a GitHub PR. The core loop is four skills: `sdd-plan` → `sdd-implement` → `sdd-commit` → `sdd-pr`. They're backed by `codekit` (the setup hub, with `init` and `update` modes), `code-review-local`, `resolve-conflict`, and `linear-docs`. `update-deps` sits beside the loop: it upgrades a project's dependencies and files follow-up features as Linear issues.

External systems, and how each one is reached:
- **Linear**, via the hosted Linear MCP (`https://mcp.linear.app/mcp`, OAuth), bundled in `.mcp.json` and `mcp_config.json`. Skills call tools by name: `get_issue`, `list_issues`, `list_comments`, `list_issue_statuses`, `list_teams`, `save_issue`, `save_comment`.
  **Exception:** bulk document uploads go through `skills/linear-docs/scripts/linear_docs.py`, which calls Linear's GraphQL API with `LINEAR_API_KEY`, because sending file contents through the MCP costs their full size in tokens. Keep that script standard-library only and safe to re-run (it matches documents by title and compares words). Large writes to Linear go through a script; small ones go through the MCP.
- **GitHub**, via the `gh` CLI only. There's no GitHub MCP.
- **Library docs**, via the Context7 MCP (`https://mcp.context7.com/mcp`, no auth), bundled next to Linear. `sdd-plan` (plan phase), `sdd-implement`, and `update-deps` call `resolve-library-id` → `query-docs` rather than relying on memory.
- **SDD frameworks**: SpecKit (detected by `.specify/`) and OpenSpec (detected by `openspec/`), with a manual fallback when neither is present.

There's no build system and no compiled code: Markdown and JSON only. **The deliverable is prose an agent will execute**, so a change to a `SKILL.md` is a behavior change.

## Directory Map

| Path | Purpose |
|------|---------|
| `skills/<name>/SKILL.md` | Skill entry point: frontmatter plus numbered workflow steps |
| `skills/<name>/resources/` | Templates the skill fills in (commit message, PR body, Linear comment, `.gitconfig`) |
| `skills/<name>/scripts/` | Executables a skill runs by absolute path from the project root (`linear-docs` only) |
| `skills/<name>/references/` | Detail that `SKILL.md` links to and loads only when that step runs (e.g. `codekit/references/init.md`, `update.md`, `sdd-context.md`, one per mode or step) |
| `skills/codekit/SKILL.md` | The hub. It holds only mode routing, the prerequisite checks both modes share, and the shared rules. A new step goes in the mode's reference file, not here. If init gains a new installed file or config key, `update` Step 5 must re-sync it too. |
| `skills/codekit/resources/principles.md` | **The principles baseline**, the single source for both the SpecKit constitution and the condensed OpenSpec context. Change a principle here and in `openspec-config.yaml`'s one-line summary together. Stack-specific rules don't belong here; they're generated per project as Project Patterns. |
| `.claude-plugin/` | Claude `plugin.json` + `marketplace.json` |
| `plugin.json` | Antigravity manifest (`{"name": "codekit"}`). A different file and schema from Claude's. Don't merge them. Antigravity is two products, the IDE (installed by placing the folder in `~/.gemini/config/plugins/`) and the `agy` CLI (`agy plugin install`), with the same plugin contents. Its global config stays under `~/.gemini/`. Don't "correct" that path to `~/.agents/`. |
| `.mcp.json` / `mcp_config.json` | Claude / Antigravity MCP config (Linear, Context7). Keep them identical. |
| `rules/` | Antigravity always-on rules (guidance, not enforcement) |
| `docs/` | Setup, usage flow, SDD framework guides |
| `.config/` | This repo's own pre-commit config and commit template |

## Commands

Users install from GitHub: `/plugin install codekit --marketplace TheLampshady/codekit` (Claude Code), `agy plugin install https://github.com/TheLampshady/codekit` (Antigravity CLI). Keep the README's install section on those commands. The `make` targets are for developing codekit from a checkout. They install this working copy, so edits show up without a release:

```bash
make setup        # hooks + Antigravity + Claude plugin, all from this checkout
make claude       # register this checkout as a local marketplace and install from it
make antigravity  # Antigravity IDE symlink (live reload) + agy CLI install from this path
make status       # install status + gh/uv/specify/openspec/LINEAR_API_KEY
make check        # pre-commit on all files
```

The marketplace name `codekit-marketplace` (`.claude-plugin/marketplace.json`) appears in users' install and update commands. Don't rename it.

There's no test suite. Verify a skill by installing the plugin and running it against a real repo with a real Linear issue.

## Conventions

- **Config lives in git config** under the `codekit.*` namespace (`basebranch`, `linear-team`, `reviewers`). Linear workflow states are never configured: skills read them from the team with `list_issue_statuses`. A new setting goes there and into the tables in `README.md` and `docs/USAGE_FLOW.md`, not into a new file.
- **Ticket IDs** are Linear identifiers matched with `[A-Za-z][A-Za-z0-9]+-\d+` and uppercased. Branches are Linear's `gitBranchName`, unchanged. PR bodies carry `Fixes <ID>` (Linear's magic word).
- **Linear writes are idempotent and non-blocking** in `sdd-pr`: check before attaching or moving, warn on failure, and never roll back a PR because Linear failed.
- **No client- or company-specific content.** No internal tool names, hosts, or emails. This is the generic kit.
- **Skill frontmatter:** `name`, `description` (under 1024 characters, with "Use when asked to:" triggers), `user-invocable: true`, an optional `argument-hint`, and `disable-model-invocation: true` on every skill except `resolve-conflict`. That flag keeps a skill's description out of Claude Code's context until the user runs it. Antigravity reads only `name` and `description` and ignores the rest, so the descriptions still have to work as triggers there.
- **Skill-to-skill hand-offs:** a skill with `disable-model-invocation` can't be started by Claude, even from inside another skill. So the parent reads the child's file and follows it: *"read [../code-review-local/SKILL.md](../code-review-local/SKILL.md) and follow it"*. Only `resolve-conflict` may be called by name. Skills reference their own resources by relative path.
- **Forked skills:** `code-review-local` and `linear-docs` set `context: fork` (with `agent: general-purpose` and `background: false`). In Claude Code, running them as `/name` starts an isolated subagent with no conversation history. Their instructions must stand alone, and they never stop to ask: a needed decision is returned to the caller (`linear-docs` § Decisions). A hand-off that reads the file runs inline, not forked, so `sdd-commit` starts a subagent explicitly for the review. Antigravity ignores these fields and runs both inline.
- Version bumps touch `.claude-plugin/plugin.json` and `pyproject.toml`.

## Extra Rules

1. No tombstones. No "previous versions...".
2. Edit skills here, not in an installed copy.
3. NEVER commit without asking
