# codekit

> Spec-driven development from Linear issue to GitHub pull request, as a plugin for **Claude Code** and **Antigravity**.

codekit gives your coding agent four skills that run the daily loop: pick up a Linear issue, plan it with SpecKit or OpenSpec, implement it, commit it, and open the PR. The Linear issue stays in sync the whole way.

```
 Linear issue ──► /sdd-plan ──► /sdd-implement ──► /sdd-commit ──► /sdd-pr ──► GitHub PR
                   │ branch        │ tasks + code     │ commit +       │ rebase, push,
                   │ In Progress   │ tests + lint     │ local review   │ PR, In Review
                   └ spec + plan                                       └ Fixes ENG-123
```

## Skills

| Skill | What it does |
|-------|--------------|
| [`sdd-plan`](skills/sdd-plan/SKILL.md) | Pulls a Linear issue (by ID, URL, or `next`), assigns it and moves it to *In Progress*, checks out Linear's branch name, then runs SpecKit specify → clarify → plan or OpenSpec explore → propose. Posts clarification answers back to the issue. |
| [`sdd-implement`](skills/sdd-implement/SKILL.md) | Runs SpecKit tasks → implement or OpenSpec apply, or implements the plan by hand following `docs/FOUNDATIONS.md` and the project's conventions. Runs tests and linters. |
| [`sdd-commit`](skills/sdd-commit/SKILL.md) | Commits to the feature branch with the project's template and the Linear ID. Amends the existing commit on later runs, retries after formatter hooks, then runs a local review. |
| [`sdd-pr`](skills/sdd-pr/SKILL.md) | Rebases, pushes, and opens or updates the PR with `gh`. The body includes `Fixes ENG-123`, and the issue gets the PR link and moves to *In Review*. |

Supporting skills, also callable on their own:

| Skill | What it does |
|-------|--------------|
| [`codekit`](skills/codekit/SKILL.md) | **`init`:** repo setup. Checks gh, the Linear MCP and uv; sets up SpecKit or OpenSpec; installs the commit template, pre-commit and shared codekit git config; writes the constitution or OpenSpec `config.yaml` from codekit's principles plus patterns found in your code. **`update`:** upgrades uv, specify, openspec, pre-commit and gh, refreshes the framework's project files, and re-syncs the config and constitution with the current plugin. |
| [`code-review-local`](skills/code-review-local/SKILL.md) | Reviews the branch against the spec and the Linear issue, and writes a report to `.codekit/reviews/`. In Claude Code it runs as a separate agent that hasn't seen your conversation, so it judges the code against the spec rather than against what was discussed. |
| [`resolve-conflict`](skills/resolve-conflict/SKILL.md) | Rebases onto the base branch and resolves conflicts with you, never silently picking a side. |
| [`linear-docs`](skills/linear-docs/SKILL.md) | Uploads the spec folder to the Linear issue as documents, one per file, through Linear's API (not the MCP), so file contents never pass through the model. Offered by `sdd-plan`, and refreshed by `sdd-pr`. |

Run skills as commands: `/sdd-plan ENG-123`, or `/codekit:sdd-plan ENG-123` in Claude Code. In Claude Code they only run when you call them, which keeps their descriptions out of every session's context. The exception is `resolve-conflict`, which Claude can also start by itself when it hits a merge conflict. Antigravity doesn't support that setting, so there the skills can also start on their own from a request like "pick up ENG-123".

## Requirements

| Tool | Needed for | Setup |
|------|-----------|-------|
| Claude Code or Antigravity | Everything | — |
| Git + a GitHub remote | Everything | — |
| [GitHub CLI](https://cli.github.com/) (`gh`) | `sdd-pr` | `gh auth login` |
| Linear MCP | `sdd-plan`, `sdd-pr`, ticket context | Bundled. Authenticate once (see below). |
| `LINEAR_API_KEY` + Python 3.10+ | `linear-docs` only | A personal API key exported in your shell profile. Optional. |
| Context7 MCP | Up-to-date library docs while planning and implementing | Bundled. Works without an account; add an API key for higher rate limits. |
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

In each project you want to use it in, run `/codekit init` once. It won't continue until `gh`, the Linear MCP and `uv` are working, then offers to set up SpecKit or OpenSpec for you. Run `/codekit update` from time to time to upgrade the tools and pick up changes from newer codekit releases. In Claude Code, plugin skills are namespaced, so the full commands are `/codekit:codekit init` and `/codekit:codekit update`.

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
/sdd-pr                    # add --draft for a draft PR
```

Diagrams and details: **[docs/USAGE_FLOW.md](docs/USAGE_FLOW.md)**.

## Configuration

codekit keeps its settings in git config, so they can be shared through a committed `.config/.gitconfig` (set up by `/codekit init`):

| Key | Used by | Default |
|-----|---------|---------|
| `codekit.basebranch` | all | GitHub default branch |
| `codekit.linear-team` | `sdd-plan next` | any team |
| `codekit.reviewers` | `sdd-pr` | none (CODEOWNERS) |

Issue states aren't configured: codekit reads them from your Linear team. `/sdd-plan` moves an issue to the team's first *In Progress*-type state, and `/sdd-pr` to its review state, if the team has one.

**Recommended:** install Linear's [GitHub integration](https://linear.app/docs/github). With it, Linear links branches and PRs by identifier and moves issues automatically on PR open and merge. codekit's own Linear updates are idempotent, so they're safe alongside it.
