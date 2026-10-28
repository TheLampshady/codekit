# codekit

> Spec-driven development from Linear issue to GitHub pull request, as a plugin for **Claude Code** and **Antigravity**.

codekit gives your coding agent four skills that run the daily loop: pick up a Linear issue, plan it with SpecKit or OpenSpec, implement it, commit it, and open the PR. The Linear issue stays in sync the whole way.

```
 Linear issue ──► /sdd-plan ──► /sdd-implement ──► /sdd-commit ──► /sdd-push ──► GitHub PR ──► merge
                   │ branch        │ tasks + code     │ commit +       │ rebase, push,            │ codekit-docs Action
                   │ In Progress   │ converge         │ local review   │ PR, In Review            │ Product Map, Decision Log,
                   └ spec (local)  │ tests + lint                    └ spec → issue             └ Glossary in Linear
```

Code goes in GitHub, prose goes in Linear. With SpecKit (or no framework), spec folders stay local while you work, where SpecKit expects them, and are gitignored. At PR time the spec, plan, and research go to the Linear issue, so PRs show code only. After merge, the decisions are pulled into the project's Decision Log, kept for reference only.

## Skills

| Skill | What it does |
|-------|--------------|
| [`sdd-plan`](skills/sdd-plan/SKILL.md) | Pulls a Linear issue (by ID, URL, or `next`), assigns it and moves it to *In Progress*, checks out Linear's branch name, then runs SpecKit specify → clarify → plan or OpenSpec explore → propose. Posts clarification answers back to the issue. |
| [`sdd-implement`](skills/sdd-implement/SKILL.md) | Runs SpecKit tasks → implement → converge or OpenSpec apply, or implements the plan by hand following `docs/FOUNDATIONS.md` and the project's conventions. Runs tests and linters. |
| [`sdd-commit`](skills/sdd-commit/SKILL.md) | Commits to the feature branch with the project's template, tagged with the Linear ID and linked to the issue. Amends the existing commit on later runs, retries after formatter hooks, then runs a local review. |
| [`sdd-push`](skills/sdd-push/SKILL.md) | Rebases, archives OpenSpec changes in the same PR, pushes, opens or updates the PR with `gh`, and uploads the final spec to the issue. The body includes `Fixes ENG-123`, and the issue gets the PR link and moves to *In Review*. |

Supporting skills, also callable on their own:

| Skill | What it does |
|-------|--------------|
| [`codekit`](skills/codekit/SKILL.md) | **`init`:** repo setup. Checks gh, the Linear MCP and uv; sets up SpecKit or OpenSpec; installs the commit template, pre-commit and shared codekit git config; writes the constitution or OpenSpec `config.yaml` from codekit's principles plus patterns found in your code. **`update`:** upgrades uv, specify, openspec, pre-commit and gh, refreshes the framework's project files, and re-syncs the config and constitution with the current plugin. `init` also sets up the project docs: it offers their first build, then the Action that keeps them current (with Linear) or a pre-push warning (without). |
| [`project-docs`](skills/project-docs/SKILL.md) | Keeps the app's project docs current for PMs who don't read the code: a Product Map (what the app does and what its data and interfaces support, in product language, each entry linked to code), a Decision Log (what was decided and why, from each shipped spec), and a Glossary. With Linear they're documents in the app's Linear project, updated after every merge by the `codekit-docs` Action. Without Linear they're files in `docs/project/`, updated by `sdd-push` in each PR. The first build also logs the decisions in specs already merged, so none are lost when `specs/` stops being tracked. |
| [`code-review-local`](skills/code-review-local/SKILL.md) | Reviews the branch against its spec and the project's constitution, and writes a report to the system temp folder, so nothing lands in the repo. In Claude Code it runs as a separate agent that hasn't seen your conversation, so it judges the code against the spec rather than against what was discussed. |
| [`resolve-conflict`](skills/resolve-conflict/SKILL.md) | Rebases onto the base branch and resolves conflicts with you, never silently picking a side. |
| [`linear-docs`](skills/linear-docs/SKILL.md) | Keeps the spec's decision-bearing files (spec, plan, research) on the Linear issue as documents, the spec's copy of record, through Linear's API (not the MCP), so file contents never pass through the model. Run by `sdd-push` at PR time. Can also pull a spec back down from the issue. |
| [`update-deps`](skills/update-deps/SKILL.md) | Upgrades dependencies in any ecosystem (uv, pip, poetry, npm, bun, pnpm, yarn, cargo, go). Researches each major bump, applies everything that passes your checks as one batch, and asks you only about updates that need a code change. New features worth adopting become Linear issues. Commits through `sdd-commit`. |

Run skills as commands: `/sdd-plan ENG-123`, or `/codekit:sdd-plan ENG-123` in Claude Code. In Claude Code they only run when you call them, which keeps their descriptions out of every session's context. The exception is `resolve-conflict`, which Claude can also start by itself when it hits a merge conflict. Antigravity doesn't support that setting, so there the skills can also start on their own from a request like "pick up ENG-123".

## codekit-board (for PMs)

[`codekit-board`](pm/skills/codekit-board/SKILL.md) is a second plugin in the same marketplace, for product managers who work in the Claude app and not the CLI. It answers questions about the board and the product (from the Product Map, Glossary, and Decision Log), and turns a rough request into a story-sized ticket, confirmed with a short impact, effort, and risk summary before anything is created. It's read-only except for those confirmed tickets. PMs connect their board (Linear, Jira, or GitHub) in the app themselves.

