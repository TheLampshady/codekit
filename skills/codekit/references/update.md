# codekit update

Brings an initialized repo up to date. It does three things: upgrades the tools the workflow runs on, refreshes the files those tools generate in the project, and re-syncs codekit's own config and constitution with the installed plugin, which may be newer than the one the repo was set up with.

If the repo was never initialized, stop and run [init.md](init.md) instead.

## 1. Prerequisites

See [SKILL.md](../SKILL.md#prerequisites). The same required checks apply.

## 2. Upgrade tools

Record each tool's version **before** anything runs (`<tool> --version`). Skip a tool that isn't installed, unless the repo uses it: SpecKit when `.specify/` exists, OpenSpec when `openspec/` exists. Show every command below as one batch, run them on a yes, then record the versions **after**.

| Tool | Upgrade | Notes |
|------|---------|-------|
| uv | `uv self update` | If uv reports it was installed by a package manager, use that instead: `brew upgrade uv`, `pipx upgrade uv`, … |
| specify | `specify self upgrade` | It upgrades only `uv tool` and `pipx` installs. For any other install it prints guidance; relay that to the user. To preview first: `specify self check`. |
| openspec | `npm install -g @fission-ai/openspec@latest` | With Homebrew: `brew upgrade openspec`. With pnpm, yarn, bun or volta, use that manager's global add. |
| pre-commit | `uv tool upgrade pre-commit` | If uv didn't install it, use whatever did (`pipx upgrade pre-commit`, `brew upgrade pre-commit`). |
| gh | `brew upgrade gh` when Homebrew owns it (`brew list gh`) | Otherwise give the command for the user's package manager (`sudo apt install --only-upgrade gh`, `winget upgrade GitHub.cli`, …) and let them run it with `! …`. Never run `sudo` yourself. |

If one upgrade fails, report the error verbatim and continue with the rest.

## 3. Refresh framework project files

Upgrading a CLI doesn't change the files it generated in the repo. Refresh those next. If the tree is dirty, ask the user to commit or stash first, so the refresh shows up as its own reviewable diff.

**SpecKit**: `specify integration upgrade` for the default integration, then `specify integration upgrade <key>` for each other installed one. It reinstalls the commands and templates and removes stale files. It **doesn't touch** `.specify/memory/constitution.md`.
- If it refuses because you've edited files it manages, list those files and ask before re-running with `--force`, because that discards the edits.
- Only when `specify integration upgrade` isn't available (an older CLI), fall back to `specify init --here --force --non-interactive --integration <key> --script sh`. This also keeps an existing constitution.

**OpenSpec**: `OPENSPEC_NO_UPDATE_CHECK=1 openspec update`. The CLI was already upgraded in Step 2, and the variable skips the interactive upgrade prompt. It regenerates the `/opsx:*` skills and commands for the configured tools and leaves `openspec/config.yaml`, `openspec/specs/` and `openspec/changes/` alone. Generated files are OpenSpec's to own, so a hand edit inside one is overwritten. Warn the user if `git diff` shows that happened.

Show `git status --short` afterwards.

## 4. Pre-commit hook versions (optional)

Offer to run `pre-commit autoupdate --config .config/.pre-commit-config.yaml`. It bumps each hook's `rev` to the latest release, which edits a committed file, so show `git diff .config/.pre-commit-config.yaml` afterwards. Then `pre-commit run --all-files --config .config/.pre-commit-config.yaml`, so new hook versions that reformat files show up now rather than at the next commit.

## 5. Re-sync codekit's own setup

Each item fills in only what's missing; it never rewrites:

1. **Git wiring:** `include.path` still lists `../.config/.gitconfig`, and `.git/hooks/pre-commit` exists. If either is missing, repeat init Step 5 (a fresh clone, or a teammate who never ran init).
2. **Config keys:** compare the `[codekit]` keys in `.config/.gitconfig` with [../resources/.gitconfig](../resources/.gitconfig). For any key the plugin knows but the file lacks, ask for its value as init Step 3 does, and append it. If `linear` is missing, ask *"Use Linear with this repo?"* first. With `linear = false`, don't ask for the Linear keys.
3. **`.gitignore`:** append any required line (init Step 4) that's missing. The `specs/` lines apply only when the repo uses Linear.
3b. **Product docs Action:** if `.github/workflows/codekit-docs.yml` exists, compare it with [../resources/codekit-docs.yml](../resources/codekit-docs.yml), filled in as init Step 7 does. If they differ, show the diff and offer to replace the file. It's codekit's template, but the team may have edited it, so never replace it without a yes. If it's missing and the repo uses Linear with `codekit.linear-project` set, offer init Step 7. Either way, re-run the `gh secret list` check from init Step 7.
4. **Constitution / OpenSpec config:** compare the project's constitution, or the `context` and `rules` in `openspec/config.yaml`, with the current [../resources/principles.md](../resources/principles.md) and [../resources/openspec-config.yaml](../resources/openspec-config.yaml), matching principles by heading or meaning. Follow the "filled in" row of [sdd-context.md §2](sdd-context.md#2-check-what-exists-never-overwrite): offer to **append** only the principles or rules the project lacks, show the exact text, and bump the constitution's MINOR version. Don't change or remove principles the project already has, even if the baseline worded them differently.
5. **Project Patterns:** check that each documented pattern still matches the code, i.e. the file paths and imports it cites still exist. Report patterns that point at code that's gone, and patterns the code now has but the doc doesn't. Offer the fixes, and never apply them silently.

## 6. Summary

```
Tool        Before    After
uv          0.x.y  →  0.x.z
specify     …      →  …
openspec    …      →  …        (or: not used)
pre-commit  …      →  …
gh          …      →  …        (or: manual: <command>)
```

Then:
- **Project files refreshed:** the framework, and the files changed (from `git status --short`).
- **Hook revs:** bumped, unchanged, or skipped.
- **Re-sync:** what was added (config keys, gitignore lines, principles, pattern fixes), or "already current".
- **Failures:** anything that didn't upgrade, with the command to run by hand.
- **Next:** review the diff and commit it, e.g. `[TASK] :: Update codekit tooling`.
