---
name: sdd-implement
description: 'Implement a planned feature on its branch. Detects SpecKit or OpenSpec and runs its task generation and implementation (speckit tasks/implement, OpenSpec apply), or implements the plan by hand following the project''s documented conventions. Runs the project''s tests and linters before handing back. Use when asked to: implement the feature, implement the plan, start implementation, build it, run implementation.'
user-invocable: true
disable-model-invocation: true
---

# SDD Implement

Executes the plan that `sdd-plan` produced. It stops at working, tested code on the feature branch and does not commit.

## Workflow

### 1. Verify and load context

1. Resolve `<base-branch>`: `git config codekit.basebranch`, then `origin/HEAD`, then `main`.
2. `git branch --show-current` must not be `<base-branch>`. If it is, stop and suggest `/sdd-plan`.
3. Find the ticket ID: a Linear identifier (`[A-Za-z][A-Za-z0-9]+-\d+`) in the branch name, uppercased.
4. Load the ticket from the conversation if it's there. Otherwise read the saved `ticket.md` from the plan directory. If neither exists and there's a ticket ID, call the Linear MCP `get_issue`.

### 2. Detect the framework and implement

| Framework | Detected by |
|-----------|-------------|
| SpecKit | `.specify/` directory |
| OpenSpec | `openspec/` directory |
| None | Neither |

**SpecKit**
1. Confirm `.specify/feature.json` points at this ticket's feature directory, the one holding `ticket.md`. If it points elsewhere, ask before switching it.
2. If `tasks.md` doesn't exist, run `/speckit.tasks`.
3. Run `/speckit.implement`.

If either command isn't installed, write `tasks.md` from `plan.md` yourself, then work through it task by task, checking each one off.

**OpenSpec**
1. Find the change: the `openspec/changes/<change-id>/` holding this ticket's `ticket.md`, or `openspec list` if there's only one active change. Ask if it's ambiguous.
2. Run `/opsx:apply <change-id>`.

If `/opsx:apply` isn't installed, work through `openspec/changes/<change-id>/tasks.md`, checking off each task. Leave archiving (`/opsx:archive`) for after the PR merges, and don't run it here.

**None (manual)**
1. Read `specs/<ticket>/plan.md` (written by `sdd-plan`) if present.
2. Gather conventions, in priority order:
   - `docs/FOUNDATIONS.md` and `docs/PRINCIPLES.md`, which repokit/dockit produce
   - `docs/ARCHITECTURE.md`, `CONTRIBUTING.md`, and anything under `docs/` about architecture, patterns or guidelines
   - `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, and `README.md` at the root
3. Implement the plan in small steps, matching the conventions you found and the code around each change.

**For every framework:** before writing code against a library, framework, SDK, or cloud API, look up its current usage with the Context7 MCP (`resolve-library-id`, then `query-docs`), matched to the version in the project's lockfile or manifest. This matters most for APIs that change often, and for anything the plan names but the codebase doesn't use yet. If Context7 isn't connected, fall back to the installed package's own docs or source, and say which one you used.

### 3. Validate

Detect the project's own commands from the `Makefile` / `justfile`, the `package.json` scripts, `pyproject.toml`, or the CI config in `.github/workflows/`, and run whichever exist:

- **Tests:** e.g. `make test`, `npm test`, `uv run pytest`, `go test ./...`
- **Lint / type-check:** e.g. `make lint`, `npm run lint`, `ruff check`, `tsc --noEmit`
- **Pre-commit:** `pre-commit run --files <changed files>` if a pre-commit config exists

Fix failures your change caused. If a failure existed before your change (check with `git stash` or ask the user), report it and leave it alone.

### 4. Summary

- **Framework:** SpecKit, OpenSpec, or manual, and the commands that ran.
- **Files changed:** from `git status --short`.
- **Validation:** each command and whether it passed. Paste failure output; don't paraphrase it.
- **Gaps:** any task left unchecked, and why.
- **Next:** test it yourself, then run `/sdd-commit`. If this skill was called by another workflow, return to it instead of suggesting a next step.
