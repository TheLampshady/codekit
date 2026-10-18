# codekit init

First-time setup of a repo for the codekit workflow.

## 1. Prerequisites

See [SKILL.md](../SKILL.md#prerequisites). Don't continue until every required check passes.

## 2. SDD framework

**Already set up.** If `.specify/` exists, the framework is SpecKit; if `openspec/` exists, it's OpenSpec. Check that its CLI is on `PATH` (`specify --version` or `openspec --version`). If it isn't, give the install command from the table below, without blocking, and go to Step 3.

**Not set up.** Ask:

> This repo has no spec-driven-development framework. Which one should codekit use?
> - **SpecKit:** specify → clarify → plan → tasks, checked against a constitution
> - **OpenSpec:** change proposals that update living specs under `openspec/specs/`
> - **None:** `sdd-plan` writes a plan by hand, and you can add a framework later with `/codekit init`

For SpecKit or OpenSpec:

1. **Install the CLI** if it's missing:

   | Framework | Needs | Install |
   |-----------|-------|---------|
   | SpecKit | uv | `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git` |
   | OpenSpec | node + npm (`npm --version`; if missing, ask the user to install Node.js, then stop) | `npm install -g @fission-ai/openspec@latest` |

2. **Pick the agent integration.** Use the agent running this skill: Claude Code is `claude` in both frameworks; Antigravity is `agy` in SpecKit and `antigravity` in OpenSpec. Ask whether teammates use the other agent too.
3. **Protect existing work.** If `git status --porcelain` isn't empty, ask the user to commit or stash first. SpecKit's `--force` can replace files at the paths it manages.
4. **Initialize** from the repo root, non-interactively:
   - SpecKit: `specify init --here --force --non-interactive --integration <key> --script sh` (`--script ps` on Windows). For a second agent, follow `specify integration --help`.
   - OpenSpec: `openspec init --tools <id>[,<id>]`, e.g. `--tools claude,antigravity`
5. Show `git status --short` so the user can see exactly what the framework added. Its `.gitignore` entries are handled in Step 4.

For **None**: note that Step 6 will be skipped, and move on.

## 3. Gather settings

Ask these in one message, with the detected defaults filled in:

1. **Base branch:** detect it from `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, else `origin/HEAD`, else `main`.
   The answer from the prerequisites, *"Use Linear with this repo?"*, is stored as `codekit.linear` (`true` or `false`). With **no**, skip questions 2 and 3.
2. **Linear team key:** call `list_teams` and offer the teams. This is used by `sdd-plan next`. Optional.
3. **Linear project:** the project this app's tickets and docs live in. Call `list_projects` (scoped to the team from question 2, if one was picked), offer them by name, and store the chosen project's **ID**. The user creates the project in Linear; never create one. If they don't have it yet, leave it blank: `/codekit update` asks again later. Optional.
4. **Default reviewers:** GitHub handles, comma-separated. Optional, and CODEOWNERS covers it if the repo has one.

## 4. Install files

Run `mkdir -p .config`. For each file, **skip it if the destination exists** and say it was skipped:

| Destination | Source |
|-------------|--------|
| `.config/.gitconfig` | [../resources/.gitconfig](../resources/.gitconfig), with the placeholders filled from Step 3. Delete any line whose value the user left blank. |
| `.config/.commit-message-template` | [../../sdd-commit/resources/.commit-message-template](../../sdd-commit/resources/.commit-message-template) |
| `.config/.pre-commit-config.yaml` | [../resources/.pre-commit-config.yaml](../resources/.pre-commit-config.yaml) |

If `.config/.gitconfig` already exists, offer to append whichever `[codekit]` keys it lacks. Append them; never rewrite the file.

**`.gitignore`:** only when the repo uses Linear and the framework is SpecKit or none, create it if it's missing and append each of these lines that isn't already there. Specs aren't committed: they live locally while you build, and the Linear issue holds the copy of record (`linear-docs`), so PRs show code only. **Without Linear, don't add them:** the repo is the specs' only home, so they stay committed.
```
specs/
.specify/feature.json
```
If `git ls-files specs` lists files, they're already tracked, and `.gitignore` won't untrack them. Offer `git rm -r --cached specs`, which stages their removal from the repo but leaves them on disk. Never run it without a yes. OpenSpec keeps `openspec/` committed, because its living spec is part of the repo by design.
If SpecKit or OpenSpec is present, offer the extra entries from that framework's guide in [docs/extensions/](../../../docs/extensions/).

## 5. Wire into git

1. **Include the shared config.** If `git config --local --get-all include.path` doesn't already list `../.config/.gitconfig`, run:
   ```bash
   git config --local --add include.path ../.config/.gitconfig
   ```
   The path is relative to `.git/`, so it resolves to `<repo>/.config/.gitconfig`. Committing `.config/` shares these settings with the team. Each clone runs this line once, which is what this skill and `make setup`-style targets are for.
2. **Pre-commit:** if `.git/hooks/pre-commit` doesn't exist, run `uv tool install pre-commit` (skip it if `pre-commit --version` already works), then `pre-commit install --config .config/.pre-commit-config.yaml`.
3. **Project setup scripts:** if the repo has a `Makefile` / `justfile` `setup` target or a `scripts/setup*` script, offer to add the `include.path` line and the pre-commit install to it so new clones get them automatically. Show the exact diff and wait for a yes.

## 6. SDD context: constitution / OpenSpec config

Only if SpecKit or OpenSpec is present. Follow [sdd-context.md](sdd-context.md). In short:
1. Start from codekit's constitution, [../resources/principles.md](../resources/principles.md). Ask whether the project has shipped yet.
2. Build a **Project Patterns** section only from patterns verified in the repo: `docs/FOUNDATIONS.md` first, then written docs, then the code.
3. SpecKit: run `/speckit.constitution` (or the `speckit-constitution` skill) with the filled baseline, which writes `.specify/memory/constitution.md`. OpenSpec: fill `openspec/config.yaml` from [../resources/openspec-config.yaml](../resources/openspec-config.yaml) (condensed `context`, plus `rules` per artifact).
4. Treat an unfilled framework template as missing. **Never replace** a filled-in constitution or config: offer to append only the missing principles.

## 7. Product docs Action

Only if the repo uses Linear and a project was chosen in Step 3. Ask:

> Install the `codekit-docs` GitHub Action? After every merge it updates the app's **Product Map**, **Glossary**, and **Decision Log** (reference only) in your Linear project, so PMs can read about and ask about the app without GitHub access. It runs Claude Code on GitHub, so it needs a Claude Pro or Max subscription (or an Anthropic API key) even if your team uses Antigravity, plus two repository secrets.

On a yes:

1. **Workflow:** if `.github/workflows/codekit-docs.yml` exists, skip it. Otherwise `mkdir -p .github/workflows` and write it from [../resources/codekit-docs.yml](../resources/codekit-docs.yml), with `BASE_BRANCH` replaced by the base branch from Step 3.
2. **Secrets:** run `gh secret list` (it shows names only). For each of these that's missing, give the user the command to run **in their own terminal**, not through `!`. Never ask for, read, or handle a secret's value yourself.

   | Secret | How the user sets it |
   |--------|----------------------|
   | `CLAUDE_CODE_OAUTH_TOKEN` | Run `claude setup-token`, then `gh secret set CLAUDE_CODE_OAUTH_TOKEN` and paste the token when prompted. |
   | `LINEAR_API_KEY` | `gh secret set LINEAR_API_KEY --body "$LINEAR_API_KEY"`, which reuses the key already exported in their profile. |

   A team on the Anthropic API instead of a subscription replaces the workflow's `claude_code_oauth_token` line with `anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}` and sets that secret.
3. **First run:** the Action runs once the workflow is on the base branch. With no map in Linear yet, its first run builds the whole map. To build it before then, run `/codekit docs` locally.

## 8. Verify and summarize

Check that `git config codekit.basebranch` returns the chosen branch, which proves the include works. Then report what was installed, skipped, or still missing (framework, constitution, Action and its secrets, optional checks), and what to commit: `.config/`, `.gitignore`, the framework files, and `.github/workflows/codekit-docs.yml` if installed. Next is `/sdd-plan`.
