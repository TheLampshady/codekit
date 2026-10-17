# SpecKit

[SpecKit](https://github.com/github/spec-kit) (`specify`) is a spec-driven development framework: constitution → specify → clarify → plan → tasks → implement. codekit detects it from `.specify/` and runs those phases for you:

| codekit skill | SpecKit phases |
|---------------|----------------|
| `/sdd-plan` | `/speckit.specify` → `/speckit.clarify` → `/speckit.plan` |
| `/sdd-implement` | `/speckit.tasks` → `/speckit.implement` |

You don't need to run the `speckit.*` commands yourself.

## Install

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git
specify self check        # is a newer release available?
specify self upgrade
```

## Initialize a project

`/codekit init` does this for you when you pick SpecKit. To run it by hand:

```bash
specify init --here --force --non-interactive --integration claude --script sh   # Claude Code
specify init --here --force --non-interactive --integration agy --script sh      # Antigravity
```

Commit or stash your work first, because `--force` can replace files at the paths SpecKit manages.

## Updating

`/codekit update` runs `specify self upgrade`, then `specify integration upgrade` for each installed integration. That refreshes the commands and templates without touching `.specify/memory/constitution.md`. If you've edited a file SpecKit manages, the upgrade stops and codekit asks before forcing it.

## Branches

SpecKit tracks the active feature through `.specify/feature.json`, **not** the git branch. That lets codekit use Linear's branch names (`jdoe/eng-123-add-login`).

SpecKit's opt-in **`git` extension** creates numbered branches (`001-feature`) during specify. If it's enabled, `sdd-plan` switches back to the Linear branch afterwards, but leaving the extension disabled is cleaner. If you need it, set a branch template that contains the Linear identifier.

## Permissions

SpecKit runs helper scripts under `.specify/scripts/`. Allow them so you aren't prompted for each one:

- **Claude Code:** in `.claude/settings.json`, add
  ```json
  { "permissions": { "allow": ["Bash(.specify/scripts/*)", "Bash(bash .specify/scripts/*)"] } }
  ```
- **Antigravity:** Settings → Advanced Command Access → Terminal Commands → add `regex:.*\.specify/scripts/.*`

## .gitignore

```gitignore
.specify/*
!.specify/memory/
```

Keep `.specify/memory/` committed: it holds the constitution. Commit `specs/` too if you want plans reviewed alongside the code. Ignore it if plans are personal scratch.

## Constitution

The constitution (`.specify/memory/constitution.md`) holds the architecture, testing, style, and security rules that SpecKit checks every specify, plan, and implement step against.

**`/codekit init` writes it for you.** It runs `/speckit.constitution` with:
- **codekit's constitution** ([principles.md](../../skills/codekit/resources/principles.md)): modular code, consistency, testing discipline and economy, change- and copy-resilient tests, import-time safety, boundary logging, quality gates, no backwards compatibility before first release, existing conventions as the baseline, and governance.
- **Project Patterns:** the "use X, never Y" rules for this repo's shared clients, config, auth, and deployment. These come from `docs/FOUNDATIONS.md` (repokit's dockit) when present, otherwise from the code. Each pattern cites real files.

It never replaces a constitution you've already filled in. It offers to append only the missing principles. To amend later, run `/speckit.constitution` yourself or ask *"update the constitution"*.

## Extensions

```bash
specify extension add <name> --from <zip-url>
specify extension remove <name>
```

Approved catalogs go in `.specify/extension-catalogs.yml`.
