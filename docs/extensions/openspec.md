# OpenSpec

[OpenSpec](https://github.com/Fission-AI/OpenSpec) organizes work as change proposals (`openspec/changes/<change-id>/`) that update capability specs (`openspec/specs/`). codekit detects it from `openspec/` and drives the workflow:

| codekit skill | OpenSpec step |
|---------------|---------------|
| `/sdd-plan` | `/opsx:explore` → `/opsx:propose <change-id>` |
| `/sdd-implement` | `/opsx:apply <change-id>` |
| `/sdd-pr` | `/opsx:archive <change-id>`, in the feature's PR after the rebase |

codekit names changes `<ticket-id>-<slug>` (e.g. `eng-123-add-login`), so `openspec list` maps back to Linear at a glance.

Unlike SpecKit projects, where codekit keeps specs out of the repo, OpenSpec's living spec (`openspec/specs/`) is committed by design, so OpenSpec PRs include spec text. `sdd-pr` still uploads `proposal.md` and `design.md` to the issue, so the `codekit-docs` Action can add the change's decisions to the Decision Log.

## Install

```bash
npm install -g @fission-ai/openspec@latest
openspec --version
```

## Initialize a project

`/codekit init` does this for you when you pick OpenSpec. To run it by hand:

```bash
openspec init --tools claude,antigravity   # or just one of them
```

This installs the `/opsx:*` slash commands for each tool.

## Updating

`/codekit update` upgrades the CLI (`npm install -g @fission-ai/openspec@latest`), then runs `openspec update`. That regenerates the `/opsx:*` skills and commands and leaves `openspec/config.yaml`, `openspec/specs/` and `openspec/changes/` alone. The generated command files belong to OpenSpec, so keep your own instructions in `config.yaml`, not in those files.

## Inspecting changes

```bash
openspec list                    # active changes
openspec show <change-id>        # one change in detail
openspec validate <change-id>    # structure check
openspec view                    # interactive dashboard
```

## Permissions

- **Claude Code:** in `.claude/settings.json`, add `{ "permissions": { "allow": ["Bash(openspec:*)"] } }`
- **Antigravity:** Settings → Advanced Command Access → Terminal Commands → add `openspec`

## Project context

`openspec/config.yaml` has two parts:
- `context:` is prepended to **every** artifact. OpenSpec drops it if it exceeds 50 KB.
- `rules:` holds per-artifact rules (`proposal`, `specs`, `design`, `tasks`), injected only into the matching artifact.

**`/codekit init` fills both.** `context` gets the project summary, the stack, the principles baseline condensed to one line each, and the Project Patterns (from `docs/FOUNDATIONS.md` or the code). `rules` turns the principles into artifact-level checks: new infrastructure is an open question in proposals, decision logic stays pure in designs, and tasks include their tests and name the test file they extend. The full baseline with examples stays out of `context`, because context costs tokens on every artifact. If the repo also has a SpecKit constitution or `docs/PRINCIPLES.md`, the context points to it instead.

It never replaces a config you've already filled in. It offers to append only what's missing.

## .gitignore

Commit `openspec/`: proposals and specs are meant to be reviewed with the code. Ignore only the agent command files `openspec init` generates, if you don't want them versioned.
