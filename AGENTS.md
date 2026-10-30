# AGENTS.md

Guidance for coding agents working in this repository. This is the only context file: Claude Code (v2.1.277 and later) and Antigravity both read `AGENTS.md`. **Don't add a `CLAUDE.md` or `GEMINI.md`.** If Claude Code finds a `CLAUDE.md`, it reads that instead of this file, and two files means two places to drift.

## What This Repo Is

codekit is a **Claude Code + Antigravity plugin** that runs spec-driven development from a Linear issue to a GitHub PR. The core loop is four skills: `sdd-plan` → `sdd-implement` → `sdd-commit` → `sdd-push`. They're backed by `codekit` (the setup hub, with `init` and `update` modes), `project-docs` (the Product Map, Decision Log, and Glossary, for PMs), `code-review-local`, `resolve-conflict`, and `linear-docs`. `update-deps` sits beside the loop: it upgrades a project's dependencies and files follow-up features as Linear issues.

External systems, and how each one is reached:
- **Linear**, via the hosted Linear MCP (`https://mcp.linear.app/mcp`, OAuth), bundled in `.mcp.json` and `mcp_config.json`. Skills call tools by name: `get_issue`, `list_issues`, `list_comments`, `list_issue_statuses`, `list_teams`, `list_projects`, `save_issue`, `save_comment`.
  **Exception:** bulk document reads and writes go through the scripts in `skills/linear-docs/scripts/`: `linear_docs.py` (a spec folder's spec, plan, and research ↔ issue documents) and `project_docs.py` (the project docs ↔ Linear project documents, which imports from `linear_docs.py`). They call Linear's GraphQL API with `LINEAR_API_KEY`, because sending file contents through the MCP costs their full size in tokens. Keep both standard-library only and safe to re-run (they match documents by title and compare words). Large writes to Linear go through a script; small ones go through the MCP.
- **Code in GitHub, prose in Linear.** In SpecKit and no-framework projects, `codekit init` gitignores `specs/`: specs stay local while working (SpecKit expects them there), `sdd-push` uploads the decision-bearing files to the Linear issue at PR time, and the post-merge Action turns them into the project's Decision Log. Don't add steps that commit spec text, and don't re-implement what SpecKit already does: codekit skills orchestrate. OpenSpec is the exception, because its living spec is committed by design.
- **GitHub**, via the `gh` CLI only. There's no GitHub MCP. `codekit init` can install one GitHub Action into a project, `codekit-docs.yml`, which runs `/codekit:project-docs --ci` after each merge using `anthropics/claude-code-action`. It installs this plugin from the marketplace, so a change to `project-docs` reaches every project on its next run.
- **Library docs**, via the Context7 MCP (`https://mcp.context7.com/mcp`, no auth), bundled next to Linear. `sdd-plan` (plan phase) and `update-deps` call `resolve-library-id` → `query-docs` rather than relying on memory. Skills state a tool instruction once, where it matters, and never repeat it in another step.
- **SDD frameworks**: SpecKit (detected by `.specify/`) and OpenSpec (detected by `openspec/`), with a manual fallback when neither is present.

There's no build system and no compiled code: Markdown and JSON only. **The deliverable is prose an agent will execute**, so a change to a `SKILL.md` is a behavior change.

## Directory Map

| Path | Purpose |
|------|---------|
| `skills/<name>/SKILL.md` | Skill entry point: frontmatter plus numbered workflow steps |
| `skills/<name>/resources/` | Templates the skill fills in (commit message, PR body, Linear comment, `.gitconfig`, the `codekit-docs.yml` workflow, the Product Map, Decision Log, and Glossary) |
| `skills/<name>/scripts/` | Executables a skill runs by absolute path from the project root (`linear-docs`, and `project-docs`' `collect_git.sh`, which gathers git input so the `codekit-docs` Action needs no `git` in its allowlist) |
| `skills/<name>/references/` | Detail that `SKILL.md` links to and loads only when that step runs (e.g. `codekit/references/init.md`, `update.md`, `sdd-context.md`, one per mode or step) |
| `skills/codekit/SKILL.md` | The hub. It holds only mode routing, the shared prerequisite checks, and the shared rules. A new step goes in the mode's reference file, not here. If init gains a new installed file or config key, `update` Step 5 must re-sync it too. |
| `skills/project-docs/` | **The project docs**: docs for people who don't read the code, kept current from it. Today that's the Product Map, Decision Log, and Glossary. They live in the Linear project, or in `docs/project/` with `codekit.linear = false`. A new project doc gets a template in `resources/` whose first `# ` heading is its title (Linear matches documents by title), its own step in `SKILL.md`, and a line in the get and publish steps. |
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
make status       # install status + gh/uv/specify/openspec/LINEAR_API_KEY
make check        # pre-commit on all files
```

The marketplace name `codekit-marketplace` (`.claude-plugin/marketplace.json`) appears in users' install and update commands. Don't rename it.

There's no test suite. Verify a skill by installing the plugin and running it against a real repo with a real Linear issue.

## Conventions

- **Config lives in git config** under the `codekit.*` namespace (`basebranch`, `linear`, `linear-team`, `linear-project`, `reviewers`). **Linear is optional:** with `codekit.linear = false`, every Linear step is skipped, specs stay committed, and the project docs live in `docs/project/`. A new Linear step must honor that flag. Linear workflow states are never configured: skills read them from the team with `list_issue_statuses`. A new setting goes there and into the tables in `README.md` and `docs/USAGE_FLOW.md`, not into a new file.
- **Ticket IDs** are Linear identifiers matched with `[A-Za-z][A-Za-z0-9]+-\d+` and uppercased. Branches are Linear's `gitBranchName`, unchanged. PR bodies carry `Fixes <ID>` (Linear's magic word).
- **Linear writes are idempotent and non-blocking** in `sdd-push`: check before attaching or moving, warn on failure, and never roll back a PR because Linear failed.
- **No client- or company-specific content.** No internal tool names, hosts, or emails. This is the generic kit.
- **Skill frontmatter:** `name`, `description` (under 1024 characters, with "Use when asked to:" triggers), `user-invocable: true`, an optional `argument-hint`, and `disable-model-invocation: true` on every skill except `resolve-conflict`. That flag keeps a skill's description out of Claude Code's context until the user runs it. Antigravity reads only `name` and `description` and ignores the rest, so the descriptions still have to work as triggers there.
- **Skill-to-skill hand-offs:** a skill with `disable-model-invocation` can't be started by Claude, even from inside another skill. So the parent reads the child's file and follows it: *"read [../code-review-local/SKILL.md](../code-review-local/SKILL.md) and follow it"*. Only `resolve-conflict` may be called by name. Skills reference their own resources by relative path.
- **Forked skills:** `code-review-local` and `linear-docs` set `context: fork` (with `agent: general-purpose` and `background: false`). In Claude Code, running them as `/name` starts an isolated subagent with no conversation history. Their instructions must stand alone, and they never stop to ask: a needed decision is returned to the caller (`linear-docs` § Decisions). A hand-off that reads the file runs inline, not forked, so `sdd-commit` starts a subagent explicitly for the review. Antigravity ignores these fields and runs both inline.
- Version bumps touch `.claude-plugin/plugin.json` and `pyproject.toml`. The PM plugin versions on its own, in its `marketplace.json` entry.

## Extra Rules

1. No tombstones. No "previous versions...".
2. Edit skills here, not in an installed copy.
3. NEVER commit without asking
