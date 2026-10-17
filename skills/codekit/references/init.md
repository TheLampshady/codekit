# codekit init

First-time setup of a repo for the codekit workflow.

## 1. Prerequisites

See [SKILL.md](../SKILL.md#prerequisites-both-modes). Don't continue until every required check passes.

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
2. **Linear team key:** call `list_teams` and offer the teams. This is used by `sdd-plan next`. Optional.
3. **Default reviewers:** GitHub handles, comma-separated. Optional, and CODEOWNERS covers it if the repo has one.

## 4. Install files

Run `mkdir -p .config`. For each file, **skip it if the destination exists** and say it was skipped:

| Destination | Source |
|-------------|--------|
| `.config/.gitconfig` | [../resources/.gitconfig](../resources/.gitconfig), with the placeholders filled from Step 3. Delete any line whose value the user left blank. |
| `.config/.commit-message-template` | [../../sdd-commit/resources/.commit-message-template](../../sdd-commit/resources/.commit-message-template) |
| `.config/.pre-commit-config.yaml` | [../resources/.pre-commit-config.yaml](../resources/.pre-commit-config.yaml) |

If `.config/.gitconfig` already exists, offer to append whichever `[codekit]` keys it lacks. Append them; never rewrite the file.

**`.gitignore`:** create it if it's missing, and append each of these lines that isn't already there:
```
.codekit/
```
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

## 7. Verify and summarize

- `git config codekit.basebranch` returns the chosen branch, which proves the include works.
- `git config commit.template` returns `.config/.commit-message-template`.
- The SDD framework: already present, newly initialized (with which integrations), or none.
- The constitution or config, if written: its path, the number of project patterns, and where they came from.
- List what was installed, skipped, and still missing among the optional items (GitHub remote, Linear API key, python3).
- **Next:** commit `.config/`, `.gitignore`, and the framework files (including `.specify/memory/` or `openspec/config.yaml`), then run `/sdd-plan <ENG-123>` to start the first issue. Later, `/codekit update` keeps the tools and files current.