Two ways to install it:

| Way | Steps | Sharing |
|-----|-------|---------|
| From GitHub | In the Claude app, add `TheLampshady/codekit` as a plugin source and install `codekit-board`. | Each person installs it themselves. It can't be shared from the UI. |
| From a zip | Run `make pm-zip` to build `dist/codekit-board.zip`. In **Customize → Skills**, upload the zip (drag and drop works). | Share it with your team from the UI. |

To update a zip-installed skill, run `make pm-zip` again and upload the new zip over the old skill, which replaces it in place, so the sharing stays.

## Requirements

| Tool | Needed for | Setup |
|------|-----------|-------|
| Claude Code or Antigravity | Everything | — |
| Git + a GitHub remote | Everything | — |
| [GitHub CLI](https://cli.github.com/) (`gh`) | `sdd-push` | `gh auth login` |
| Linear MCP | `sdd-plan`, `sdd-push`, ticket context | Bundled. Authenticate once (see below). |
| `LINEAR_API_KEY` + Python 3.10+ | `linear-docs`, `project-docs` (with Linear) | A personal API key exported in your shell profile. Needed with SpecKit or no framework, where the Linear issue holds the spec. Optional with OpenSpec. |
| Context7 MCP | Up-to-date library docs while planning and updating dependencies | Bundled. Works without an account; add an API key for higher rate limits. |
| [uv](https://docs.astral.sh/uv/) | Installing SpecKit and pre-commit | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| SpecKit **or** OpenSpec | Optional | `/codekit init` offers to install and set one up. Without one, the skills plan and implement by hand. See [docs/extensions/](docs/extensions/). |

Full walkthrough: **[docs/SETUP.md](docs/SETUP.md)**.

## Install

No clone needed. Install straight from GitHub:

**Claude Code.** In a session:
```text
/plugin install codekit --marketplace TheLampshady/codekit
```
Or from your shell: `claude plugin install codekit --marketplace TheLampshady/codekit`. Pick **user scope** to have it in every project.

**Antigravity CLI:**
```bash
agy plugin install https://github.com/TheLampshady/codekit
```

**Antigravity IDE.** The IDE has no plugin marketplace yet; it loads plugins from a folder:
```bash
git clone https://github.com/TheLampshady/codekit.git ~/.gemini/config/plugins/codekit
```
Then restart the IDE.

Then connect Linear once:
- **Claude Code:** run `/mcp`, select `linear`, and complete the OAuth flow in the browser.
- **Antigravity:** open the MCP servers panel and sign in to `linear`.

In each project you want to use it in, run `/codekit init` once. It asks whether the repo uses Linear (optional), won't continue until `gh` and `uv` work (plus the Linear MCP if you use Linear), then offers to set up SpecKit or OpenSpec for you. Run `/codekit update` from time to time to upgrade the tools and pick up changes from newer codekit releases. In Claude Code, plugin skills are namespaced, so the full commands are `/codekit:codekit init` and `/codekit:codekit update`.

### Updating codekit

| Where | How |
|-------|-----|
| Claude Code | Turn on auto-update once: `/plugin` → **Marketplaces** → `codekit-marketplace` → **Enable auto-update** (it's off by default for marketplaces outside Anthropic's). Or update by hand: `claude plugin update codekit@codekit-marketplace` |
| Antigravity CLI | Run the `agy plugin install` command again |
| Antigravity IDE | `git -C ~/.gemini/config/plugins/codekit pull`, then restart |

After updating, run `/codekit update` in each project to pick up anything the new version changed.

## Daily flow

```text
/sdd-plan ENG-123          # or a Linear URL, or "next" to pick from your queue
  → answer clarification questions, review the plan
  → optionally publish the spec + plan to the issue (linear-docs)
/sdd-implement
  → test it yourself
/sdd-commit
  → fix any blockers from the local review, then /sdd-commit again (amends)
/sdd-push                    # add --draft for a draft PR
```

Diagrams and details: **[docs/USAGE_FLOW.md](docs/USAGE_FLOW.md)**.

## Configuration

codekit keeps its settings in git config, so they can be shared through a committed `.config/.gitconfig` (set up by `/codekit init`):

| Key | Used by | Default |
|-----|---------|---------|
| `codekit.basebranch` | all | GitHub default branch |
| `codekit.linear` | all | asked by `init`. `false` turns off every Linear step: specs stay committed in the repo, and the project docs live in `docs/project/` |
| `codekit.linear-team` | `sdd-plan next` | any team |
| `codekit.linear-project` | `sdd-plan next`, `update-deps`, `project-docs` | any project |
| `codekit.reviewers` | `sdd-push` | none (CODEOWNERS) |

Issue states aren't configured: codekit reads them from your Linear team. `/sdd-plan` moves an issue to the team's first *In Progress*-type state, and `/sdd-push` to its review state, if the team has one.

**Recommended:** install Linear's [GitHub integration](https://linear.app/docs/github). With it, Linear links branches and PRs by identifier and moves issues automatically on PR open and merge. codekit's own Linear updates are idempotent, so they're safe alongside it.
